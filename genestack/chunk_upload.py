from datetime import datetime
import os
from io import BytesIO
import time
from Queue import Queue
from time import sleep
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
CHUNK_SIZE = 1024 * 1024 * 5  # 5mb


class Chunk(object):
    def __init__(self, number, start, chunk_size, uploader):
        self.data = {
            'resumableChunkSize': uploader.chunk_size,
            'resumableType': '',
            'resumableTotalSize': uploader.total_size,
            'resumableIdentifier': uploader.token,
            'resumableFilename': uploader.filename,
            'resumableRelativePath': uploader.path,
            'resumableTotalChunks': uploader.chunk_count,
            'launchTime': uploader.lunch_time,
            }

        self.start = start
        self.size = chunk_size
        self.attempts = 0

        self.data['resumableChunkNumber'] = number
        # self.data['resumableCurrentChunkSize'] = chunk_size currently unused by server
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


class UploadParamsException(GenestackException):
    pass


class ChunkUpload:
    def __init__(self, connection, path):
        self.connection = connection

        self.lock = Lock()
        self.output_lock = Lock()

        self.accession = None
        self.error = None

        chunk_size = CHUNK_SIZE
        modified = datetime.fromtimestamp(os.path.getmtime(path))
        total_size = os.path.getsize(path)
        self.token = '{total_size}-{name}-{date}'.format(total_size=total_size,
                                                    name=os.path.basename(path),
                                                    date=modified.strftime('%a_%b_%d_%Y_%H_%M_%S'))

        if total_size < chunk_size * 2:
            chunk_count = 1
        else:
            chunk_count = total_size / chunk_size


        self.total_size = total_size
        self.filename = os.path.basename(path)
        self.path = path
        self.chunk_count = chunk_count
        self.lunch_time = int(time.time() * 1000)
        self.chunk_size = chunk_size
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
        r = self.connection.get_request(CHUNK_UPLOAD_URL, chunk.data)
        return r.text == '{"message":"Uploaded"}'

    def upload_chunk(self, chunk):
        files = {'file': chunk.get_file()}
        r = self.connection.post_multipart(CHUNK_UPLOAD_URL, chunk.data, files=files)
        response = json.loads(r.text)
        if r.status_code == 400:
            raise UploadParamsException('Error: %s' % response['error'])
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
                chunk, connection = q.get()
                attempts = RETRY_ATTEMPTS
                while attempts:
                    try:
                        if not self.is_uploaded(chunk):
                            result = self.upload_chunk(chunk)
                            if result == 'Chunk uploaded':
                                self.update_progress(chunk.size)
                            elif result != 'Chunk skipped':
                                with self.lock:
                                    self.update_progress(chunk.size)
                                stop()
                                with self.lock:
                                    self.accession = result
                                return
                    except UploadParamsException as e:
                        with self.lock:
                            self.error = str(e)
                        stop()
                        return
                    except Exception as e:
                        self.update_progress(0, msg="%s. Chunk %s attempts left: %s" % (e, chunk.data['resumableChunkNumber'], attempts - 1))
                        sleep(LAST_ATTEMPT_WAIT / 2 ** attempts)
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
            q.put((chunk, self.connection))

        q.join()

        if self.accession:
            return self.accession
        else:
            raise GenestackException('Fail to upload %s. %s' % (self.path, self.error or ''))


def chunk_upload(path, connection):
    return ChunkUpload(connection, path).upload()