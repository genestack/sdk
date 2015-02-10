#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

import os
import platform
from genestack import GenestackException
from xml.dom.minidom import getDOMImplementation, parse
from User import User
from copy import deepcopy


GENESTACK_SDK = "Genestack SDK"
SETTING_FILE_NAME = 'genestack.xml'
SETTINGS_FOLDER = '.genestack'


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
            path = os.path.join(str(buf.value), SETTINGS_FOLDER)
        else:
            path = os.path.join(os.path.expanduser('~/'), SETTINGS_FOLDER)
        return path

    def get_settings_file(self):
        return os.path.join(self.get_settings_folder(), SETTING_FILE_NAME)

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
            keyring.delete_password(GENESTACK_SDK, user.alias)
        except ImportError:
            pass
        except Exception as e:
            print "Error while deleting user password for %s: %s" % (user.alias, e)

    def add_user(self, user):
        if not user.alias:
            raise GenestackException("Cant add user without alias to config.")
        if user.alias in self.__users:
            raise GenestackException("User alias %s is already present" % user.alias)
        self.__users[user.alias] = user
        if len(self.__users) == 1:
            self.set_default_user(user)  # will save it inside
        else:
            self.save()

    def set_default_user(self, user):
        if not user.alias in self.__users:
            raise GenestackException('User %s is not present in config users.' % user.alias)
        if not self.default_user or user.alias != self.default_user.alias:
            self.__default_user = user
        self.save()

    def load(self):
        config_path = self.get_settings_file()

        if not os.path.exists(config_path):
            print 'Warning. config is not present. You can setup it via: genestack-user-setup.py init'
            return  # check that this return handled everywhere

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
                if not password:
                    try:
                        import keyring
                        password = keyring.get_password(GENESTACK_SDK, alias)
                    except (ImportError, Exception) as e:
                        print e
                self.add_user(User(email, alias=alias, host=host, password=password))

        default_user_alias = get_text(dom, 'default_user')
        store_raw_text = get_text(dom, 'store_raw')
        if store_raw_text == 'True':
            self.store_raw = True
        elif store_raw_text == 'False':
            self.store_raw = False
        try:
            self.__default_user = self.__users[default_user_alias]
        except KeyError:
            print "Cannot set default user. User %s is not present in config users." % default_user_alias

    def change_password(self, alias, password):
        user = self.__users[alias]
        user.password = password
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
                    import keyring
                    keyring.set_password("%s" % GENESTACK_SDK, user.alias, user.password)
                except (ImportError, Exception) as e:

                    if self.store_raw is not None:
                        save_to_file = self.store_raw
                    elif self.store_raw_session is not None:
                        save_to_file = self.store_raw_session
                    else:
                        print 'Exception at storing password at secure storage: %s' % e
                        try:
                            response = raw_input("Do you want to store password in config file as plain text? [y/N]").lstrip().lower()
                        except KeyboardInterrupt:
                            response = 'n'
                        save_to_file = response in ['y', 'yes']

                        try:
                            store_response = raw_input("Set this as default behaviour? [Y/n]").lstrip().lower()
                            if store_response in ['y', 'yes']:
                                self.store_raw = save_to_file
                        except KeyboardInterrupt:
                            self.store_raw_session = save_to_file

                    if save_to_file:
                        password_element = document.createElement('password')
                        password_element.appendChild(document.createTextNode(user.password))
                        user_element.appendChild(password_element)

        if self.default_user:
            default_user_element = document.createElement('default_user')
            top.appendChild(default_user_element)
            default_user_element.appendChild(document.createTextNode(self.default_user.alias))
        if self.store_raw is not None:
            store_raw_element = document.createElement('store_raw')
            top.appendChild(store_raw_element)
            store_raw_element.appendChild(document.createTextNode(str(self.store_raw)))
        with open(config_path, 'w') as f:
            document.writexml(f, indent='', addindent='\t', newl='\n')

config = Config()
config.load()
