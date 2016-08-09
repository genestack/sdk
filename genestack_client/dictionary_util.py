# -*- coding: utf-8 -*-
import sys

from genestack_client import Application, FilesUtil, SpecialFolders, GenestackException


class DictionaryUtil(Application):
    APPLICATION_ID = 'genestack/bio-dictionary-util'

    def __init__(self, connection, application_id=None):
        sys.stderr.write(
            'Usage of this class is deprecated, '
            'old syle dictionaries should not be created anymore '
            'use DataImporter.create_dictionary to create dictionary files.\n'
                         )
        Application.__init__(self, connection, application_id)

    def create(self, name, parent=None):
        """
        Create a dictionary file in specified folder.

        :param name: name of the dictionary file
        :type name: str
        :param parent: parent accession (if not specified, the dictionary will be put in the `Created Files` folder)
        :type parent: str
        :return: accession of the dictionary file
        :rtype: str
        """
        accession = self.invoke('createDictionary', name)
        if parent:
            fu = FilesUtil(self.connection)
            fu.link_file(accession, parent)
            fu.unlink_file(accession, fu.get_special_folder(SpecialFolders.CREATED))
        return accession

    def add_entries(self, dictionary_file, entries_list):
        """
        Add entries to a dictionary file.

        Currently, entries cannot be longer than 255 characters.
        If an entry exceeds this limit, a `GenestackException` will be raised.
        If two entries have the same characters with a different case (e.g. 'Homo sapiens' and 'HOMO SAPIENS')
        the latest entry will overwrite the previous one.

        :param dictionary_file: accession of the dictionary file
        :type dictionary_file: str
        :param entries_list: list of entries
        :param entries_list: list[str]
        :return: None
        """
        if any(len(entry) > 255 for entry in entries_list):
            raise GenestackException("Dictionary entries cannot be longer than 255 characters")

        self.invoke('addToDictionary', dictionary_file, entries_list)

    def remove_entries(self, dictionary_file, entries_list):
        """
        Remove entries from a dictionary file.

        :param dictionary_file: accession of the dictionary file
        :type dictionary_file: str
        :param entries_list: list of entries
        :param entries_list: list[str]
        :return: None
        """
        self.invoke('removeFromDictionary', dictionary_file, entries_list)

    def clear(self, dictionary_file):
        """
        Remove all entries from a dictionary file.

        :param dictionary_file: accession of the dictionary file
        :type dictionary_file: str
        :return: None
        """
        self.invoke('clear', dictionary_file)
