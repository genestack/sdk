# -*- coding: utf-8 -*-

from __future__ import print_function

from getpass import getpass
from urlparse import urlsplit

from genestack_client import Connection, GenestackAuthenticationException, GenestackException
from genestack_client.utils import isatty, interactive_select

DEFAULT_HOST = 'platform.genestack.org'


def _get_server_url(host):
    has_scheme = bool(urlsplit(host).scheme)

    # compatibility with dev settings
    # TODO Add code that will do migration in configs and remove this check.
    if host.startswith('localhost'):
        return 'http://%s/frontend/endpoint' % host

    if has_scheme:
        return '%s/endpoint' % host
    else:
        return 'https://%s/endpoint' % host


class User(object):
    """
    Class encapsulating all user info required for authentication.

    That includes:
     - user alias
     - server URL (or is it hostname?)
     - token *or* email/password pair
    """
    def __init__(self, email, alias=None, host=None, password=None, token=None):
        """
        All fields are optional.
        If ``alias`` is None it will be the same as ``email``.
        If no ``host`` is specified, the ``DEFAULT_HOST`` be used.

        If you login interactively, no ``email`` or ``password`` is required.
        The alias is used to find the matching user in :py:func:`~genestack_client.get_user`

        :param email: email
        :type email: str
        :param alias: alias
        :type alias: str
        :param host: host
        :type host: str
        :param password: password
        :type password: str
        """
        self.host = host or DEFAULT_HOST
        self.email = email
        self.password = password  # TODO make property
        self.alias = alias or email
        self.token = token

    def get_connection(self, interactive=True, debug=False, show_logs=False):
        """
        Return a logged-in connection for current user.
        If ``interactive`` is ``True`` and the password or email are unknown,
        they will be asked in interactive mode.
        If no host is specified, the ``DEFAULT_HOST`` will be used.

        :param interactive: ask email and/or password interactively.
        :type interactive: bool
        :param debug: print stack trace in case of exception
        :type debug: bool
        :param show_logs: print application logs (received from server)
        :type show_logs: bool
        :return: logged connection
        :rtype: genestack_client.Connection
        """
        connection = Connection(_get_server_url(self.host), debug=debug, show_logs=show_logs)
        if self.token:
            connection.login_by_token(self.token)
        elif self.email and self.password:
            connection.login(self.email, self.password)
        elif interactive:
            self.__interactive_login(connection)
        #else:
        #    raise GenestackException('Not enough user data to login')
        return connection

    def __repr__(self):
        return "User('%s', alias='%s', host='%s', password='%s', token='%s')" % (
            self.email, self.alias, self.host, self.password and '*****', self.token and '*****')

    def __interactive_login(self, connection):
        if not isatty():
            raise GenestackException("Interactive login is not possible")
        connection.check_version()

        email = self.email
        message = 'Connecting to %s' % self.host

        login_by_token = 'by token'
        login_by_email = 'by email and password'
        login_anonymously = 'anonymously'

        choice = interactive_select([login_by_token, login_by_email, login_anonymously],
                                    'How do you want to login')

        if choice == login_anonymously:
            return

        while True:
            if message:
                print(message)

            if choice == login_by_email:
                input_message = 'e-mail [%s]: ' % email if email and '@' in email else 'e-mail: '
                email = raw_input(input_message).strip() or email

                password = getpass('password for %s: ' % email)
                try:
                    connection.login(email, password)
                    self.email = email
                    self.password = password
                    return
                except GenestackAuthenticationException:
                    message = ('Your username and password have been rejected by %s, '
                               'please try again' % self.host)
            else:
                token = getpass('token: ')
                try:
                    connection.login_by_token(token)
                    self.token = token
                    return
                except GenestackAuthenticationException:
                    message = 'Your token has been rejected by %s, please try again' % self.host

    def __eq__(self, other):
        return (
            isinstance(other, User) and
            self.alias == other.alias and
            self.password == other.password and
            self.host == other.host and
            self.email == other.email
        )

    def __ne__(self, other):
        return not self.__eq__(other)
