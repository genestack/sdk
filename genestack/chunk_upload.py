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
        self.attempts = 0

        self.__file = None

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


class ChunkedUpload:
    def __init__(self, application, path, chunk_size=None):
        if chunk_size is None:
            chunk_size = CHUNK_SIZE
        if chunk_size <= 0:
            raise GenestackException("Chunk size should be positive.")

        self.chunk_upload_url = '/application/uploadChunked/%s/%s/unusedToken' % (application.vendor, application.application)
        self.connection = application.connection

        self.queue_lock = Lock()
        self.lock = Lock()
        self.output_lock = Lock()

        self.accession = None
        self.error = None

        modified = datetime.fromtimestamp(os.path.getmtime(path))
        total_size = os.path.getsize(path)

        token = '{total_size}-{name}-{date}'.format(total_size=total_size,
                                                    name=re.sub('[^A-z0-9_-]', '_', os.path.basename(path)),
                                                    date=modified.strftime('%a_%b_%d_%Y_%H_%M_%S'))

        # Last chunk can be large than CHUNK_SIZE but less then two chunks.
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
            for x in xrange(1, chunk_count):
                end = start + chunk_size
                yield Chunk(x, start, end - start, *info)
                start = end
            yield Chunk(self.chunk_count, start, self.total_size - start, *info)

        self.iterator = _iterator()

    def get_next_chunk(self):
        with self.queue_lock:
            return next(self.iterator)

    def update_progress(self, update_size):
        with self.output_lock:
            self.progress(self.filename, update_size, self.total_size)

    def upload(self):
        condition = Condition()
        self.end_task_flag = False

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
            def notify():
                self.end_task_flag = True
                with condition:
                    condition.notify()

            while True:  # daemon working cycle
                try:
                    chunk = self.get_next_chunk()
                except StopIteration:
                    self.end_task_flag = True

                if self.end_task_flag:
                    notify()
                    return

                file_cache = None
                upload_checked = False

                for attempt in reversed(xrange(1, RETRY_ATTEMPTS + 1)):
                    # Check if chunk is already uploaded
                    if not upload_checked:
                        try:
                            r = self.connection.get_request(self.chunk_upload_url, params=chunk.data, follow=False)
                            if r.status_code == 200:
                                self.update_progress(chunk.size)
                                break
                            else:
                                upload_checked = True
                        except RequestException:
                            # check that any type of connection error occurred and retry.
                            time.sleep(LAST_ATTEMPT_WAIT / 2 ** attempt)
                            self.error = str(e)
                            continue

                    # try to upload chunk
                    if file_cache is None:
                        file_cache = chunk.get_file()
                    file_cache.seek(0)
                    files = {'file': file_cache}
                    try:
                        r = self.connection.post_multipart(self.chunk_upload_url, data=chunk.data, files=files, follow=False)
                    except RequestException as e:
                        # check that any type of connection error occurred and retry.
                        time.sleep(LAST_ATTEMPT_WAIT / 2 ** attempt)
                        self.error = str(e)
                        continue

                    if 400 <= r.status_code < 600:
                        try:
                            response = json.loads(r.text)
                            if isinstance(response, dict) and 'error' in response:
                                self.error = response['error']
                        except ValueError:
                            self.error = "Got response with status code: %s" % r.status_code
                        notify()
                        return
                    elif r.status_code == 200:
                        self.update_progress(chunk.size)
                        application_response = json.loads(r.text)
                        # FIXME after #4125
                        if application_response not in ('Chunk uploaded', 'Chunk skipped'):
                            with self.lock:
                                self.accession = application_response
                            notify()
                            return
                        else:
                            break
                    else:
                        # Not sure if sure if we should have different approach for non 200 statuses.
                        time.sleep(LAST_ATTEMPT_WAIT / 2 ** attempt)
                        self.error = 'Http error: %s' % r.status_code
                        continue
                else:
                    notify()
                    return

        threads = [Thread(target=do_stuff) for _ in range(NUM_THREADS)]
        [thread.setDaemon(True) for thread in threads]
        [thread.start() for thread in threads]

        with condition:
            while True:
                try:
                    condition.wait(5)
                except (KeyboardInterrupt, SystemExit):
                    self.end_task_flag = True
                    with self.lock:
                        self.error = 'Interrupted by user.'
                if not any(x.isAlive() for x in threads):
                    break

        if self.accession:
            return self.accession
        else:
            raise GenestackException('Fail to upload %s. %s' % (self.path, self.error or ''))


def chunk_upload(application, path, chunk_size=None):
    return ChunkedUpload(application, path, chunk_size=None).upload()