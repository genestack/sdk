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
from Queue import Queue
import json
import sys
from genestack.Connection import TTYProgress, DottedProgress
from genestack.utils import isatty
from genestack import GenestackException
from threading import Thread, Lock


CHUNK_UPLOAD_URL = '/application/uploadChunked/genestack/rawloader/unusedToken'
RETRY_ATTEMPTS = 5
LAST_ATTEMPT_WAIT = 5
NUM_THREADS = 5


class Chunk(object):
    def __init__(self, number, start, current_chunk_size, uploader):
        self.data = {
            'resumableChunkSize': uploader.CHUNK_SIZE,
            'resumableType': '',
            'resumableTotalSize': uploader.total_size,
            'resumableIdentifier': uploader.token,
            'resumableFilename': uploader.filename,
            'resumableRelativePath': uploader.path,
            'resumableTotalChunks': uploader.chunk_count,
            'launchTime': uploader.launch_time,
            'resumableChunkNumber': number,
            'resumableCurrentChunkSize': current_chunk_size
            }

        self.start = start
        self.size = current_chunk_size
        self.attempts = 0

        self.__file = None
        self.uploader = uploader

    def __str__(self):
        return "Chunk %s %s for %s" % (self.data['resumableChunkNumber'], self.size, self.uploader.path)

    def get_file(self):
        if self.__file is None:
            container = BytesIO()
            with open(self.uploader.path, 'rb') as f:
                f.seek(self.start)
                container.write(f.read(self.size))
            self.__file = container
        self.__file.seek(0)
        return self.__file


class WrongUploadDataException(GenestackException):
    pass


class ChunkedUpload:
    CHUNK_SIZE = 1024 * 1024 * 5  # 5mb

    def __init__(self, connection, path):
        self.connection = connection

        self.lock = Lock()
        self.output_lock = Lock()

        self.accession = None
        self.error = None

        modified = datetime.fromtimestamp(os.path.getmtime(path))
        total_size = os.path.getsize(path)
        self.token = '{total_size}-{name}-{date}'.format(total_size=total_size,
                                                    name=os.path.basename(path),
                                                    date=modified.strftime('%a_%b_%d_%Y_%H_%M_%S'))

        if total_size < self.CHUNK_SIZE * 2:
            chunk_count = 1
        else:
            chunk_count = total_size / self.CHUNK_SIZE


        self.total_size = total_size
        self.filename = os.path.basename(path)
        self.path = path
        self.chunk_count = chunk_count
        self.launch_time = int(time.time() * 1000)
        self.chunk_size = self.CHUNK_SIZE
        self.chunks = []

        start = 0
        x = 0
        for x in xrange(1, self.chunk_count):
            end = start + self.chunk_size
            self.chunks.append(Chunk(x, start, end - start, self))
            start = end
        self.chunks.append(Chunk(x + 1, start, self.total_size - start, self))

        if isatty():
            self.progress = TTYProgress()
        else:
            self.progress = DottedProgress(40)

    def is_uploaded(self, chunk):
        r = self.connection.get_request(CHUNK_UPLOAD_URL, params=chunk.data, follow=False)
        if r.status_code == 200:
            return True
        elif r.status_code == 204:
            return False
        else:
            raise GenestackException("Unexpected response with status %s: %s" % (r.status_code, r.text))

    def upload_chunk(self, chunk):
        files = {'file': chunk.get_file()}
        r = self.connection.post_multipart(CHUNK_UPLOAD_URL, data=chunk.data, files=files, follow=False)
        response = json.loads(r.text)
        if r.status_code == 400:
            raise WrongUploadDataException('Error: %s' % response['error'])
        if isinstance(response, dict) and 'error' in response:
            raise Exception('Error at chunk upload: %s' % response['error'])
        return response

    def update_progress(self, update_size, msg=None):
        with self.output_lock:
            if msg and isatty():
                sys.stderr.write('\r%s: %s\n' % (self.filename, msg))
            self.progress(self.filename, update_size, self.total_size)

    def upload(self):
        q = Queue()

        def do_stuff(q):
            def stop():
                with q.mutex:
                    q.queue.clear()
                    q.all_tasks_done.notify_all()
                    q.unfinished_tasks = 0
            while True:
                chunk = q.get()
                attempts = RETRY_ATTEMPTS
                while attempts:
                    try:
                        with self.lock:
                            self.update_progress(chunk.size)

                        if not self.is_uploaded(chunk):
                            result = self.upload_chunk(chunk)
                            if result == 'Chunk uploaded':
                                pass
                            elif result != 'Chunk skipped':
                                stop()
                                with self.lock:
                                    self.accession = result
                                return
                    except WrongUploadDataException as e:
                        with self.lock:
                            self.error = str(e)
                        stop()
                        return
                    except Exception as e:
                        self.update_progress(0, msg="%s. Chunk %s attempts left: %s" % (e, chunk.data['resumableChunkNumber'], attempts - 1))
                        time.sleep(LAST_ATTEMPT_WAIT / 2 ** attempts)
                        attempts -= 1
                        self.error = str(e)
                        continue
                    q.task_done()
                    break
                else:
                    stop()
                    return

        for _ in range(NUM_THREADS):
            worker = Thread(target=do_stuff, args=(q,))
            worker.setDaemon(True)
            worker.start()

        for chunk in self.chunks:
            q.put(chunk)

        q.join()

        if self.accession:
            return self.accession
        else:
            raise GenestackException('Fail to upload %s. %s' % (self.path, self.error or ''))


def chunk_upload(path, connection):
    return ChunkedUpload(connection, path).upload()