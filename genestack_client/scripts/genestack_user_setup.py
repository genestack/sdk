#!python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2016 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

from argparse import ArgumentParser

import os
import re
import sys
from getpass import getpass
from genestack_client import GenestackException
from genestack_client.genestack_shell import GenestackShell, Command
from genestack_client.settings import DEFAULT_HOST, User, config


def ask_host():
    host = raw_input('host [%s]: ' % DEFAULT_HOST).strip()
    return host or DEFAULT_HOST


def validate_alias(alias):
    expression = re.compile('[a-zA-Z0-9_@\-]+$')
    return bool(alias and expression.match(alias))


def ask_alias(existed):
    print 'Please input alias. (Alias can contain: letters (a-Z), digit (0-9), at (@), underscore (_), minus (-))'
    while True:
        alias = raw_input('alias: ').strip()
        if not alias:
            print 'Alias cannot be empty.'
            continue
        if not validate_alias(alias):
            print 'Restricted symbols message'
            continue
        if alias in existed:
            print 'Alias must be unique.'
            continue
        return alias


def ask_email_and_password(host, alias=None):
    print 'Please input your email and password for %s' % host
    user_login = None
    while True:
        if user_login:
            res = raw_input('Please specify your user login(email) [%s]: ' % user_login).strip()
            if res:
                user_login = res
        else:
            user_login = raw_input('Please specify your user login(email): ').strip()
            if not user_login:
                print 'Login cannot be empty.'
                continue
        user_password = getpass('Please specify your password for %s: ' % user_login)
        if not user_password:
            print 'Password cannot be empty'
            continue

        if not user_login or not user_password:
            print
            continue
        user = User(user_login, host=host, password=user_password, alias=alias)
        try:
            connection = user.get_connection()
            break
        except GenestackException:
            print 'Your username or password was incorrect. Please try again.'
    return connection, user


def check_config():
    config_path = config.get_settings_file()
    if not os.path.exists(config_path):
        print "You do not seem to have a config file yet. Please run genestack-user-setup init. Exiting."
        exit(1)


class AddUser(Command):
    COMMAND = 'add'
    DESCRIPTION = 'Add new user.'
    OFFLINE = True

    def run(self):
        alias = ask_alias(config.users.keys())
        host = ask_host()
        _, user = ask_email_and_password(host, alias=alias)
        config.add_user(user)
        print "User %s created" % user.alias


def select_user(users, selected=None):
    user_list = users.values()
    user_list.sort(key=lambda x: x.alias)
    default_message = ''
    selected_alias = selected and selected.alias
    while True:
        for i, user in enumerate(user_list, start=1):
            if user.alias and user.alias == selected_alias:
                print '*',
                default_message = ' [%s]' % i
            else:
                print ' ',
            print '%s) %s' % (i, user.alias)

        raw_user_index = raw_input("Select default user name or number%s: " % default_message).strip()
        if not raw_user_index and selected:
            return selected

        if raw_user_index in users:
            return users[raw_user_index]

        try:
            user_index = int(raw_user_index) - 1
        except ValueError:
            print 'Wrong number or alias: "%s".' % raw_user_index
            continue

        try:
            return user_list[user_index]
        except IndexError:
            print "Number is not in list."
            continue


class SetPassword(Command):
    COMMAND = 'password'
    DESCRIPTION = 'Set password for user.'
    OFFLINE = True

    def update_parser(self, parent):
        parent.add_argument('alias', metavar='<alias>', help='Alias for user to change password', nargs='?')

    def run(self):
        check_config()
        users = config.users
        user = users.get(self.args.alias)
        if not user:
            user = select_user(users, None)  # TODO get current user for shell and command line

        while True:
            user.password = getpass('Input password for %s: ' % user.alias)
            try:
                user.get_connection()
                break
            except GenestackException:
                continue
        config.change_password(user.alias, user.password)
        print 'Password was changed.'


class SetDefault(Command):
    COMMAND = 'default'
    DESCRIPTION = 'Set default user.'
    OFFLINE = True

    def update_parser(self, parent):
        parent.add_argument('alias', metavar='<alias>', help='Alias for user to change password', nargs='?')

    def run(self):
        check_config()
        users = config.users
        user = users.get(self.args.alias)
        if not user:
            user = select_user(users, config.default_user)
        if user.alias != config.default_user.alias:
            print 'Set "%s" as default user.' % user.alias
            config.set_default_user(user)
        else:
            print "Default user was not changed."


class Remove(Command):
    COMMAND = 'remove'
    DESCRIPTION = 'Remove user.'
    OFFLINE = True

    def update_parser(self, parent):
        parent.add_argument('alias', metavar='<alias>', help='Alias for user to change password', nargs='?')

    def run(self):
        check_config()
        users = config.users

        user = users.get(self.args.alias)
        if not user:
            user = select_user(users, config.default_user)
        if user.alias == config.default_user.alias:
            print 'Cant delete default user'
            return
        config.remove_user(user)
        print "%s was removed from config" % user.alias


class RenameUser(Command):
    COMMAND = 'rename'
    DESCRIPTION = 'Rename user.'
    OFFLINE = True

    def update_parser(self, parent):
        parent.add_argument('alias', metavar='<alias>', help='Alias to be renamed', nargs='?')
        parent.add_argument('new_alias', metavar='<new_alias>', help='New alias', nargs='?')

    def run(self):
        check_config()
        users = config.users

        user = users.get(self.args.alias)

        if not user:
            print "Select user to rename."
            user = select_user(users)
        if not self.args.new_alias or not validate_alias(self.args.new_alias):
            print "Select new alias."
            new_alias = ask_alias(users.keys())
        else:
            new_alias = self.args.new_alias

        new_user = User(email=user.email, alias=new_alias, host=user.host, password=user.password)

        config.add_user(new_user, save=False)
        if user.alias == config.default_user.alias:
            config.set_default_user(new_user, save=False)

        config.remove_user(user)
        print '"%s" alias changed to "%s"' % (user.alias, new_user.alias)


class List(Command):
    COMMAND = 'list'
    DESCRIPTION = 'List all users.'
    OFFLINE = True

    def run(self):
        check_config()
        users = sorted(config.users.items())

        default_user_alias = config.default_user and config.default_user.alias

        for key, user in users:
            print
            print '%s%s:' % (key, ' (default)' if default_user_alias == key else '')
            print '  %-10s%s' % ('email', user.email)
            print '  %-10s%s' % ('host', user.host)


class Path(Command):
    COMMAND = 'path'
    DESCRIPTION = 'Show path to configuration file.'
    OFFLINE = True

    def run(self):
        print config.get_settings_file()


class Init(Command):
    COMMAND = 'init'
    DESCRIPTION = 'Create default settings.'
    OFFLINE = True

    def get_command_parser(self, parser=None):
        parser = parser or ArgumentParser(description=self.DESCRIPTION)
        parser.description = self.DESCRIPTION
        group = parser.add_argument_group("command arguments")
        self.update_parser(group)
        group.add_argument('-H', '--host', default=DEFAULT_HOST,
                           help="server host, use it to make init with different host, default: %s" % DEFAULT_HOST,
                           metavar='<host>')
        return parser

    def run(self):
        """
        Create config file if it is not present.

        Catch ``KeyboardInterrupt`` and ``EOFError`` is required here for case
        when this command is run for first time and in shell mode.
        If we don't quit here, shell will continue execution and ask credentials once more.
        """
        try:
            config_path = config.get_settings_file()
            if os.path.exists(config_path):
                print "A config file was already found at %s" % config_path
                return
            print "If you do not have a Genestack account, you need to create one first."

            connection, user = ask_email_and_password(self.args.host)
            config.add_user(user)  # adding first user make him default.
            print "Initialization finished. Config file created at %s" % config_path
        except (KeyboardInterrupt, EOFError):
            sys.stdout.flush()
            sys.stderr.write('\nError: Init is not finished\n')
            sys.stderr.flush()
            exit(1)


class UserManagement(GenestackShell):
    DESCRIPTION = "Genestack user management application."
    COMMAND_LIST = [Init, List, AddUser, SetDefault, SetPassword, Path, Remove, RenameUser]
    intro = "User setup shell.\nType 'help' for list of available commands.\n\n"
    prompt = 'user_setup> '

    def set_shell_user(self, args):
        config_path = config.get_settings_file()
        if not os.path.exists(config_path):
            print "No config file was found; starting init."
            self.process_command(Init(), ['--host', args.host or DEFAULT_HOST], None)
            args.host = None  # do not provide host for future use of arguments


def main():
    shell = UserManagement()
    shell.cmdloop()

if __name__ == '__main__':
    main()
