# -*- coding: utf-8 -*-

import os
import platform
from copy import deepcopy
from xml.dom.minidom import getDOMImplementation, parse

import sys

from genestack_client import GenestackException
from genestack_client.settings.genestack_user import User
from genestack_client.utils import ask_confirmation

_PASSWORD_KEYRING = 'Genestack SDK'
_TOKEN_KEYRING = 'Genestack SDK (token)'

_SETTING_FILE_NAME = 'genestack.xml'
_SETTINGS_DIR = '.genestack'


class Config(object):
    def __init__(self):
        self.__default_user = None
        self.__users = {}
        self.store_raw = None
        self.store_raw_session = None

    def get_settings_folder(self):
        if platform.system() == 'Windows':
            import ctypes.wintypes

            # http://stackoverflow.com/a/3859336/1310066 26 is Roaming folder
            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(0, 26, 0, 0, buf)
            path = os.path.join(str(buf.value), _SETTINGS_DIR)
        else:
            path = os.path.join(os.path.expanduser('~/'), _SETTINGS_DIR)
        return path

    def get_settings_file(self):
        return os.path.join(self.get_settings_folder(), _SETTING_FILE_NAME)

    @property
    def default_user(self):
        return deepcopy(self.__default_user)

    @property
    def users(self):
        return deepcopy(self.__users)

    def remove_user(self, user):
        del self.__users[user.alias]
        self.save()
        try:
            import keyring
        except ImportError:
            return
        try:
            if keyring.get_password(_PASSWORD_KEYRING, user.alias):
                keyring.delete_password(_PASSWORD_KEYRING, user.alias)
            if keyring.get_password(_TOKEN_KEYRING, user.alias):
                keyring.delete_password(_TOKEN_KEYRING, user.alias)
        except Exception as e:
            sys.stderr.write('Error while deleting user password for %s: %s\n' % (user.alias, e))

    def add_user(self, user, save=True):
        if not user.alias:
            raise GenestackException('Cannot add user without alias')
        if user.alias in self.__users:
            raise GenestackException('User alias "%s" already exists' % user.alias)
        self.__users[user.alias] = user
        if len(self.__users) == 1:
            self.set_default_user(user, save=False)
        if save:
            self.save()

    def set_default_user(self, user, save=True):
        if user.alias not in self.__users:
            raise GenestackException('User "%s" does not exist' % user.alias)
        if not self.default_user or user.alias != self.default_user.alias:
            self.__default_user = user
        if save:
            self.save()

    def load(self):
        config_path = self.get_settings_file()

        if not os.path.exists(config_path):
            return

        def get_text(parent, tag):
            elements = parent.getElementsByTagName(tag)
            if len(elements) == 1:
                return elements[0].childNodes[0].data.strip()
            return None

        with open(config_path) as f:
            dom = parse(f)

            users = dom.getElementsByTagName('user')
            for user in users:
                alias = get_text(user, 'alias')
                host = get_text(user, 'host')
                email = get_text(user, 'email')
                password = get_text(user, 'password')
                token = get_text(user, 'token')
                if not password:
                    try:
                        import keyring
                        password = keyring.get_password(_PASSWORD_KEYRING, alias)
                    except Exception as e:
                        sys.stderr.write('Fail to load password for alias "%s": %s\n' % (alias, e))
                if not token:
                    try:
                        import keyring
                        token = keyring.get_password(_TOKEN_KEYRING, alias)
                    except Exception as e:
                        sys.stderr.write('Fail to load token for alias "%s": %s\n' % (alias, e))
                self.add_user(User(email, alias=alias, host=host, password=password,
                                   token=token), save=False)

        default_user_alias = get_text(dom, 'default_user')
        store_raw_text = get_text(dom, 'store_raw')
        if store_raw_text == 'True':
            self.store_raw = True
        elif store_raw_text == 'False':
            self.store_raw = False
        try:
            default_user = self.__users[default_user_alias]
            self.set_default_user(default_user, save=False)
        except KeyError:
            raise GenestackException('Cannot set find user: "%s" is not present in config users' % default_user_alias)

    def change_password(self, alias, password):
        user = self.__users[alias]
        user.password = password
        self.save()

    def change_token(self, alias, token):
        user = self.__users[alias]
        user.token = token
        self.save()

    def save(self):
        settings_folder = self.get_settings_folder()
        if not os.path.exists(settings_folder):
            os.makedirs(settings_folder)
        config_path = self.get_settings_file()

        dom = getDOMImplementation()
        document = dom.createDocument(None, 'genestack', None)
        top = document.documentElement
        users_element = document.createElement('users')
        top.appendChild(users_element)

        for user in self.__users.values():
            if not user.alias:
                continue

            user_element = document.createElement('user')
            users_element.appendChild(user_element)
            alias_element = document.createElement('alias')
            alias_element.appendChild(document.createTextNode(user.alias))
            user_element.appendChild(alias_element)

            if user.email:
                email_element = document.createElement('email')
                email_element.appendChild(document.createTextNode(user.email))
                user_element.appendChild(email_element)

            if user.host:
                host_element = document.createElement('host')
                host_element.appendChild(document.createTextNode(user.host))
                user_element.appendChild(host_element)

            if user.password:
                try:
                    self._store_value_securely(_PASSWORD_KEYRING, user.alias, user.password)
                except Exception:
                    self._store_value_insecurely(user.password, document, user_element, 'password')
            if user.token:
                try:
                    self._store_value_securely(_TOKEN_KEYRING, user.alias, user.token, )
                except Exception:
                    self._store_value_insecurely(user.token, document, user_element, 'token')

        if self.default_user:
            default_user_element = document.createElement('default_user')
            top.appendChild(default_user_element)
            default_user_element.appendChild(document.createTextNode(self.default_user.alias))
        if self.store_raw is not None:
            store_raw_element = document.createElement('store_raw')
            top.appendChild(store_raw_element)
            store_raw_element.appendChild(document.createTextNode(str(self.store_raw)))
        with open(config_path, 'w') as f:
            document.writexml(f, indent='', addindent='    ', newl='\n')

    def _store_value_insecurely(self, value, document, parent, element_name):
        """
        Store value in XML config file.

        :param value: value to be stored
        :type value: basestring
        :param document: document
        :type document: xml.dom.minidom.Document
        :param parent: parent element
        :type parent: xml.dom.minidom.Element
        :param element_name: name of the element
        :type element_name: basestring
        :return: None
        """
        if self.store_raw is not None:
            save_to_file = self.store_raw
        elif self.store_raw_session is not None:
            save_to_file = self.store_raw_session
        else:
            try:
                save_to_file = ask_confirmation(
                    'Do you want to store sensitive data in config file in plain text?',
                    default='n')
            except KeyboardInterrupt:
                save_to_file = False
            try:
                self.store_raw = ask_confirmation('Set this as default behaviour?', default='y')
            except KeyboardInterrupt:
                self.store_raw_session = save_to_file
        if save_to_file:
            value_element = document.createElement(element_name)
            value_element.appendChild(document.createTextNode(value))
            parent.appendChild(value_element)
        else:
            sys.stderr.write('"%s" has not been saved to config file\n' % element_name)

    def _store_value_securely(self, service_name, username, secret_value):
        """
        Save value in security vault.

        :param service_name: key for storage
        :type service_name: basestring
        :param username: user alias
        :type username: basestring
        :param secret_value: value to be stored
        :type secret_value: basestring
        :return: None
        :raises Exception if not able to store value
        """
        try:
            import keyring
            keyring.set_password(service_name, username, secret_value)
        except Exception as e:
            if not self.store_raw:
                sys.stderr.write('Cannot store in secure storage: %s\n' % e)
            raise e

config = Config()
config.load()
