#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2016 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#
import argparse
import json
import shlex
from datetime import datetime

from genestack_client.genestack_shell import GenestackShell, Command

APPLICATION_SHELL = 'genestack/shell'


def serialize_params(params):
    args = []
    for arg in params:
        try:
            args.append(json.loads(arg))
        except ValueError:
            args.append(arg)
    return args


class Call(Command):
    COMMAND = 'call'
    DESCRIPTION = 'call another application\'s method'
    OFFLINE = False

    def update_parser(self, p):
        p.add_argument(
            'applicationId',
            help='full application id'
        )
        p.add_argument(
            'method',
            help='application method'
        )
        p.add_argument(
            'params', nargs=argparse.REMAINDER,
            help='params'
        )

    def do_request(self):
        params = serialize_params(self.args.params)
        return self.connection.application(self.args.applicationId).invoke(self.args.method, *params)

    def run(self):
        res = self.do_request()
        print json.dumps(res, indent=2)


class Time(Call):
    DESCRIPTION = 'invoke with timer'
    COMMAND = 'time'

    def run(self):
        start = datetime.now()
        Call.run(self)
        print 'Execution time: %s' % (datetime.now() - start)


class Shell(GenestackShell):
    COMMAND_LIST = [Time, Call]

    def default(self, line):
        args = shlex.split(line)
        if args and args[0] in self.COMMANDS:
            self.process_command(self.COMMANDS[args[0]](), args[1:], self.connection)
        else:
            self.process_command(Call(), ['genestack/shell'] + args, self.connection)


def main():
    shell = Shell()
    shell.cmdloop()

if __name__ == '__main__':
    main()
