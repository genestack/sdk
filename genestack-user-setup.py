#!python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

import os
import re
from getpass import getpass
from genestack import GenestackException, get_connection
from genestack.GenestackShell import GenestackShell, Command
from genestack.settings import DEFAULT_HOST, User, config


def ask_host():
    host = raw_input('host [%s]: ' % DEFAULT_HOST).strip()
    return host or DEFAULT_HOST


def ask_alias(existed):
    expression = re.compile('[A-z0-9_@\-]+$')

    print 'Alias can be only alphanum @ _ -'
    while True:
        alias = raw_input('alias: ').strip()
        if not alias:
            print 'Alias cannot be empty.'
            continue
        if not expression.match(alias):
            print 'Restricted symbols message'
            continue
        if alias in existed:
            print 'Alias must be unique.'
            continue
        return alias


def ask_email_and_password(host, alias=None):
    print 'Please input you email and password for %s' % host
    user_login = None
    while True:
        if user_login:
            res = raw_input('Please specify you user login(email) [%s]: ' % user_login).strip()
            if res:
               user_login = res
        else:
            user_login = raw_input('Please specify you user login(email): ').strip()
            if not user_login:
                print 'Login cannot be empty.'
                continue
        user_password = getpass('Please specify you password for %s: ' % user_login)
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
            print 'You email and password does not match. Please try again.'
    return connection, user


class AddUser(Command):
    COMMAND = 'add'
    DESCRIPTION = 'Add new user.'
    OFFLINE = True

    def run(self):
        alias = ask_alias(config.users.keys())
        host = ask_host()
        _, user = ask_email_and_password(host, alias=alias)
        config.add_user(user)
        config.save()


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

    def update_parser(self, parent):
        parent.add_argument('alias', metavar='<alias>', help='Alias for user to change password', nargs='?')

    def run(self):
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
        config.save()


class SetDefault(Command):
    COMMAND = 'default'
    DESCRIPTION = 'Set default user.'
    OFFLINE = True

    def update_parser(self, parent):
        parent.add_argument('alias', metavar='<alias>', help='Alias for user to change password', nargs='?')

    def run(self):
        users = config.users

        user = users.get(self.args.alias)
        if not user:
            user = select_user(users, config.default_user)
        if user.alias != config.default_user.alias:
            print 'Set "%s" as default user.' % user.alias
            config.set_default_user(user)
            config.save()
        else:
            print "Default user was not changed."


class List(Command):
    COMMAND = 'list'
    DESCRIPTION = 'List current users.'
    OFFLINE = True

    def run(self):
        users = sorted(config.users.items())

        default_user_alias = config.default_user and config.default_user.alias

        for key, user in users:
            print
            print '%s%s:' % (key, ' (default)' if default_user_alias == key else '')
            print '  %-10s%s' % ('email', user.email)
            print '  %-10s%s' % ('host', user.host)


class Path(Command):
    COMMAND = 'path'
    DESCRIPTION = 'Show path to config'
    OFFLINE = True

    def run(self):
        print config.get_settings_file()


class Init(Command):
    COMMAND = 'init'
    DESCRIPTION = 'Create default settings.'
    OFFLINE = True

    def run(self):
        config_path = config.get_settings_file()
        if os.path.exists(config_path):
            print "Config is already present at %s" % config_path
            return

        print "To setup you setting you need to have genestack account, please visit %s and create one." % DEFAULT_HOST
        print "This setup can be relaunched later."  # TODO add script name to be lunched

        connection, user = ask_email_and_password(DEFAULT_HOST)
        config.add_user(user)
        config.set_default_user(user)
        config.save()
        return connection


class UserManagement(GenestackShell):
    DESCRIPTION = "Genestack user management application."
    COMMAND_LIST = [Init, List, AddUser, SetDefault, SetPassword, Path]

    def set_shell_user(self, args):
        config_path = config.get_settings_file()
        if not os.path.exists(config_path):
            print "Config is not present, running init manager."
            connection = self.process_command(Init(), [], None)
            self.connection = connection
        else:
            self.connection = get_connection(args)
        email = self.connection.whoami()
        self.prompt = '%s> ' % email
        self.intro = "Hello, %s!" % email


if __name__ == '__main__':
    shell = UserManagement()
    shell.cmdloop()
