# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

import os
import sys
import urllib
import urllib2
import cookielib
import json
from Exceptions import GenestackServerException, GenestackException
from utils import isatty


class AuthenticationErrorHandler(urllib2.HTTPErrorProcessor):
    def http_error_401(self, req, fp, code, msg, headers):
        raise GenestackException('Authentication failure')


class _NoRedirect(urllib2.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        #print 'Redirect: %s %s %s -> %s' % (code, msg, req.get_full_url(), newurl)
        return


class _NoRedirectError(urllib2.HTTPErrorProcessor):
    def http_error_307(self, req, fp, code, msg, headers):
        return fp
    http_error_301 = http_error_302 = http_error_303 = http_error_307


class Connection:
    """
    Connection to specified url. Server url is not same as host. If include protocol host and path: ``https://platform.genestack.org/endpoint``

    Connection is not logged by default. To access applications methods you need to :attr:`login`.
    """
    DEFAULT_VENDOR = 'genestack'

    def __init__(self, server_url):
        self.server_url = server_url
        cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj), AuthenticationErrorHandler)
        self.opener.addheaders.append(('gs-extendSession', 'true'))
        self._no_redirect_opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj), _NoRedirect, _NoRedirectError, AuthenticationErrorHandler)

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
        Login connection with given credentials. Raises exception if login failed.

        :param email: login at server
        :type email: str
        :param password: password
        :type password: str
        :rtype: None
        :raises: GenestackServerException: if login failed
        """
        logged = self.application('genestack/signin').invoke('authenticate', email, password)
        if not logged:
            raise GenestackException("Fail to login %s" % email)

    def logout(self):
        """
        Logout from server.

        :rtype: None
        """
        self.open('/signOut', follow=False)

    def open(self, path, data=None, follow=True):
        """
        Sends data to url. Url is concatenated server url and path.

        :param path: part of url that added to self.server_url
        :param data: dict of parameters or file-like object or string
        :param follow: flag to follow redirect
        :return: response
        :rtype: urllib.addinfourl
        """
        if data is None:
            data = ''
        elif isinstance(data, dict):
            data = urllib.urlencode(data)
        try:
            if follow:
                return self.opener.open(self.server_url + path, data)
            else:
                return self._no_redirect_opener.open(self.server_url + path, data)
        except urllib2.URLError, e:
            raise urllib2.URLError('Fail to connect %s%s %s' % (self.server_url,
                                                                path,
                                                                str(e).replace('urlopen error', '').strip('<\ >')))

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


class Application:
    """
    Create new application instance for given connection. Connection must be logged in to call methods.

    application_id can be specified as init argument or in APPLICATION_ID class variable in case of using inheritance.
    """

    APPLICATION_ID = None

    def __init__(self, connection, application_id=None):
        application_id = application_id or self.APPLICATION_ID
        if not application_id:
            raise GenestackException('Application ID was not specified')

        self.connection = connection
        parts = application_id.split('/')
        if len(parts) == 1:
            self.vendor = 'genestack'
            self.application = application_id
            print 'Deprecation warning: use "genestack/%(id)s" instead of "%(id)s"' % {'id': application_id}
        elif len(parts) == 2:
            self.vendor = parts[0]
            self.application = parts[1]
        else:
            raise GenestackException('Invalid application ID: %s' % application_id)

    def __invoke(self, path, to_post):
        f = self.connection.open(path, to_post)
        response = json.load(f)
        if isinstance(response, dict) and 'error' in response:
            raise GenestackServerException(
                response['error'], path, to_post,
                stack_trace=response.get('errorStackTrace')
            )
        return response

    def invoke(self, method, *params):
        """
        Invoke application method.

        :param method: name of method
        :type method: str
        :param params: arguments that will be passed to java method. Arguments must be json serializable.
        :return: json deserialized response.
        """

        to_post = {'method': method}
        if params:
            to_post['parameters'] = json.dumps(params)

        path = '/application/invoke/%s/%s' % (self.vendor, self.application)

        return self.__invoke(path, to_post)


    def upload_file(self, file_path, token):
        from chunk_upload import chunk_upload

        return chunk_upload(file_path)

    # def upload_file(self, file_path, token):
    #     """
    #     Upload file to server storage. Require special token that can be generated by application.
    #
    #     :param file_path: path to existing file.
    #     :type file_path: str
    #     :param token: upload token
    #     :type file_path: str
    #     :rtype: None
    #     """
    #     if isatty():
    #         progress = TTYProgress()
    #     else:
    #         progress = DottedProgress(40)
    #
    #     file_to_upload = FileWithCallback(file_path, 'rb', progress)
    #     filename = os.path.basename(file_path)
    #     path = '/application/upload/%s/%s/%s/%s' % (
    #         self.vendor, self.application, token, urllib.quote(filename)
    #     )
    #     return self.__invoke(path, file_to_upload)


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
        self.__callback(self, len(data), self.__total)
        return data


class TTYProgress(object):
    def __init__(self):
        self._seen = 0.0

    def __call__(self, file_obj, size, total):
        if size > 0 and total > 0:
            self._seen += size
            pct = self._seen * 100.0 / total
            sys.stderr.write('\rUploading %s - %.2f%%' % (os.path.basename(file_obj.name), pct))
            if int(pct) >= 100:
                sys.stderr.write('\n')
            sys.stderr.flush()


class DottedProgress(object):
    def __init__(self, full_length):
        self.__full_length = full_length
        self.__dots = 0
        self.__seen = 0.0

    def __call__(self, file_obj, size, total):
        if size > 0 and total > 0:
            if self.__seen == 0:
                sys.stderr.write('Uploading %s: ' % os.path.basename(file_obj.name))
            self.__seen += size
            dots = int(self.__seen * self.__full_length / total)
            while dots > self.__dots and self.__dots < self.__full_length:
                self.__dots += 1
                sys.stderr.write('.')
            if self.__dots == self.__full_length:
                sys.stderr.write('\n')
            sys.stderr.flush()
