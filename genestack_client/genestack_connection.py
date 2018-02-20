# -*- coding: utf-8 -*-

from __future__ import print_function

import cookielib
import json
import os
import sys
import urllib
import urllib2
from distutils.version import StrictVersion
from urlparse import urlsplit

import requests

from genestack_client import (GenestackAuthenticationException, GenestackException,
                              GenestackServerException, GenestackVersionException, __version__)
from genestack_client.chunked_upload import upload_by_chunks
from genestack_client.utils import isatty


class AuthenticationErrorHandler(urllib2.HTTPErrorProcessor):
    def http_error_401(self, req, fp, code, msg, headers):
        raise GenestackAuthenticationException('Authentication failure')


class _NoRedirect(urllib2.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # print('Redirect: %s %s %s -> %s' % (code, msg, req.get_full_url(), newurl))
        return


class _NoRedirectError(urllib2.HTTPErrorProcessor):
    def http_error_307(self, req, fp, code, msg, headers):
        return fp
    http_error_301 = http_error_302 = http_error_303 = http_error_307


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
    To do so, you need to call the :py:meth:`~genestack_client.Connection.login` method.
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
        cj = cookielib.CookieJar()
        self.__cookies_jar = cj
        self.opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(cj), AuthenticationErrorHandler
        )
        self._no_redirect_opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(cj),
            _NoRedirect,
            _NoRedirectError,
            AuthenticationErrorHandler
        )
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

    def login(self, email, password):
        """
        Attempt a login on the connection with the specified credentials.
        Raises an exception if the login fails.

        :param email: email
        :type email: str
        :param password: password
        :type password: str
        :rtype: None
        :raises: :py:class:`~genestack_client.GenestackServerException` if module version is outdated
                 :py:class:`~genestack_client.GenestackAuthenticationException` if login failed
        """
        self.check_version()
        logged = self.application('genestack/signin').invoke('authenticate', email, password)
        if not logged['authenticated']:
            hostname = urlsplit(self.server_url).hostname
            raise GenestackAuthenticationException("Fail to login with %s to %s" % (email, hostname))

    def login_by_token(self, token):
        """
        Attempt a login on the connection with the specified token.
        Raises an exception if the login fails.

        :param token: token
        :rtype: None
        :raises: :py:class:`~genestack_client.GenestackServerException` if module version is outdated
                 :py:class:`~genestack_client.GenestackAuthenticationException` if login failed
        """
        self.check_version()
        logged = self.application('genestack/signin').invoke('authenticateByApiToken', token)
        if not logged['authenticated']:
            hostname = urlsplit(self.server_url).hostname
            raise GenestackAuthenticationException('Fail to login by token to %s' % hostname)

    def check_version(self):
        """
        Check the version of the client library required by the server.
        The server will return a message specifying the compatible version.
        If the current version is not supported, an exception is raised.

        :return: None
        """
        my_version = StrictVersion(__version__)

        try:
            client_version_app = self.application('genestack/clientVersion')
            compatible_version = client_version_app.invoke('getCompatibleVersion')
        except GenestackServerException:
            # We don't know what happened, but it might be due to incompatible client/API versions.
            # Throw a version exception, making sure we tell the user to update.
            raise GenestackVersionException(my_version)

        compatible = StrictVersion(compatible_version)

        if compatible <= my_version:
            return

        raise GenestackVersionException(my_version, compatible)

    def logout(self):
        """
        Logout from server.

        :rtype: None
        """
        self.application('genestack/signin').invoke('signOut')

    def open(self, path, data=None, follow=True, headers=None):
        """
        Sends data to a URL. The URL is the concatenation of the server URL and "path".

        :param path: part of URL that is added to self.server_url
        :param data: dict of parameters, file-like objects or strings
        :param follow: should we follow a redirection if any?
        :param headers: additional headers as list of pairs
        :type headers: list[tuple[str]]
        :return: response
        :rtype: urllib.addinfourl
        """
        if data is None:
            data = ''
        elif isinstance(data, dict):
            data = urllib.urlencode(data)

        self.opener.addheaders = [('gs-extendSession', 'true')]
        if headers:
            self.opener.addheaders += headers

        try:
            if follow:
                return self.opener.open(self.server_url + path, data)
            else:
                return self._no_redirect_opener.open(self.server_url + path, data)
        except urllib2.URLError, e:
            raise urllib2.URLError('Fail to connect %s%s %s' % (
                self.server_url, path, str(e).replace('urlopen error', '').strip('<\ >')
            ))

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
        return requests.get(
            url=self.server_url + path,
            params=params,
            allow_redirects=follow,
            cookies=self.__cookies_jar
        )

    def post_multipart(self, path, data=None, files=None, follow=True):
        return requests.post(
            url=self.server_url + path,
            data=data,
            files=files,
            allow_redirects=follow,
            cookies=self.__cookies_jar
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
        headers = []
        if trace:
            headers.append(('Genestack-Trace', 'true'))
        f = self.connection.open(path, post_data, headers=headers)
        response = Response(json.load(f))

        if response.error is not None:
            raise GenestackServerException(
                response.error, path, post_data,
                debug=self.connection.debug,
                stack_trace=response.error_stack_trace
            )

        if response.log and (self.connection.show_logs or self.connection.debug):
            message = '\nLogs:\n' + '\n'.join(
                item['message'] + item.get('stackTrace', '') for item in response.log
            )
            print(message)

        return response

    def get_response(self, method, params=None, trace=True):
        """
        Invoke one of the application's public Java methods and return Response object.
        Allow to access to logs and traces in code,
        if you need only result use :py:meth:`~genestack_client.Application.invoke`

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
        path = '/application/invoke/%s/%s' % (self.application_id, urllib.quote(method))

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
            self.application_id, token, urllib.quote(filename)
        )
        return self.__invoke(path, file_to_upload).result


class FileWithCallback(file):
    def __init__(self, path, mode, callback):
        file.__init__(self, path, mode)
        self.seek(0, os.SEEK_END)
        self.__total = self.tell()
        self.seek(0)
        self.__callback = callback

    def __len__(self):
        return self.__total

    def read(self, size=None):
        data = file.read(self, size)
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
