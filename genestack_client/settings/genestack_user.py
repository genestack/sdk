# -*- coding: utf-8 -*-

from getpass import getpass

from genestack_client import Connection, GenestackAuthenticationException, GenestackException
from genestack_client.utils import ask_confirmation, isatty

DEFAULT_HOST = 'platform.genestack.org'


def _get_server_url(host):
        if host.startswith('localhost'):
            return 'http://%s/frontend/endpoint' % host
        else:
            return 'https://%s/endpoint' % host


class User(object):
    """
    Class encapsulating all user info required for authentication.

    That includes:
     - user alias
     - server URL (or is it hostname?)
     - email/password pair
    """
    def __init__(self, email, alias=None, host=None, password=None):
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
        if self.email and self.password:
            connection.login(self.email, self.password)
        elif interactive:
            self.__interactive_login(connection)
        #else:
        #    raise GenestackException('Not enough user data to login')
        return connection

    def __repr__(self):
        return "User('%s', alias='%s', host='%s', password='%s')" % (self.email, self.alias, self.host, self.password and '*****')

    def __interactive_login(self, connection):
        if not isatty():
            raise GenestackException("Interactive login is not possible")
        connection.check_version()

        email = self.email
        message = 'Connecting to %s' % self.host
        while True:
            if message:
                print message
            if email and '@' in email:
                email = raw_input('e-mail [%s]: ' % email).strip() or email
            else:
                email = raw_input('e-mail: ').strip() or email
            if not email:
                anonymously = ask_confirmation('Proceed anonymously', default='n')
                if anonymously:
                    return
                continue
            password = getpass('password for %s: ' % email)
            try:
                connection.login(email, password)
                self.email = email
                self.password = password
                return
            except GenestackAuthenticationException:
                message = 'Your username or password was incorrect for %s. Please try again.' % self.host

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
