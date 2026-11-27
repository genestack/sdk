#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from odm_sdk import FilesUtil, GenestackException


class DictionarySearch(object):
    """
    Class for finding dictionaries used in templates.
    """

    def __init__(self, connection):
        self._files_util = FilesUtil(connection)

    def find_dictionary(self, path, name):
        """
        Finds a dictionary by its name. Without a path, it finds the dictionary that is not obsolete
        through the search, because ODM does not link dictionaries into a folder.
        With a path, it finds the dictionary in that folder.

        :return: accession of the dictionary or ``None``
        :raises GenestackException: if more than one dictionary that is not obsolete has the name
        """
        if not path:
            accessions = self._files_util.find_dictionaries_by_name(name)
            if len(accessions) > 1:
                raise GenestackException(
                    "More than one dictionary has the name '%s': %s. Mark the wrong ones obsolete"
                    % (name, ', '.join(accessions)))
            return accessions[0] if accessions else None
        parent = self._find_dictionary_directory(path)
        return self._files_util.find_file_by_name(name, parent=parent)

    def _find_dictionary_directory(self, path):
        head, tail = self._split_path(path)
        return self._files_util.get_folder(head, *tail)

    def _split_path(self, path):
        # search in the home folder if not specified otherwise
        split = path.split('/')
        home_folder = self._files_util.get_home_folder()
        if split[0] in (self._files_util.get_public_folder(), home_folder):
            return split[0], split[1:]
        return home_folder, split
