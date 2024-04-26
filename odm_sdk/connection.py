import json
import os
import sys
import urllib
from io import FileIO
from urllib.parse import urlsplit
import requests
from requests import HTTPError, RequestException

from odm_sdk import (GenestackAuthenticationException, GenestackConnectionFailure,
                              GenestackException, GenestackResponseError, GenestackServerException,
                              GenestackVersionException, __version__)
from odm_sdk.chunked_upload import upload_by_chunks
from odm_sdk.utils import isatty


class Response(object):
    """Represents response from Genestack server."""

    def __init__(self, data):
        self._data = data

    @property
    def error(self):
        return self._data.get('error')

    @property
    def error_stack_trace(self):
        return self._data.get('errorStackTrace')

    @property
    def log(self):
        return self._data['log']

    @property
    def result(self):
        return self._data['result']

    @property
    def trace(self):
        return self._data.get('trace')

    @property
    def elapsed_microseconds(self):
        return self._data.get('elapsedMicroseconds')


class Connection(object):
    """
    A class to handle a connection to a specified Genestack server.
    Instantiating the class does mean you are logged in to the server.
    To do so, you need to call the :py:meth:`~odm_sdk.Connection.login` method.
    """

    def __init__(self, server_url, debug=False, show_logs=False):
        """
        :param server_url: server url
        :type server_url: str
        :param debug:  will print additional traceback from application
        :type debug: bool
        :param show_logs: will print application logs (received from server)
        :type show_logs: bool
        """
        self.server_url = server_url
        self.session = requests.session()
        self.debug = debug
        self.show_logs = show_logs

    def __del__(self):
        try:
            self.logout()
        except Exception:
            # fail silently
            pass

    def whoami(self):
        """
        Return user email.

        :return: email
        :rtype: str
        """
        return self.application('genestack/signin').invoke('whoami')

    @staticmethod
    def _handle_inactive_user_auth(auth_result):
        """
        Check authentication response and throw descriptive exception for inactive users.

        :param auth_result: authentication response
        """
        if auth_result.get('userDeactivated'):
            raise GenestackAuthenticationException(
                "User's Genestack account was deactivated."
                " Contact your organization administrator")
        elif auth_result.get('userNotConfirmed'):
            raise GenestackAuthenticationException(
                "User's Genestack account was not confirmed")

    def login(self, email, password):
        """
        Attempt a login on the connection with the specified credentials.
        Raises an exception if the login fails.

        :param email: email
        :type email: str
        :param password: password
        :type password: str
        :rtype: None
        :raises: :py:class:`~odm_sdk.GenestackAuthenticationException` if login failed
        """
        logged = self.application('genestack/signin').invoke('authenticate', email, password)
        Connection._handle_inactive_user_auth(logged)
        if not logged['authenticated']:
            hostname = urlsplit(self.server_url).hostname
            raise GenestackAuthenticationException(
                'Fail to login with "%s" to "%s"' % (email, hostname))

    def login_by_token(self, token):
        """
        Attempt a login on the connection with the specified token.
        Raises an exception if the login fails.

        :param token: token
        :rtype: None
        :raises: :py:class:`~odm_sdk.GenestackAuthenticationException` if login failed
        """
        logged = self.application('genestack/signin').invoke('authenticateByApiToken', token)
        Connection._handle_inactive_user_auth(logged)
        if not logged['authenticated']:
            hostname = urlsplit(self.server_url).hostname
            raise GenestackAuthenticationException('Fail to login by token to %s' % hostname)

    def login_by_access_token(self, access_token):
        """
        Attempt a login on the connection with the specified access token.
        Raises an exception if the login fails.

        :param access_token: OAuth access token
        :type access_token: str
        :rtype: None
        :raises: :py:class:`~odm_sdk.GenestackAuthenticationException` if login failed
        """
        access_token = os.getenv(access_token, access_token)
        self.session.headers.update({'Authorization': f'Bearer {access_token}'})
        logged = self.application('genestack/signin').invoke('authenticateOAuthAccessToken', access_token)
        Connection._handle_inactive_user_auth(logged)
        if not logged['authenticated']:
            self.session.headers.pop('Authorization')
            hostname = urlsplit(self.server_url).hostname
            raise GenestackAuthenticationException('Fail to login by token to %s' % hostname)

    def logout(self):
        """
        Logout from server.

        :rtype: None
        """
        self.application('genestack/signin').invoke('signOut')

    def perform_request(self, path, data='', follow=True, headers=None):
        """
        Perform an HTTP request to Genestack server.

        Connects to remote server and sends ``data`` to an endpoint ``path``
        with additional ``headers``.

        :param str path: URL path (endpoint) to be used (concatenated with
                     ``self.server_url``).
        :param dict|file|str data: dictionary, bytes, or file-like object to send in the body
        :param bool follow: should we follow a redirection (if any)
        :param dict[str, str] headers: dictionary of additional headers; list of pairs is
                        supported too until v1.0 (for backward compatibility)
        :return: response from server
        :rtype: Response
        """
        _headers = {'gs-extendSession': 'true'}

        if headers:
            _headers.update(headers)
        try:
            response = self.session.post(
                self.server_url + path, data=data, headers=_headers,
                allow_redirects=follow,
                timeout=int(os.environ.get("GENESTACK_CLIENT_TIMEOUT"))
                if os.environ.get("GENESTACK_CLIENT_TIMEOUT", None) else None)
            if response.status_code == 401:
                raise GenestackAuthenticationException('Authentication failure')
            try:
                response.raise_for_status()
            except HTTPError as e:
                raise GenestackResponseError(*e.args)
            try:
                return Response(response.json())
            except ValueError as e:
                raise GenestackException('Cannot parse content: %s' % e)

        except RequestException as e:
            raise GenestackConnectionFailure(str(e))

    def application(self, application_id):
        """
        Returns an application handler for the application with the specified ID.

        :param application_id: Application ID.
        :type application_id: str
        :return: application class
        :rtype: Application
        """
        return Application(self, application_id)

    def __repr__(self):
        return 'Connection("%s")' % self.server_url

    def get_request(self, path, params=None, follow=True):
        # This request also serves for download method of an application
        # It is possible that next request that uses same connection will fail,
        # that why we create new connection every time instead of reuse self.session
        return requests.get(
            url=self.server_url + path,
            params=params,
            allow_redirects=follow,
            cookies=self.session.cookies
        )

    def post_multipart(self, path, data=None, files=None, follow=True):
        return self.session.post(
            url=self.server_url + path,
            data=data,
            files=files,
            allow_redirects=follow,
        )


class Application(object):
    """
    Create a new application instance for the given connection.
    The connection must be logged in to call the application's methods.
    The application ID can be specified either as an argument to the class constructor
    or by overriding the ``APPLICATION_ID`` attribute in a child class.
    """

    APPLICATION_ID = None

    def __init__(self, connection, application_id=None):
        if application_id and self.APPLICATION_ID:
            raise GenestackException(
                "Application ID specified both as argument and as class variable"
            )
        self.application_id = application_id or self.APPLICATION_ID
        if not self.application_id:
            raise GenestackException('Application ID was not specified')

        self.connection = connection

        # validation of application ID
        if len(self.application_id.split('/')) != 2:
            raise GenestackException(
                'Invalid application ID, expect "{vendor}/{application}" got: %s' % self.application_id
            )

    def __invoke(self, path, post_data, trace=None):
        headers = {}
        if trace:
            headers['Genestack-Trace'] = 'true'
        response = self.connection.perform_request(path, post_data, headers=headers)

        if response.error is not None:
            raise GenestackServerException(
                response.error, path, post_data,
                debug=self.connection.debug,
                stack_trace=response.error_stack_trace
            )

        if response.log and (self.connection.show_logs or self.connection.debug):
            message = '\nLogs:\n' + '\n'.join(
                item['message'] + ('\n' + item['stackTrace'] if item.get('stackTrace') else '') for item in response.log
            )
            print(message)

        return response

    def get_response(self, method, params=None, trace=True):
        """
        Invoke one of the application's public Java methods and return Response object.
        Allow to access to logs and traces in code,
        if you need only result use :py:meth:`~odm_sdk.Application.invoke`

        :param method: name of the public Java method
        :type method: str
        :param params: arguments that will be passed to the Java method.
                       Arguments must be JSON-serializable.
        :type params: tuple
        :param trace: request trace from server
        :type trace: bool
        :return: Response object
        :rtype: Response
        """
        if not params:
            params = []

        post_data = json.dumps(params)
        path = '/application/invoke/%s/%s' % (self.application_id, urllib.parse.quote(method))

        # there might be present also self.__invoke(path, post_data)['log'] -- show it?
        return self.__invoke(path, post_data, trace=trace)

    def invoke(self, method, *params):
        """
        Invoke one of the application's public Java methods.

        :param method: name of the public Java method
        :type method: str
        :param params: arguments that will be passed to the Java method.
                       Arguments must be JSON-serializable.
        :return: JSON-deserialized response
        """
        return self.get_response(method, params).result

    def upload_chunked_file(self, file_path):
        return upload_by_chunks(self, file_path)

    def upload_file(self, file_path, token):
        """
        Upload a file to the current Genestack instance.
        This action requires a special token that can be generated by the application.

        :param file_path: path to existing local file.
        :type file_path: str
        :param token: upload token
        :type file_path: str
        :rtype: None
        """
        if isatty():
            progress = TTYProgress()
        else:
            progress = DottedProgress(40)

        file_to_upload = FileWithCallback(file_path, 'rb', progress)
        filename = os.path.basename(file_path)
        path = '/application/upload/%s/%s/%s' % (
            self.application_id, token, urllib.parse.quote(filename)
        )
        return self.__invoke(path, file_to_upload).result


class FileWithCallback(FileIO):
    def __init__(self, path, mode, callback):
        FileIO.__init__(self, path, mode)
        self.seek(0, os.SEEK_END)
        self.__total = self.tell()
        self.seek(0)
        self.__callback = callback

    def __len__(self):
        return self.__total

    def read(self, size=None):
        data = FileIO.read(self, size)
        self.__callback(os.path.basename(self.name), len(data), self.__total)
        return data


class TTYProgress(object):
    def __init__(self):
        self._seen = 0.0

    def __call__(self, name, size, total):
        if size > 0 and total > 0:
            self._seen += size
            pct = self._seen * 100.0 / total
            sys.stderr.write('\rUploading %s - %.2f%%' % (name, pct))
            if int(pct) >= 100:
                sys.stderr.write('\n')


class DottedProgress(object):
    def __init__(self, full_length):
        self.__full_length = full_length
        self.__dots = 0
        self.__seen = 0.0

    def __call__(self, name, size, total):
        if size > 0 and total > 0:
            if self.__seen == 0:
                sys.stderr.write('Uploading %s: ' % name)
            self.__seen += size
            dots = int(self.__seen * self.__full_length / total)
            while dots > self.__dots and self.__dots < self.__full_length:
                self.__dots += 1
                sys.stderr.write('.')
            if self.__dots == self.__full_length:
                sys.stderr.write('\n')
