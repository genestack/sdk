# -*- coding: utf-8 -*-

#
# Copyright (c) 2015-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

from datetime import datetime
import os
from io import BytesIO
import time
from threading import Thread, Lock, Condition
import json
import re
import Connection
from genestack.utils import isatty
from genestack.Exceptions import GenestackException
from requests.exceptions import RequestException

RETRY_ATTEMPTS = 5
LAST_ATTEMPT_WAIT = 5
NUM_THREADS = 5
CHUNK_SIZE = 1024 * 1024 * 5  # 5mb


class Chunk(object):
    def __init__(self, number, start, size, chunk_size, total_size, token, filename, path, chunk_count, launch_time):
        self.data = {
            'resumableChunkSize': chunk_size,
            'resumableType': '',
            'resumableTotalSize': total_size,
            'resumableIdentifier': token,
            'resumableFilename': filename,
            'resumableRelativePath': path,
            'resumableTotalChunks': chunk_count,
            'launchTime': launch_time,
            'resumableChunkNumber': number,
            'resumableCurrentChunkSize': size
            }

        self.start = start
        self.size = size

    def __str__(self):
        return "Chunk %s %s for %s" % (self.data['resumableChunkNumber'], self.size, self.data['resumableRelativePath'])

    def get_file(self):
        container = BytesIO()
        with open(self.data['resumableRelativePath'], 'rb') as f:
            f.seek(self.start)
            container.write(f.read(self.size))
        container.seek(0)
        return container


class PermanentError(GenestackException):
    """
    Exception thrown then no need to try resume upload.
    """
    pass


def with_lock(method):
    """
    Execute method with lock. Instance should have lock object in lock attribute.
    """
    def wrapper(self, *args):
        with self.lock:
            return method(self, *args)
    return wrapper


class ChunkedUpload(object):
    def __init__(self, application, path, chunk_size=None):
        if chunk_size is None:
            chunk_size = CHUNK_SIZE
        if chunk_size <= 0:
            raise GenestackException("Chunk size should be positive.")

        self.chunk_upload_url = '/application/uploadChunked/%s/%s/unusedToken' % (application.vendor, application.application)
        self.connection = application.connection

        self.lock = Lock()
        self.__iterator_lock = Lock()
        self.__output_lock = Lock()

        self.__application_result = None
        self.__has_application_result = False
        self.__end_task_flag = False
        self.__thread_counter = 0
        self.__error = None

        self.condition = Condition()

        modified = datetime.fromtimestamp(os.path.getmtime(path))
        total_size = os.path.getsize(path)

        token = '{total_size}-{name}-{date}'.format(total_size=total_size,
                                                    name=re.sub('[^A-z0-9_-]', '_', os.path.basename(path)),
                                                    date=modified.strftime('%a_%b_%d_%Y_%H_%M_%S'))

        # Last chunk can be larger than CHUNK_SIZE but less then two chunks.
        # Example: CHUNK_SIZE = 2
        # file size 2 > 1 chunk
        # file size 3 > 1 chunk
        # file size 4 > 2 chunk
        # file size 5 > 2 chunk

        if total_size < chunk_size * 2:
            chunk_count = 1
        else:
            chunk_count = total_size / chunk_size

        self.total_size = total_size
        self.filename = os.path.basename(path)
        self.path = path
        self.chunk_count = chunk_count
        launch_time = int(time.time() * 1000)

        if isatty():
            self.progress = Connection.TTYProgress()
        else:
            self.progress = Connection.DottedProgress(40)

        def _iterator():
            start = 0
            info = [chunk_size, total_size, token, self.filename, path, chunk_count, launch_time]
            for x in xrange(1, chunk_count + 1):
                if x == chunk_count:
                    curren_chunk_size = self.total_size - start
                else:
                    curren_chunk_size = chunk_size
                yield Chunk(x, start, curren_chunk_size, *info)
                start += curren_chunk_size

        self.iterator = _iterator()

    @property
    @with_lock
    def application_result(self):
        return self.__application_result

    @application_result.setter
    @with_lock
    def application_result(self, value):
        self.__application_result = value

    @property
    @with_lock
    def has_application_result(self):
        return self.__has_application_result

    @has_application_result.setter
    @with_lock
    def has_application_result(self, value):
        self.__has_application_result = value

    @property
    @with_lock
    def end_task_flag(self):
        return self.__end_task_flag

    @end_task_flag.setter
    @with_lock
    def end_task_flag(self, value):
        self.__end_task_flag = value

    @property
    @with_lock
    def error(self):
        return self.__error

    @error.setter
    def error(self, value):
        self.__error = value

    @property
    @with_lock
    def thread_counter(self):
        return self.__thread_counter

    @thread_counter.setter
    @with_lock
    def thread_counter(self, value):
        self.__thread_counter = value

    def __update_progress(self, update_size):
        with self.__output_lock:
            self.progress(self.filename, update_size, self.total_size)

    def __check_chunk(self, chunk):
        """
        Check if chunk is already uploaded,
            - return True if file uploaded
            - return False is file is not uploaded
            - return string in case of connection error.
        """
        try:
            r = self.connection.get_request(self.chunk_upload_url, params=chunk.data, follow=False)
            return r.status_code == 200
        except RequestException as e:
            # check that any type of connection error occurred and retry.
            return str(e)

    def __upload_chunk(self, chunk, chunk_file):
        """
        Upload data to server. Return response or string if got connection troubles.
        """
        chunk_file.seek(0)
        files = {'file': chunk_file}
        try:
            r = self.connection.post_multipart(self.chunk_upload_url, data=chunk.data, files=files, follow=False)
            return r
        except RequestException as e:
            # check that any type of connection error occurred and retry.
            return str(e)

    def __process_chunk(self, chunk):
        """
        Try to upload chunk in several attempts.
        :param chunk:
        :return:
        """
        file_cache = None
        upload_checked = False
        error = None

        for attempt in xrange(RETRY_ATTEMPTS):
            # check if we still try to upload.
            if self.end_task_flag:
                return

            sleep_time = 1

            # Check if chunk is already uploaded
            if not upload_checked:
                res = self.__check_chunk(chunk)
                if res is True:
                    self.__update_progress(chunk.size)
                    return
                elif res is False:
                    upload_checked = True
                else:
                    self.error = res
                    time.sleep(sleep_time)
                    sleep_time *= 2
                    continue

            # try to upload chunk
            if file_cache is None:
                file_cache = chunk.get_file()

            r = self.__upload_chunk(chunk, file_cache)
            if isinstance(r, str):
                # check that any type of connection error occurred and retry.
                time.sleep(sleep_time)
                sleep_time *= 2
                error = r
                continue

            # done without errors
            if r.status_code == 200:
                self.__update_progress(chunk.size)
                response = json.loads(r.text)
                if 'applicationResult' in response:
                    self.application_result = response['applicationResult']
                    self.has_application_result = True
                    self.end_task_flag = True
                return

            error = "Got response with status code: %s" % r.status_code
            # permanent errors
            if 400 <= r.status_code < 600:
                self.end_task_flag = True
                try:
                    response = json.loads(r.text)
                    if isinstance(response, dict) and 'error' in response:
                        error = response['error']
                except ValueError:
                    pass
                self.error = error
                return

            # other network errors, try again
            time.sleep(sleep_time)
            sleep_time *= 2
            continue

        self.error = error

    def upload(self):
        def do_stuff():
            """
            Daemon look for uploading.
            Daemon quits on next conditions:
                - all chunk are processed
                - someone set self.end_task_flag to True
                - got response form server that file is fully uploaded
                - got permanent error (4xx, 5xx)
                - got not 200 http response RETRY_ATTEMPTS times in a row
            """
            self.thread_counter += 1

            try:
                while True:  # daemon working cycle
                    if self.end_task_flag:
                        return
                    try:
                        with self.__iterator_lock:
                            chunk = next(self.iterator)
                    except StopIteration:
                        return
                    self.__process_chunk(chunk)
            except Exception as e:
                self.error = str(e)
            finally:
                self.end_task_flag = True
                self.thread_counter -= 1
                with self.condition:
                    self.condition.notify()

        threads = [Thread(target=do_stuff) for _ in range(NUM_THREADS)]
        [thread.setDaemon(True) for thread in threads]
        [thread.start() for thread in threads]

        with self.condition:
            while True:
                try:
                    self.condition.wait()
                except (KeyboardInterrupt, SystemExit):
                    self.end_task_flag = True
                    self.error = 'Interrupted by user.'
                if not self.thread_counter:
                    break

        if self.has_application_result:
            return self.application_result
        else:
            raise GenestackException('Fail to upload %s. %s' % (self.path, self.error or ''))


def upload_by_chunks(application, path, chunk_size=None):
    return ChunkedUpload(application, path, chunk_size=chunk_size).upload()