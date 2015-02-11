# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

from getpass import getpass
from genestack import GenestackException, Connection
from genestack.utils import isatty

DEFAULT_HOST = 'platform.genestack.org'


def _get_server_url(host):
        if host.startswith('localhost'):
            return 'http://%s/frontend/endpoint' % host
        else:
            return 'https://%s/endpoint' % host


class User(object):
    def __init__(self, email, alias=None, host=None, password=None):
        self.host = host or DEFAULT_HOST
        self.email = email
        self.password = password  # TODO make property
        self.alias = alias or email

    def get_connection(self, interactive=True):
        connection = Connection(_get_server_url(self.host))
        if self.email and self.password:
            connection.login(self.email, self.password)
        elif interactive:
            self.__interactive_login(connection)
        else:
            raise GenestackException('Not enough user data to login')
        return connection

    def __repr__(self):
        return "User('%s', alias='%s', host='%s', password='%s')" % (self.email, self.alias, self.host, self.password and '*****')

    def __interactive_login(self, connection):
        """
        Login interactive.
        """
        if not isatty():
            raise GenestackException("Interactive login is not possible.")
        email = self.email
        message = 'Connecting to %s' % self.host
        while True:
            if message:
                print message
            if email and '@' in email:
                email = raw_input('E-mail [%s]: ' % email).strip() or email
            else:
                email = raw_input('E-mail: ').strip() or email
            if not email:
                continue
            password = getpass('password for %s: ' % email)
            try:
                connection.login(email, password)
                self.email = email
                self.password = password
                return
            except GenestackException:
                message = 'Your username or password was incorrect for %s. Please try again.' % self.host

