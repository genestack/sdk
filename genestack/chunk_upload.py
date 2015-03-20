from collections import deque
from datetime import datetime
import os
from io import BytesIO
import time
from Queue import Queue
from time import sleep
import json
from genestack import GenestackServerException, Application, GenestackException
import requests
from threading import Thread


CHUNK_UPLOAD_URL = 'application/uploadChunked/genestack/rawloader/unusedToken'
RETRY_ATTEMPTS = 5
LAST_ATTEMPT_WAIT = 5
NUM_THREADS = 5
CHUNK_SIZE = 1024 * 1024 * 5  # 5mb


class NewConnection:
    """
    Connection to specified url. Server url is not same as host. If include protocol host and path: ``https://platform.genestack.org/endpoint``

    Connection is not logged by default. To access applications methods you need to :attr:`login`.
    """
    DEFAULT_VENDOR = 'genestack'

    def __init__(self, server_url):
        self.server_url = server_url
        self.cookies = None

    def whoami(self):
        """
        Return user email.

        :return: email
        :rtype: str
        """
        return self.application('genestack/signin').invoke('whoami')

    def login(self, email, password):
        """
        Login connection with given credentials. Raises exception if login failed.

        :param email: login at server
        :type email: str
        :param password: password
        :type password: str
        :rtype: None
        :raises: GenestackServerException: if login failed
        """
        self.session = requests.Session()

        r = self.session.post(self.server_url + '/application/invoke/genestack/signin', {'method': 'authenticate',
                                                                                         'parameters': json.dumps(
                                                                                             ['tester@genestack.com',
                                                                                              'pwdTester123'])})

        logged = json.loads(r.text)
        if not logged:
            raise GenestackException("Fail to login %s" % email)


    def logout(self):
        """
        Logout from server.

        :rtype: None
        """
        self.open('/signOut', follow=False)

    def get(self, path, data=None, follow=True):
        r = self.session.get(self.server_url + path, params=data, allow_redirects=follow)
        return r.text

    def open(self, path, data=None, files=None, follow=True):
        """
        Sends data to url. Url is concatenated server url and path.

        :param path: part of url that added to self.server_url
        :param data: dict of parameters or file-like object or string
        :param follow: flag to follow redirect
        :return: response
        :rtype: request
        """

        r = self.session.post(self.server_url + path, data=data, files=files, allow_redirects=follow)
        return r.text
        # except requests.exceptions.RequestException, e:
        # raise urllib2.URLError('Fail to connect %s%s %s' % (self.server_url,
        #                                                         path,
        #                                                         str(e).replace('urlopen error', '').strip('<\ >')))

    def application(self, application_id):
        """
        Return documentation with specified id.

        :param application_id: application_id.
        :type application_id: str
        :return: application class
        :rtype: Application
        """
        return Application(self, application_id)

    def __repr__(self):
        return 'Connection("%s")' % self.server_url


def get_new_connection():
    from utils import get_user
    user = get_user()
    connection = NewConnection('http://localhost:8080/frontend/endpoint/')
    connection.login(user.email, user.password)
    return connection


class Chunk(object):
    def __init__(self, number, start, end, path):
        self.number = number
        self.start = start
        self.end = end
        self.path = path
        self.file = None
        self.attempts = 0


    def size(self):
        return self.end - self.start

    def __str__(self):
        return "Chunk %s %s [%s, %s) for %s" % (self.number, self.size(), self.start, self.end, self.path)

    def get_data(self):
        if self.file is None:
            container = BytesIO()
            with open(self.path, 'rb') as f:
                f.seek(self.start)
                container.write(f.read(self.size()))
            self.file = container
        self.file.seek(0)
        return self.file


class ChunkQueue(deque):
    def __init__(self, path, chunk_size=6000):
        modified = datetime.fromtimestamp(os.path.getmtime(path))
        self.path = path
        self.size = os.path.getsize(path)
        self.token = '{size}-{name}-{date}'.format(size=self.size,
                                                   name=os.path.basename(path),
                                                   date=modified.strftime('%a_%b_%d_%Y_%H_%M_%S'))
        self.CHUNK_SIZE = chunk_size
        self.chunk_count = max((self.size / chunk_size) - 1, 1)
        self.lunch_time = int(time.time() * 1000)

        start = 0
        x = 0
        for x in xrange(1, self.chunk_count):
            end = start + chunk_size
            self.append(Chunk(x, start, end, path))
            start = end
        self.append(Chunk(x + 1, start, self.size, path))


def get_data(chunk, queue):
    return {'resumableChunkNumber': chunk.number,
            'resumableChunkSize': queue.CHUNK_SIZE,
            'resumableCurrentChunkSize': chunk.size(),
            'resumableType': '',
            'resumableTotalSize': queue.size,
            'resumableIdentifier': queue.token,
            'resumableFilename': os.path.basename(queue.path),
            'resumableRelativePath': queue.path,
            'resumableTotalChunks': queue.chunk_count,
            'launchTime': queue.lunch_time,
            }


def upload_chunk(chunk, queue, connection):

    data = get_data(chunk, queue)

    files = {'file': chunk.get_data()}

    r = connection.open(CHUNK_UPLOAD_URL, data, files=files)
    response = json.loads(r)
    if isinstance(response, dict) and 'error' in response:
        raise GenestackServerException(
            response['error'], '???', {},
            stack_trace=response.get('errorStackTrace')
        )
    return response


def is_uploaded(chunk, queue, connection):
    data = get_data(chunk, queue)
    r = connection.get(CHUNK_UPLOAD_URL, data)
    return r == 'Upload'


def chunk_upload(path):
    connection = get_new_connection()
    result_container = []
    q = Queue()

    def do_stuff(q):
        while True:
            chunk, queue, connection = q.get()
            attempts = RETRY_ATTEMPTS
            while attempts:
                try:
                    if not is_uploaded(chunk, queue, connection):
                        result = upload_chunk(chunk, queue, connection)
                        if result not in ('Chunk uploaded', 'Chunk skipped'):
                            # assert isinstance(q, PriorityQueue)
                            with q.mutex:
                                q.queue.clear()
                                q.all_tasks_done.notify_all()
                                q.unfinished_tasks = 0
                            result_container.append(result)
                            return

                except Exception as e:
                    print "Fail to upload chunk %s, attempts left: %s. Error %s\n" % (chunk.number, attempts - 1, e)
                    sleep(LAST_ATTEMPT_WAIT / 2 ** attempts)
                    attempts -= 1
                    continue
                q.task_done()
                break

            else:
                result_container.append(None)
                with q.mutex:
                    q.queue.clear()
                    q.all_tasks_done.notify_all()
                    q.unfinished_tasks = 0
                return

    for _ in range(NUM_THREADS):
        worker = Thread(target=do_stuff, args=(q,))
        worker.setDaemon(True)
        worker.start()

    queue = ChunkQueue(path, CHUNK_SIZE)

    for x in queue:
        q.put((x, queue, connection))

    q.join()
    if result_container[0]:
        return result_container[0]
    else:
        raise GenestackServerException('Fail to upload %s.' % path)