import json
import os
import re
import sys
import time
from datetime import datetime
from io import BytesIO
from threading import Condition, Lock, Thread

from OpenSSL.SSL import SysCallError
from requests.exceptions import RequestException

from odm_sdk import GenestackException
from odm_sdk.utils import isatty

RETRY_ATTEMPTS = 5
RETRY_INTERVAL = 2  # seconds
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
        return "Chunk %s %s bytes for %s" % (self.data['resumableChunkNumber'], self.size,
                                             self.data['resumableRelativePath'])

    def get_file(self):
        container = BytesIO()
        with open(self.data['resumableRelativePath'], 'rb') as f:
            f.seek(self.start)
            container.write(f.read(self.size))
        container.seek(0)
        return container


class PermanentError(GenestackException):
    """
    If this exception is thrown, the upload will not be able to be resumed.
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
            raise GenestackException("Chunk size should be positive")

        self.chunk_upload_url = '/application/uploadChunked/%s/unusedToken' % application.application_id
        self.connection = application.connection

        self.lock = Lock()
        self.__iterator_lock = Lock()
        self.__output_lock = Lock()

        self.__application_result = None
        self.__has_application_result = False
        self.__finished = False
        self.__error = None
        self.thread_counter = 0

        self.condition = Condition()

        modified = datetime.fromtimestamp(os.path.getmtime(path))
        total_size = os.path.getsize(path)

        # TODO change according to javascript token
        token = '{total_size}-{name}-{date}'.format(total_size=total_size,
                                                    name=re.sub('[^A-z0-9_-]', '_', os.path.basename(path)),
                                                    date=modified.strftime('%a_%b_%d_%Y_%H_%M_%S'))
        self.token = token
        self.path = path
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

        # import from here to avoid circular imports
        # TODO move progress functions to other module.
        if isatty():
            from .connection import TTYProgress
            self.progress = TTYProgress()
        else:
            from .connection import DottedProgress
            self.progress = DottedProgress(40)

        def _iterator():
            start = 0
            info = [chunk_size, total_size, token, self.filename, path, chunk_count, launch_time]
            for x in range(1, chunk_count + 1):
                if x == chunk_count:
                    current_chunk_size = self.total_size - start
                else:
                    current_chunk_size = chunk_size
                yield Chunk(x, start, current_chunk_size, *info)
                start += current_chunk_size

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
    def finished(self):
        return self.__finished

    @finished.setter
    @with_lock
    def finished(self, value):
        self.__finished = value

    @property
    @with_lock
    def error(self):
        return self.__error

    @error.setter
    def error(self, value):
        self.__error = value

    def __update_progress(self, update_size):
        with self.__output_lock:
            self.progress(self.filename, update_size, self.total_size)

    def __process_chunk(self, chunk):
        """
        Try to upload a chunk of data in several attempts.
        :param chunk:
        :return:
        """
        file_cache = None
        upload_checked = False
        error = None

        for attempt in range(RETRY_ATTEMPTS):
            # Check if chunk is already uploaded
            if not upload_checked:
                try:
                    response = self.connection.get_request(self.chunk_upload_url, params=chunk.data, follow=False)
                except RequestException as e:
                    error = str(e)
                    time.sleep(RETRY_INTERVAL)
                    continue

                if response.status_code == 200:
                    self.__update_progress(chunk.size)
                    return
                else:
                    upload_checked = True

            # try to upload chunk
            if file_cache is None:
                file_cache = chunk.get_file()

            file_cache.seek(0)
            try:
                response = self.connection.post_multipart(self.chunk_upload_url,
                                                          data=chunk.data,
                                                          files={'file': file_cache},
                                                          follow=False)
            except (RequestException, SysCallError) as e:
                # check that any type of connection error occurred and retry.
                time.sleep(RETRY_INTERVAL)
                error = str(e)
                if self.connection.debug:
                    sys.stderr.write('%s/%s attempt to upload %s failed. Connection error: %s\n' %
                                     (attempt + 1, RETRY_ATTEMPTS, chunk, error))
                continue
            # done without errors
            if response.status_code == 200:
                self.__update_progress(chunk.size)
                data = json.loads(response.text)

                if data.get('lastChunkUploaded', False):
                    self.application_result = data['result']
                    self.has_application_result = True
                    self.finished = True
                return

            error = "Got response with status code: %s" % response.status_code
            # permanent errors
            if 400 <= response.status_code < 600:
                self.finished = True
                try:
                    data = json.loads(response.text)
                    if isinstance(data, dict) and 'error' in data:
                        error = data['error']
                except ValueError:
                    pass
                self.error = error
                return
            # other network errors, try again
            time.sleep(RETRY_INTERVAL)
            continue

        self.error = error
        self.finished = True

    def upload(self):
        def do_stuff():
            """
            The daemon will look for uploads.
            The daemon will quit if one of the following conditions is met:
                - all chunks have been processed
                - someone set self.finished to True
                - the server said that the file upload was complete
                - a permanent error was raised (4xx, 5xx)
                - the number of RETRY_ATTEMPTS was exceeded for a single chunk
            """
            with self.condition:
                self.thread_counter += 1
            try:
                while not self.finished:  # daemon working cycle
                    try:
                        with self.__iterator_lock:
                            chunk = next(self.iterator)
                    except StopIteration:
                        return
                    self.__process_chunk(chunk)
            except Exception as e:
                self.error = str(e)
            finally:
                with self.condition:
                    self.thread_counter -= 1
                    self.condition.notify()

        threads = [Thread(target=do_stuff) for _ in range(min(NUM_THREADS, self.chunk_count))]
        [thread.setDaemon(True) for thread in threads]
        [thread.start() for thread in threads]

        with self.condition:
            while True:
                try:
                    self.condition.wait()
                except (KeyboardInterrupt, SystemExit):
                    self.error = 'Interrupted by user'
                    self.finished = True
                    break
                if not self.thread_counter:
                    break
        if self.has_application_result:
            return self.application_result
        else:
            error_message = self.error or 'file has been uploaded from another session'
            raise GenestackException('Fail to upload %s: %s' % (self.path, error_message))


def upload_by_chunks(application, path, chunk_size=None):
    return ChunkedUpload(application, path, chunk_size=chunk_size).upload()
