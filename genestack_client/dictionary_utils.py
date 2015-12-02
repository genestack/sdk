from genestack_client import Application, FilesUtil, SpecialFolders


class DictionaryUtils(Application):
    APPLICATION_ID = 'genestack/bio-dictionary-util'

    def create(self, name, parent=None):
        """
        Create dictionary file in specified folder.

        :param name: name of dictionary file
        :type name: str
        :param parent: parent accession, default Created folder
        :type parent: str
        :return: accession if dictionary
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
        Add entries to dictionary file.

        Entry in lower case should be unique in dictionary.
        If you add both 'Homo Sapiens' and 'homo sapiens' only last entry will be stored in dictionary.

        :param dictionary_file: accession if dictionary
        :type dictionary_file: str
        :param entries_list: list of entries
        :param entries_list: list[str]
        :return: None
        """
        self.invoke('addToDictionary', dictionary_file, entries_list)
