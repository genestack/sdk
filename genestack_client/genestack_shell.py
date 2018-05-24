# -*- coding: utf-8 -*-

from __future__ import print_function

import cmd
import os
import shlex
import sys
from argparse import ArgumentParser, HelpFormatter
from traceback import print_exc

from genestack_client import (GenestackAuthenticationException, GenestackException,
                              GenestackVersionException)
from utils import get_connection, isatty, make_connection_parser, get_terminal_width
from version import __version__

if isatty():
    # To have autocomplete and console navigation on windows you need to have pyreadline installed.
    # Pyreadline replace readline with alias to itself.
    try:
        import readline
    except:
        pass

HELP_SEPARATOR = '\n%s  Help  %s' % ('=' * 20, '=' * 20)


def get_help(parser):
    """
    Return help text for the parser.

    :param parser: parser
    :type parser: ArgumentParser
    :return: fully formatted help string
    :rtype: str
    """
    # Code almost identical with parser.print_help() with next changes:
    # it return text instead print
    # it place group 'command arguments' to the first place
    width = min(get_terminal_width(), 100)
    formatter = HelpFormatter(prog=parser.prog, max_help_position=30, width=width)
    # usage
    formatter.add_usage(parser.usage, parser._actions,
                        parser._mutually_exclusive_groups)
    # description
    formatter.add_text(parser.description)

    # positionals, optionals and user-defined groups
    groups = list(parser._action_groups)
    groups.sort(key=lambda x: x.title != 'command arguments')
    for action_group in groups:
        formatter.start_section(action_group.title)
        formatter.add_text(action_group.description)
        formatter.add_arguments(action_group._group_actions)
        formatter.end_section()

    # epilog
    formatter.add_text(parser.epilog)

    # determine help from format above
    return formatter.format_help()


class Command(object):
    """
    Command class to be inherited.

        - ``COMMAND``: name of the command
        - ``DESCRIPTION``: description as shown in the help message
        - ``OFFLINE``: set to ``True`` if the command does not require a connection to the Genestack server.
    """
    COMMAND = None
    DESCRIPTION = ''
    OFFLINE = False

    # TODO make private all that possible

    def __init__(self):
        self.connection = None
        self.args = None

    def get_command_parser(self, parser=None):
        """
        Returns a command parser. This function is called each time before a command is executed.
        To add new arguments to the command,
        you should override the :py:meth:`~genestack_client.genestack_shell.Command.update_parser` method.

        :param parser: base argument parser. For offline commands and commands inside shell, it will be ``None``.
            For the other cases, it will be the result of :py:func:`~genestack_client.make_connection_parser`
        :type parser: argparse.ArgumentParser
        :return: parser
        :rtype: argparse.ArgumentParser
        """
        parser = parser or ArgumentParser(description=self.DESCRIPTION)
        parser.prog = '%s %s' % (parser.prog, self.COMMAND)
        parser.description = self.DESCRIPTION
        group = parser.add_argument_group("command arguments")
        self.update_parser(group)
        return parser

    def update_parser(self, parent):
        """
        Add arguments for the command. Should be overridden in child classes.

        :param parent: argument group
        :type parent: argparse._ArgumentGroup
        :rtype: None
        """
        pass

    def set_connection(self, conn):
        """
        Set a connection for the command.

        :param conn: connection
        :type conn: genestack_client.Connection
        """
        self.connection = conn

    def set_arguments(self, args):
        """
        Set parsed arguments for the command.

        :param args: parsed arguments
        :type args: argparse.Namespace
        """
        self.args = args

    def get_short_description(self):
        """
        Returns a short description for the command. Used in the "help" message.

        :return short description
        :rtype: str
        """
        return self.DESCRIPTION

    def run(self):
        """
        Override this method to implement the command action.

        Return value of this method is always ignored.
        If this method raises an exception, the command will be treated as failed.

        If this command is executed in the shell mode,
        the failed state is ignored, otherwise exit code ``1`` is returned.

        Raise :py:class:`~genestack_client.genestack_exceptions.GenestackException` to indicate command failure
        without showing the stacktrace.

        :rtype: None
        """
        raise NotImplementedError()


class GenestackShell(cmd.Cmd):
    """
    Arguments to be overridden in children:

        - ``INTRO``: greeting at start of shell mode
        - ``COMMAND_LIST``: list of available commands
        - ``DESCRIPTION``: description for help.

    Run as script:

        .. code-block:: sh

            script.py [connection_args] command [command_args]

    Run as shell:

        .. code-block:: sh

            script.py [connection_args]


    Default shell commands:
        - ``help``: show help about shell or command
        - ``quit``: quits shell
        - ``ctrl+D``: quits shell
    """
    INTRO = ''
    COMMAND_LIST = []
    DESCRIPTION = "Shell and commandline application"

    COMMANDS = {}  # filled in init

    # Don't add docstrings to methods, all methods should be considered private, but due design of Cmd it is not possible
    # TODO make private all that possible

    def get_history_file_path(self):
        """
        Get path to history file.

        :return: path to history file
        :rtype: str
        """
        return os.path.join(os.path.expanduser("~"), '.%s' % self.__class__.__name__)

    def get_names(self):
        return [x for x in cmd.Cmd.get_names(self) if x != 'do_EOF']

    def __init__(self, *args, **kwargs):
        self.COMMANDS = {command.COMMAND: command for command in self.COMMAND_LIST}
        cmd.Cmd.__init__(self, *args, **kwargs)
        self.connection = None

    def get_shell_parser(self, offline=False):
        """
        Returns the parser for shell arguments.

        :return: parser for shell commands
        :rtype: argparse.ArgumentParser
        """
        parents = [] if offline else [make_connection_parser()]
        parser = ArgumentParser(conflict_handler='resolve', description=self.DESCRIPTION, parents=parents)

        # override default help
        parser.add_argument('-h', '--help', action='store_true', help="show this help message and exit")
        parser.add_argument('-v', '--version', action='store_true', help="show version")
        parser.add_argument('command', metavar='<command>', help='"%s" or empty to use shell' % '", "'.join(self.COMMANDS), nargs='?')
        return parser

    def setup_connection(self, args=None):
        try:
            self.connection = get_connection(args)
        except GenestackVersionException as e:
            sys.stderr.write(str(e))
            sys.stderr.write('\n')
            exit(13)

    def preloop(self):
        # Entry point. Check whether we should run a script and exit, or start an interactive shell.

        parser = self.get_shell_parser()
        args, others = parser.parse_known_args()

        if args.version:
            print(__version__)
            exit(0)

        command = self.COMMANDS.get(args.command)
        if command:
            command = command()
        elif args.command:
            print("*** Unknown command: %s" % args.command)
            print(get_help(parser))
            exit(0)
        elif others:
            print("*** Unknown arguments: %s" % ' '.join(others))
            print(get_help(parser))
            exit(0)

        if args.help:
            if not command:
                print(get_help(parser))
            elif command.OFFLINE:
                print(get_help(command.get_command_parser()))
            else:
                print(get_help(command.get_command_parser(make_connection_parser())))
            exit(0)

        if command:
            if not command.OFFLINE:
                self.setup_connection(args)
            else:
                # parse arguments that have same name as connection parser
                parser = self.get_shell_parser(offline=True)
                _, others = parser.parse_known_args()

            exit_code = self.process_command(command, others)
            exit(exit_code)

        # do shell
        try:
            readline.read_history_file(self.get_history_file_path())
            readline.set_history_length(1000)
        except (IOError, NameError):
            pass
        self.set_shell_user(args)

    def set_shell_user(self, args):
        """
        Set the connection for shell mode.

        :param args: script arguments
        :type args: argparse.Namespace
        """
        # set user for shell
        self.setup_connection(args)
        try:
            email = self.connection.whoami()
            self.prompt = '%s> ' % email
        except GenestackAuthenticationException:
            self.prompt = 'anonymous>'
        if self.connection.debug:
            debug_string = ' (with debug enabled)'
        else:
            debug_string = ''
        self.intro = ('genestack_client v{version}{debug_string}\n'
                      '{intro}'.format(version=__version__,
                                       debug_string=debug_string,
                                       intro=self.INTRO)
                      )

    def postloop(self):
        try:
            readline.write_history_file(self.get_history_file_path())
        except (IOError, NameError):
            pass

    def do_EOF(self, line):
        return True

    do_quit = do_EOF

    def process_command(self, command, argument_list, shell=False):
        """
        Runs the given command with the provided arguments and returns the exit code

        :param command: command
        :type command: Command
        :param argument_list: the list of arguments for the command
        :type argument_list: list
        :param shell: should we use shell mode?
        :type shell: bool
        :return: 0 if the command was executed successfully, 1 otherwise

        :rtype: int
        """
        if shell or command.OFFLINE:
            p = command.get_command_parser()
        else:
            p = command.get_command_parser(make_connection_parser())
        try:
            args = p.parse_args(argument_list)
        except SystemExit:
            return 1
        command.set_connection(self.connection)
        command.set_arguments(args)
        try:
            command.run()
            return 0
        except (KeyboardInterrupt, EOFError):
            print()
            print("Command interrupted.")
        except GenestackException as e:
            sys.stdout.flush()
            sys.stderr.write('%s\n' % e)
        except Exception:
            sys.stdout.flush()
            print_exc()
        return 1

    def do_debug(self, line):
        self.connection.debug = not self.connection.debug
        if self.connection.debug:
            print('Debug enabled')
        else:
            print('Debug disabled')

    def get_commands_for_help(self):
        """
        Return list of command - description pairs to shown in shell help command.

        :return: command - description pairs
        :rtype: list[(str, str)]
        """
        commands = [('quit', 'Exit shell.'), ('debug', 'Toggle debug for connection.')]
        for name, value in self.COMMANDS.items():
            commands.append((name, value().get_short_description()))
        return sorted(commands)

    def do_help(self, line):
        print()

        command = self.COMMANDS.get(line)
        if command:
            print(get_help(command().get_command_parser()))
            return

        if not line:
            print(self.doc_header)
            print('=' * len(self.doc_header))
            commands = self.get_commands_for_help()
            max_size = max(len(command_name) for command_name, _ in commands)
            help_size = max((20, max_size + 3))
            for command_name, short_description in self.get_commands_for_help():
                print('%-*s%s' % (help_size, command_name, short_description))
            print('=' * len(self.doc_header))

        try:
            getattr(self, 'help_' + line)()
            return
        except AttributeError:
            pass

        try:
            doc = getattr(self, 'do_' + line).__doc__
            if doc:
                self.stdout.write('%s\n' % str(doc))
                return
        except AttributeError:
            pass

        self.stdout.write('%s\n' % str(self.nohelp % (line,)))

    def emptyline(self):
        # override default cmd behavior.
        pass

    def default(self, line):
        try:
            args = shlex.split(line)
        except Exception as e:
            sys.stderr.write(str(e))
            sys.stderr.write('\n')
            return
        if args and args[0] in self.COMMANDS:
            self.process_command(self.COMMANDS[args[0]](), args[1:], shell=True)
        else:
            self.stdout.write('*** Unknown command: %s\n' % line)

    def completenames(self, text, *ignored):
        dotext = 'do_' + text
        commands = [a[3:] for a in self.get_names() if a.startswith(dotext)]
        commands += [x for x in self.COMMANDS.keys() if x.startswith(text)]
        return commands

    def cmdloop(self, intro=None):
        # TODO on ctrl+C don't exit
        try:
            cmd.Cmd.cmdloop(self, intro=intro)
        except (KeyboardInterrupt, EOFError):
            print()
            self.postloop()
