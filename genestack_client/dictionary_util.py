from genestack_client import Application, FilesUtil, SpecialFolders, GenestackException


class DictionaryUtil(Application):
    APPLICATION_ID = 'genestack/bio-dictionary-util'

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
        Entries exceeding this limit will be skipped (and a warning will be issued)
        If two entries have the same characters with a different case (e.g. 'Homo sapiens' and 'HOMO SAPIENS')
        the latest entry will overwrite the previous one.

        :param dictionary_file: accession of the dictionary file
        :type dictionary_file: str
        :param entries_list: list of entries
        :param entries_list: list[str]
        :return: None
        """
        invalid_entries = [entry for entry in entries_list if len(entry) >= 255]
        if invalid_entries:
            print "Warning: the following entries will be skipped as they are over 255 characters: %s" \
                  % (", ".join(invalid_entries))
            entries_list = [entry for entry in entries_list if len(entry) < 255]
        self.invoke('addToDictionary', dictionary_file, entries_list)
