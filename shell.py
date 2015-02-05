#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

from datetime import datetime

from genestack.GenestackShell import GenestackShell, Command

APPLICATION_SHELL = 'shell'


class Invoke(Command):
    COMMAND = 'invoke'
    DESCRIPTION = 'invoke shell application'
    OFFLINE = False

    def update_parser(self, p):
        p.add_argument(
            'method',
            help='shell method'
        )
        p.add_argument(
            'params', nargs='*',
            help='params'
        )

    def do_request(self):

        return self.connection.application(APPLICATION_SHELL).invoke(self.args.method, *self.args.params)

    def run(self):
        print self.do_request()


class Time(Invoke):
    DESCRIPTION = 'invoke with timer'

    def run(self):
        t1 = datetime.now()
        result = self.do_request()
        delta = datetime.now() - t1
        print '%s: %s' % (delta, result)


class Shell(GenestackShell):
    COMMAND_LIST = [Time]

    def default(self, line):
        args = line.split()
        if args and args[0] in self.COMMANDS:
            self.process_command(self.COMMANDS[args[0]](), args[1:], self.connection)
        else:
            self.process_command(Invoke(), args, self.connection)

if __name__ == '__main__':
    shell = Shell()
    shell.cmdloop()
