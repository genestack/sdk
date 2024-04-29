import argparse
import subprocess
import sys

from odm_sdk import GenestackException


def get_terminal_width():
    """
    Return terminal width in characters (defaults to 80).

    :return: terminal width
    :rtype: int
    """
    try:
        rows, columns = subprocess.check_output(['stty', 'size']).decode().split()
        return int(columns)
    except Exception as e:
        sys.stderr.write('Fail to get terminal size, use 80 as default: %s' % e)
        return 80


def isatty():
    """
    Return ``True`` if the file is connected to a tty device.

    :return: is a tty
    :rtype: bool
    """
    try:
        return sys.stdout.isatty()
    except AttributeError:
        return False


class GenestackArgumentParser(argparse.ArgumentParser):
    def parse_known_args(self, args=None, namespace=None):
        args, argv = super(GenestackArgumentParser, self).parse_known_args(args, namespace)
        if sum([bool(args.token), bool(args.user), bool(args.access_token)]) > 1:
            self.error('Exactly one of token, access_token or user should be specified')
        if args.pwd and not args.user:
            self.error('Password should not be specified without user')
        return args, argv


def make_connection_parser(user=None, password=None, host=None, token=None, access_token=None):
    """
    Creates an argument parser with the provided connection parameters.
    If one of ``email``, ``password`` or ``user`` is specified, they are used. Otherwise, the default
    identity from the local config file will be used.

    :param user: user alias or email
    :type user: str
    :param password: user password
    :type password: str
    :param host: host
    :type host: str
    :param token: API token string
    :type token: str
    :param access_token: access token string
    :type access_token: str
    :return: parser
    :rtype: argparse.ArgumentParser
    """
    parser = GenestackArgumentParser()
    group = parser.add_argument_group('connection')
    group.add_argument('-H', '--host', default=host, help='server host', metavar='<host>')
    group.add_argument('-u', '--user', dest='user', metavar='<user>', default=user,
                       help='user alias from settings or email')
    group.add_argument('-p', '--password', dest='pwd', default=password, metavar='<password>',
                       help='user password')
    group.add_argument('--token', dest='token', default=token, metavar='<api-token>',
                       help='API token to be used instead of the login and password')
    group.add_argument('--access-token', dest='access_token', default=access_token, metavar='<access-token>',
                       help='Access token or environment variable with its value to be used instead '
                            'of the login and password')
    group.add_argument('--debug', dest='debug', action='store_true',
                       help='include server stacktrace into error messages (implies --show-logs)')
    group.add_argument('--show-logs', dest='show_logs', action='store_true',
                       help='print application logs received from server to stdout')
    return parser


def get_user(args=None):
    """
    Returns the user corresponding to the provided arguments.
    If ``args`` is ``None``, uses :py:func:`~odm_sdk.make_connection_parser` to get arguments.

    :param args: result of commandline parse
    :type args: argparse.Namespace
    :return: user
    :rtype: settings.User
    """

    from .settings import config, User

    if args is None:
        args = make_connection_parser().parse_args()

    alias = args.user
    if args.token:
        return User(host=args.host, token=args.token)
    if args.access_token:
        return User(host=args.host, access_token=args.access_token)
    if not args.host and not args.pwd:
        if not alias and config.default_user:
            return config.default_user
        if alias in config.users:
            return config.users[alias]
    return User(email=alias, host=args.host, password=args.pwd, token=args.token)


def get_connection(args=None):
    """
    This is the same as :py:func:`~odm_sdk.get_user` . :py:meth:`~odm_sdk.settings.User.get_connection`
    Generally the fastest way to get an active connection.

    :param args: argument from :attr:`argparse.parse_args`
    :type args: argparse.Namespace
    :return: connection
    :rtype: odm_sdk.Connection
    """
    if args is None:
        args = make_connection_parser().parse_args()
    user = get_user(args)
    return user.get_connection(interactive=True, debug=args.debug, show_logs=args.show_logs)


def ask_confirmation(question, default=None):
    """
    Ask confirmation and return response as boolean value.
    Will be looping until user provides correct credentials.
    Does not check if program is attached to tty device.

    :param question: question to ask, without [y/n] suffix and question mark.
    :param default: default value for empty string. Can be ``'y'``, ``'n'``, and ``None``
    :return: whether user confirms
    :rtype: bool
    """
    if not isatty():
        raise GenestackException("Prompt cannot be called")

    assert default in ('y', 'n', None), 'Wrong default value, expect "n", "y" or None'
    question_suffix = '[%s/%s]' % tuple(x.upper() if x == default else x for x in 'yn')

    while True:
        text = input('%s %s? ' % (question, question_suffix)).strip().lower()
        if not text and default:
            text = default

        if text in ('y', 'yes'):
            return True
        if text in ('n', 'no'):
            return False
        print('Unexpected response please input "y[es]" or "n[o]"')


def interactive_select(items, message, to_string=None, selected=None):
    """
    Asks user to choose one of the items.
    Will be looping until user provides correct credentials.
    Does not check if program is attached to tty device.

    :param items: list of possible choices
    :param message: clarifying message
    :type to_string: function to convert choice to string
    :param selected: selected item by default
    :type selected: str
    :return:
    """
    to_string = to_string or str

    if selected and selected not in items:
        raise GenestackException('Selected item "%s" is not in list: %s' % (selected, items))

    about_default = ''

    while True:
        for i, option in enumerate(items, start=1):
            if option == selected:
                print('* ', end=' ')
                about_default = ' [%s]' % i
            else:
                print('  ', end=' ')
            print('%-2s %s' % ('%s)' % i, to_string(option)))

        raw_index = input('%s%s: ' % (message, about_default)).strip()

        if not raw_index and selected:
            return selected

        if not raw_index.isdigit():
            print('Wrong number: "%s"' % raw_index)
            continue

        item_index = int(raw_index) - 1

        if not 0 <= item_index < len(items):
            print('Number is not in list')
            continue
        return items[item_index]


def validate_constant(cls, key):
    constants = {v for k, v in cls.__dict__.items() if (not k.startswith("_") and isinstance(v, str))}
    return key in constants
