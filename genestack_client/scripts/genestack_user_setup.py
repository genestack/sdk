#!python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import re
import sys
from argparse import ArgumentParser
from getpass import getpass
from operator import attrgetter

from genestack_client import GenestackAuthenticationException
from genestack_client.genestack_shell import Command, GenestackShell
from genestack_client.settings import DEFAULT_HOST, User, config
from genestack_client.utils import interactive_select


def input_host():
    host = raw_input('host [%s]: ' % DEFAULT_HOST).strip()
    return host or DEFAULT_HOST


def validate_alias(alias):
    expression = re.compile('[a-zA-Z0-9_@\-]+$')
    return bool(alias and expression.match(alias))


def input_alias(existing):
    print('Please input alias. (Alias can contain: letters (a-z, A-Z), '
          'digits (0-9), at-sign (@), underscore (_), hyphen (-))')
    while True:
        alias = raw_input('alias: ').strip()
        if not alias:
            print('Alias cannot be empty')
            continue
        if not validate_alias(alias):
            print('Restricted symbols message')
            continue
        if alias in existing:
            print('Alias must be unique')
            continue
        return alias


def create_user_from_input(host, alias):
    """
    Ask credentials interactively and return user that can login to platform.

    :param host:  server host
    :type host:  basestring
    :param alias: user alias
    :type alias: basestring
    :return: user
    :rtype: User
    """
    by_token = 'by token'
    items = [by_token, 'by email and password']
    use_token = interactive_select(items, 'Select authentication') == by_token

    if use_token:
        return create_user_from_token(host, alias=alias)
    else:
        return create_user_from_input_email_and_password(host, alias=alias)


def create_user_from_input_email_and_password(host, alias=None):
    """
    Ask email and password, check that it is possible to login with this credentials
    and return user.

    :param host:  server host
    :type host:  basestring
    :param alias: user alias
    :type alias: basestring
    :return: user
    :rtype: User
    """
    print('Specify email and password for host: "%s"' % host, end=' ')
    if alias:
        print('and alias: "%s"' % alias)
    else:
        print()
    user_login = None
    while True:
        if user_login:
            res = raw_input('Please specify your user login (email) [%s]: ' % user_login).strip()
            if res:
                user_login = res
        else:
            user_login = raw_input('Please specify your user login (email): ').strip()
            if not user_login:
                print('Login cannot be empty')
                continue
        user_password = getpass('Please specify your password for %s: ' % user_login)
        if not user_password:
            print('Password cannot be empty')
            continue

        if not user_login or not user_password:
            print()
            continue
        user = User(user_login, host=host, password=user_password, alias=alias)
        try:
            user.get_connection()
            break
        except GenestackAuthenticationException:
            print('Your username or password was incorrect, please try again')
    return user


def create_user_from_token(host, alias=None):
    print('Host: %s' % host)
    msg = 'Please specify Genestack API token%s: '
    with_alias = '' if not alias else ' for "%s"' % alias
    msg = msg % with_alias
    while True:
        token = getpass(msg)
        if not token:
            print('Token cannot be empty')
            continue
        user = User(email=None, host=host, password=None, alias=alias, token=token)
        try:
            user.get_connection()
            break
        except GenestackAuthenticationException:
            print('Could not login with given token, please try again')
    return user


def check_config():
    config_path = config.get_settings_file()
    if not os.path.exists(config_path):
        print('You do not seem to have a config file yet. '
              'Please run `genestack-user-setup init`. Exiting')
        exit(1)


class AddUser(Command):
    COMMAND = 'add'
    DESCRIPTION = 'Add new user.'
    OFFLINE = True

    def run(self):
        alias = input_alias(config.users.keys())
        host = input_host()
        user = create_user_from_input(host, alias)
        config.add_user(user)
        print('User "%s" has been created' % user.alias)


def select_user(users, selected=None):
    """
    Choose user from users stored in config.

    :param users:
    :param selected:
    :return:
    :rtype: User
    """
    user_list = users.values()
    user_list.sort(key=lambda x: x.alias)
    return interactive_select(user_list, 'Select user', to_string=attrgetter('alias'), selected=selected)


class ChangePassword(Command):
    COMMAND = 'change-password'
    DESCRIPTION = 'Change password for user.'
    OFFLINE = True

    def update_parser(self, parent):
        parent.add_argument('alias', metavar='<alias>', help='Alias for user to change password', nargs='?')

    def run(self):
        check_config()
        users = config.users
        user = users.get(self.args.alias)
        if not user:
            user = select_user(users)

        if not user.email:
            print('User without email could be authorized only by token')
            return

        while True:
            user.password = getpass('Input password for %s: ' % user.alias.encode('utf-8'))
            try:
                user.get_connection()
                break
            except GenestackAuthenticationException:
                continue
        config.change_password(user.alias, user.password)
        print('Password has been changed successfully')


class ChangeToken(Command):
    COMMAND = 'change-token'
    DESCRIPTION = 'Change token for user.'
    OFFLINE = True

    def update_parser(self, parent):
        parent.add_argument('alias', metavar='<alias>',
                            help='Alias for user to change token for', nargs='?')

    def run(self):
        check_config()
        users = config.users
        user = users.get(self.args.alias)
        if not user:
            user = select_user(users)
        new_user = create_user_from_token(user.host, alias=user.alias)
        user.token = new_user.token
        config.change_token(user.alias, user.token)
        print('Token has been changed successfully')


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
            user = select_user(users, selected=config.default_user)
        if user.alias != config.default_user.alias:
            config.set_default_user(user)
            print('Default user has been set to "%s"' % user.alias)
        else:
            print('Default user has not been changed')


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
            user = select_user(users)
        if user.alias == config.default_user.alias:
            print('Cannot delete default user')
            return
        config.remove_user(user)
        print('"%s" has been removed from config' % user.alias)


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
            print('Select user to rename')
            user = select_user(users)
        if not self.args.new_alias or not validate_alias(self.args.new_alias):
            print('Enter new alias')
            new_alias = input_alias(users.keys())
        else:
            new_alias = self.args.new_alias

        new_user = User(email=user.email, alias=new_alias, host=user.host, password=user.password,
                        token=user.token)

        config.add_user(new_user, save=False)
        if user.alias == config.default_user.alias:
            config.set_default_user(new_user, save=False)

        config.remove_user(user)
        print('"%s" alias changed to "%s"' % (user.alias, new_user.alias))


class List(Command):
    COMMAND = 'list'
    DESCRIPTION = 'List all users.'
    OFFLINE = True

    def run(self):
        check_config()
        users = sorted(config.users.items())

        default_user_alias = config.default_user and config.default_user.alias

        for key, user in users:
            print()
            print('%s%s:' % (key, ' (default)' if default_user_alias == key else ''))
            print('  %-10s%s' % ('email', user.email))
            print('  %-10s%s' % ('host', user.host))


class Path(Command):
    COMMAND = 'path'
    DESCRIPTION = 'Show path to configuration file.'
    OFFLINE = True

    def run(self):
        print(config.get_settings_file())


class Init(Command):
    COMMAND = 'init'
    DESCRIPTION = 'Create default settings.'
    OFFLINE = True

    def get_command_parser(self, parser=None):
        parser = parser or ArgumentParser(description=self.DESCRIPTION)
        parser.description = self.DESCRIPTION
        group = parser.add_argument_group('command arguments')
        self.update_parser(group)
        group.add_argument('-H', '--host', default=DEFAULT_HOST,
                           help='Genestack host, '
                                'change it to connect somewhere else than %s' % DEFAULT_HOST,
                           metavar='<host>')
        return parser

    def run(self):
        """
        Create config file if it is not present.

        Catch ``KeyboardInterrupt`` and ``EOFError`` is required here for case
        when this command is run for first time and in shell mode.
        If we don't quit here, shell will continue execution and ask credentials once more.
        """

        # Hardcoded alias that created for the first user only.
        # Normal usecase is when user have single account and don't care about alias name.
        # Advanced users can rename alias.
        default_alias = 'Default'

        try:
            config_path = config.get_settings_file()
            if os.path.exists(config_path):
                print('A config file already exists at %s' % config_path)
                return
            print('If you do not have a Genestack account, you need to create one first')

            user = create_user_from_input(self.args.host, default_alias)
            config.add_user(user)  # adding first user make him default.
            print('Config file at "%s" has been created successfully' % config_path)
        except (KeyboardInterrupt, EOFError):
            sys.stdout.flush()
            sys.stderr.write('\nError: Init is not finished\n')
            exit(1)


class UserManagement(GenestackShell):
    DESCRIPTION = 'Genestack user management application.'
    COMMAND_LIST = [
        Init,
        List,
        AddUser,
        SetDefault,
        ChangePassword,
        ChangeToken,
        Path,
        Remove,
        RenameUser
    ]
    intro = "User setup shell.\nType 'help' for list of available commands.\n\n"
    prompt = 'user_setup> '

    def set_shell_user(self, args):
        config_path = config.get_settings_file()
        if not os.path.exists(config_path):
            print('No config file was found, creating one interactively')
            self.process_command(Init(), ['--host', args.host or DEFAULT_HOST], False)
            args.host = None  # do not provide host for future use of arguments


def main():
    shell = UserManagement()
    shell.cmdloop()

if __name__ == '__main__':
    main()
