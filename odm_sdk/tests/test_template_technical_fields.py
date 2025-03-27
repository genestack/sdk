import unittest
from unittest.mock import patch

from odm_sdk import Metainfo
from odm_sdk.scripts.metainfo_templates.importers.template_technical_fields import (
    validate_content, enrich_items, ACCESSION, DATA_CLASS)


class TestTemplateTechnicalFields(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.t_data_type = 'genestack:transcriptomicsParent'
        cls.t_data_class = DATA_CLASS.copy()
        cls.t_data_class['dataType'] = cls.t_data_type

    @patch('sys.stderr.write')
    @patch('sys.exit')
    def test_exit_on_content_with_incomplete_accession(self, mock_sys_exit, mock_stderr_write):
        content = [
            {'name': Metainfo.ACCESSION, 'dataType': self.t_data_type},
            self.t_data_class,
            {
                'dictionaryName': 'Sequencing Platforms',
                'dataType': self.t_data_type,
                'isRequired': False,
                'metainfoType': 'com.genestack.api.metainfo.StringValue',
                'name': 'Experimental Platform',
                'isReadOnly': False
            }
        ]
        validate_content(content)
        mock_stderr_write.assert_called()
        self.assertEqual(mock_stderr_write.call_args_list[0][0][0],
                         'Template field "genestack:accession" of type '
                         '"genestack:transcriptomicsParent" is predefined and cannot be edited.')
        mock_sys_exit.assert_called_once()

    @patch('sys.stdout.write')
    @patch('sys.exit')
    def test_message_on_content_with_redundant_data_class(self, mock_sys_exit, mock_stdout_write):
        content = [
            {'name': 'custom field', 'dataType': self.t_data_type},
            self.t_data_class
        ]
        validate_content(content)
        mock_stdout_write.assert_called()
        self.assertEqual(mock_stdout_write.call_args_list[0][0][0],
                         'Template field "Data Class" of type '
                         '"genestack:transcriptomicsParent" is predefined and can be omitted.')
        mock_sys_exit.assert_not_called()

    @patch('sys.stdout.write')
    @patch('sys.exit')
    def test_message_on_content_with_different_description(self, mock_sys_exit, mock_stdout_write):
        t_accession = ACCESSION.copy()
        t_accession['dataType'] = self.t_data_type
        t_accession['description'] = 'custom old description'
        content = [t_accession]
        validate_content(content)
        mock_stdout_write.assert_called()
        self.assertEqual(mock_stdout_write.call_args_list[0][0][0],
                         'Template field "genestack:accession" of type '
                         '"genestack:transcriptomicsParent" is predefined and can be omitted.')
        mock_sys_exit.assert_not_called()

    @patch('sys.stderr.write')
    @patch('sys.stdout.write')
    def test_validation_passes_on_custom_content(self, mock_stdout_write, mock_stderr_write):
        content = [
            {'name': 'custom field', 'dataType': self.t_data_type},
            {'name': 'another field', 'dataType': self.t_data_type}
        ]
        validate_content(content)
        mock_stdout_write.assert_not_called()
        mock_stderr_write.assert_not_called()

    def test_all_technical_items_are_added_to_content(self):
        content = [
            {'name': 'custom field', 'dataType': self.t_data_type},
            {'name': 'another field', 'dataType': self.t_data_type}
        ]
        enriched_items = enrich_items(self.t_data_type, content)
        self.assertEqual(len(enriched_items), 7)
        self.assertEqual(enriched_items[0]['name'], Metainfo.ACCESSION)
        self.assertEqual(enriched_items[1]['name'], Metainfo.DATA_CLASS)
        self.assertEqual(enriched_items[2]['name'], 'custom field')
        self.assertEqual(enriched_items[3]['name'], 'another field')
        self.assertEqual(enriched_items[4]['name'], Metainfo.FEATURES_STRING)
        self.assertEqual(enriched_items[5]['name'], Metainfo.FEATURES_NUMERIC)
        self.assertEqual(enriched_items[6]['name'], Metainfo.VALUES_NUMERIC)

    def test_technical_items_are_filtered_by_data_type(self):
        data_type = 'genestack:genomicsParent'
        content = [
            {'name': 'custom field', 'dataType': data_type}
        ]
        enriched_items = enrich_items(data_type, content)
        self.assertEqual(len(enriched_items), 3)
        self.assertEqual(enriched_items[0]['name'], Metainfo.ACCESSION)
        self.assertEqual(enriched_items[1]['name'], Metainfo.DATA_CLASS)
        self.assertEqual(enriched_items[2]['name'], 'custom field')

    def test_technical_items_are_description_agnostic(self):
        t_accession = ACCESSION.copy()
        t_accession['dataType'] = self.t_data_type
        t_accession['description'] = 'custom old description'
        content = [t_accession]
        enriched_items = enrich_items(self.t_data_type, content)
        self.assertEqual(len(enriched_items), 5)
        filtered_items = [item for item in enriched_items if item['name'] == Metainfo.ACCESSION]
        self.assertEqual(len(filtered_items), 1)
        self.assertEqual(enriched_items[0]['description'], 'custom old description')

    def test_technical_items_are_not_duplicated(self):
        data_type = 'study'
        content = [
            {'name': 'custom field', 'dataType': data_type}
        ]
        enriched_items = enrich_items(data_type, content)
        self.assertEqual(len(enriched_items), 2)
        self.assertEqual(enriched_items[0]['name'], Metainfo.ACCESSION)
        self.assertEqual(enriched_items[1]['name'], 'custom field')
        secondly_enriched_items = enrich_items(data_type, enriched_items)
        self.assertEqual(secondly_enriched_items, enriched_items)


if __name__ == '__main__':
    unittest.main()
