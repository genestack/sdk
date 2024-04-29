from getpass import getpass
from urllib.parse import urlsplit

import requests

from odm_sdk import Connection, GenestackAuthenticationException, GenestackException
from odm_sdk.utils import isatty, interactive_select


def _get_server_url(host):
    split_host = urlsplit(host)
    has_scheme = bool(split_host.scheme)

    # default to HTTPS if not explicitly defined
    url_stub = host if has_scheme else 'https://%s' % host
    url_stub = url_stub.rstrip('/')
    # trust provided path if it ends with '/frontend'
    if url_stub.split('/')[-1] == 'frontend':
        return '/'.join([url_stub, 'endpoint'])
    # return '.../frontend/endpoint' if '.../frontend/health' works
    if requests.get('%s/frontend/health' % url_stub).ok:
        return '%s/frontend/endpoint' % url_stub

    raise GenestackAuthenticationException(
        "Could not connect to host '{}', check if it is defined correctly"
        "".format(host))


def _read_non_canonical(msg):
    """
    An enhanced input method designed to read user inputs that may exceed the standard terminal input buffer size,
    typically limited to 1024 characters. It is required for interactively reading lengthy inputs such as raw access
    tokens directly from the user.
    The function attempts to switch the terminal to non-canonical mode, this mode is only supported on Unix-like
    systems where the termios module is available.
    :param msg: The prompt message displayed to the user.
    :return: The user input, stripped of leading and trailing whitespace.
    """
    try:
        import termios, tty, atexit, sys
        termios.tcgetattr, termios.tcsetattr
    except (ImportError, AttributeError):
        # fallback to standard input on systems that don't support termios
        return input(msg).strip()
    fd = sys.stdin.fileno()
    original_attrs = termios.tcgetattr(fd)
    # ensure that terminal settings are restored to their original state on program exit
    atexit.register(lambda: termios.tcsetattr(fd, termios.TCSADRAIN, original_attrs))

    # temporarily switch to non-canonical mode modifying local modes
    new_attrs = termios.tcgetattr(fd)
    new_attrs[3] = new_attrs[3] & ~termios.ICANON
    termios.tcsetattr(fd, termios.TCSADRAIN, new_attrs)
    try:
        return input(msg).strip()
    finally:
        # restore the original settings
        termios.tcsetattr(fd, termios.TCSADRAIN, original_attrs)


class User(object):
    """
    Class encapsulating all user info required for authentication.

    That includes:
     - user alias
     - server URL (or is it hostname?)
     - token *or* email/password pair
    """
    def __init__(self, email=None, alias=None, host=None, password=None, token=None, access_token=None):
        """
        All fields are optional.
        If ``alias`` is None it will be the same as ``email``.

        If you login interactively, no ``email`` or ``password`` is required.
        The alias is used to find the matching user in :py:func:`~odm_sdk.get_user`

        :param email: email
        :type email: str
        :param alias: alias
        :type alias: str
        :param host: host
        :type host: str
        :param password: password
        :type password: str
        """
        self.host = host
        self.email = email
        self.password = password  # TODO make property
        self.alias = alias or email
        self.token = token
        self.access_token = access_token

    def get_connection(self, interactive=True, debug=False, show_logs=False):
        """
        Return a logged-in connection for current user.
        If ``interactive`` is ``True`` and the password or email are unknown,
        they will be asked in interactive mode.

        :param interactive: ask email and/or password interactively.
        :type interactive: bool
        :param debug: print stack trace in case of exception
        :type debug: bool
        :param show_logs: print application logs (received from server)
        :type show_logs: bool
        :return: logged connection
        :rtype: odm_sdk.Connection
        """
        connection = Connection(_get_server_url(self.host), debug=debug, show_logs=show_logs)
        if self.token:
            connection.login_by_token(self.token)
        elif self.access_token:
            connection.login_by_access_token(self.access_token)
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

        email = self.email
        message = 'Connecting to %s' % self.host

        login_by_token = 'by token'
        login_by_access_token = 'by access token'
        login_by_email = 'by email and password'
        login_anonymously = 'anonymously'

        choice = interactive_select([login_by_token, login_by_access_token, login_by_email, login_anonymously],
                                    'How do you want to login')

        if choice == login_anonymously:
            return

        while True:
            if message:
                print(message)

            if choice == login_by_email:
                input_message = 'e-mail [%s]: ' % email if email and '@' in email else 'e-mail: '
                email = input(input_message).strip() or email

                password = getpass('password for %s: ' % email)
                try:
                    connection.login(email, password)
                    self.email = email
                    self.password = password
                    return
                except GenestackAuthenticationException:
                    message = ('Your username and password have been rejected by %s, '
                               'please try again' % self.host)
            elif choice == login_by_access_token:
                access_token = _read_non_canonical('access token or environment variable with its value: ')
                try:
                    connection.login_by_access_token(access_token)
                    self.access_token = access_token
                    return
                except GenestackAuthenticationException:
                    message = 'Your access token has been rejected by %s, please try again' % self.host
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
