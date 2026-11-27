import unittest
from unittest import mock

from odm_sdk import FilesUtil, GenestackException
from odm_sdk.scripts.metainfo_templates.importers.dictionary_search import DictionarySearch


def search_response(*accessions):
    return {'count': len(accessions), 'files': [{'accessions': [a]} for a in accessions]}


class DictionarySearchTest(unittest.TestCase):

    def setUp(self):
        self.search = DictionarySearch(mock.Mock())

    def test_finds_the_dictionary_by_name_without_a_folder(self):
        with mock.patch.object(FilesUtil, 'search_files', return_value=search_response('GSF1')) as m:
            self.assertEqual('GSF1', self.search.find_dictionary(None, 'Sex'))
        m.assert_called_once_with(
            search_string='Sex',
            parameters={'type': FilesUtil.DICTIONARY_FILE, 'name': 'Sex', 'obsolete': 'false'})

    def test_an_unknown_name_gives_none(self):
        with mock.patch.object(FilesUtil, 'search_files', return_value=search_response()):
            self.assertIsNone(self.search.find_dictionary(None, 'Sex'))

    def test_more_than_one_dictionary_with_the_name_is_an_error(self):
        with mock.patch.object(FilesUtil, 'search_files', return_value=search_response('GSF1', 'GSF2')):
            with self.assertRaises(GenestackException) as cm:
                self.search.find_dictionary(None, 'Sex')
        self.assertIn('GSF1, GSF2', str(cm.exception))

    def test_a_path_finds_the_dictionary_in_the_folder(self):
        with mock.patch.object(FilesUtil, 'get_home_folder', return_value='private'), \
                mock.patch.object(FilesUtil, 'get_folder', return_value='GSF9') as get_folder, \
                mock.patch.object(FilesUtil, 'find_file_by_name', return_value='GSF1') as find, \
                mock.patch.object(FilesUtil, 'search_files') as search_files:
            self.assertEqual('GSF1', self.search.find_dictionary('public/Dictionaries', 'Sex'))
        get_folder.assert_called_once_with('public', 'Dictionaries')
        find.assert_called_once_with('Sex', parent='GSF9')
        search_files.assert_not_called()
