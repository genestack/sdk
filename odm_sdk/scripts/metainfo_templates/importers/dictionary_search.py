#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from odm_sdk import FilesUtil


class DictionarySearch(object):
    """
    Class for finding dictionaries used in templates.
    """

    def __init__(self, connection):
        self._files_util = FilesUtil(connection)

    def find_dictionary(self, path, name):
        parent = self._find_dictionary_directory(path)
        return self._files_util.find_file_by_name(name, parent=parent)

    def _find_dictionary_directory(self, path):
        head, tail = self._split_path(path)
        return self._files_util.get_folder(head, *tail)

    def _split_path(self, path):
        # search in public dictionaries as default
        if not path:
            return self._files_util.get_public_folder(), ['Dictionaries']
        # search in the home folder if not specified otherwise
        else:
            split = path.split('/')
            home_folder = self._files_util.get_home_folder()
            if split[0] in (self._files_util.get_public_folder(), home_folder):
                return split[0], split[1:]
            else:
                return home_folder, split
