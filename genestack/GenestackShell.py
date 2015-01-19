#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#
"""
Base shell class used to create shell applications.
"""

from argparse import ArgumentParser
import sys
import os
import cmd
import shlex
from traceback import print_exc
from Exceptions import GenestackException
from utils import isatty, make_connection_parser, get_connection

if isatty():
    # To have autocomplete and console navigation on windows you need to have pyreadline installed.
    # Pyreadline replace readline with alias to itself.
    try:
        import readline
    except:
        pass

HELP_SEPARATOR = '\n%s  Help  %s' % ('=' * 20, '=' * 20)


def get_help(parser):
    formatter = parser._get_formatter()

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
    COMMAND = None
    DESCRIPTION = ''
    OFFLINE = False

    def __init__(self):
        self.connection = None
        self.args = None

    def get_command_parser(self, parser=None):
        parser = parser or ArgumentParser(description=self.DESCRIPTION)
        parser.description = self.DESCRIPTION
        group = parser.add_argument_group("command arguments")
        self.update_parser(group)
        return parser

    def update_parser(self, parent):
        pass

    def set_connection(self, conn):
        self.connection = conn

    def set_arguments(self, args):
        self.args = args

    def get_short_description(self):
        return self.DESCRIPTION


class GenestackShell(cmd.Cmd):
    INTRO = ''
    COMMAND_LIST = []
    COMMANDS = {}
    DESCRIPTION = "Shell and commandline application"

    def get_history_file(self):
        return os.path.join(os.path.expanduser("~"), '.%s' % self.__class__.__name__)

    def __init__(self, *args, **kwargs):
        self.COMMANDS = {command.COMMAND: command for command in self.COMMAND_LIST}
        cmd.Cmd.__init__(self, *args, **kwargs)

    def get_shell_parser(self):
        parser = ArgumentParser(conflict_handler='resolve', description=self.DESCRIPTION,
                                parents=[make_connection_parser()])
        # override default help
        parser.add_argument('-h', '--help', action='store_true', help="show this help message and exit")
        parser.add_argument('command', metavar='<command>', help='"%s" or empty to use shell' % '", "'.join(self.COMMANDS), nargs='?')
        return parser

    def preloop(self):


        parser = self.get_shell_parser()
        args, others = parser.parse_known_args()

        command = self.COMMANDS.get(args.command)
        if command:
            command = command()
        elif args.command:
            print "*** Unknown command: %s" % args.command
            print get_help(parser)
            exit(0)
        elif others:
            print "*** Unknown arguments: %s" % ' '.join(others)
            print get_help(parser)
            exit(0)

        if args.help:
            if not command:
                print get_help(parser)
            elif command.OFFLINE:
                print get_help(command.get_command_parser())
            else:
                print get_help(command.get_command_parser(make_connection_parser()))
            exit(0)

        if command:
            if not command.OFFLINE:
                connection = get_connection(args)
            else:
                connection = None
            self.process_command(command, others, connection)
            exit(0)

        # do shell
        try:
            readline.read_history_file(self.get_history_file())
        except (IOError, NameError):
            pass
        self.set_shell_user(args)

    def set_shell_user(self, args):
        """Set user for shell."""
        self.connection = get_connection(args)
        email = self.connection.whoami()
        self.prompt = '%s> ' % email
        self.INTRO = "Hello, %s!" % email

    def postloop(self):
        try:
            readline.write_history_file(self.get_history_file())
        except (IOError, NameError):
            pass

    def do_EOF(self, line):
        """Exit shell."""
        return True
    do_quit = do_EOF

    def process_command(self, command, argument_line, connection, shell=False):
        if shell:
            p = command.get_command_parser()
        else:
            p = command.get_command_parser(make_connection_parser())
        try:
            args = p.parse_args(argument_line)
        except SystemExit:
            return
        command.set_connection(connection)
        command.set_arguments(args)
        try:
            return command.run()
        except (KeyboardInterrupt, EOFError):
            print
            print "Command interrupted."
            return
        except (GenestackException, Exception) as e:
            sys.stdout.flush()
            sys.stderr.write('%s\n' % e)
            sys.stderr.flush()
            print_exc()

    def do_help(self, line):
        print

        command = self.COMMANDS.get(line)
        if command:
            print get_help(command().get_command_parser())
            return

        if not line:
            commands = {}
            for name, value in self.COMMANDS.items():
                commands[name] = value().get_short_description()
            print self.doc_header
            print '=' * len(self.doc_header)
            for command_name, short_description in commands.items():
                print '%-20s%s' % (command_name, short_description)
            print '=' * len(self.doc_header)
            return

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
        pass

    def default(self, line):
        args = shlex.split(line)
        if args and args[0] in self.COMMANDS:
            self.process_command(self.COMMANDS[args[0]](), args[1:], self.connection, shell=True)
        else:
            self.stdout.write('*** Unknown command: %s\n' % line)

    def completenames(self, text, *ignored):
        dotext = 'do_' + text
        commands = [a[3:] for a in self.get_names() if a.startswith(dotext)]
        commands += [x for x in self.COMMANDS.keys() if x.startswith(text)]
        return commands
