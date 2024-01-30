#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys

from odm_sdk import (Application, FilesUtil, GenestackException,
                              GenestackServerException, SpecialFolders,
                              GroupsUtil, ShareUtil)

from . import json_validation
from .dictionary_search import DictionarySearch
from .format import colored, print_result, Color


# permission name to look for in "not enough permissions" server error
TEMPLATE_PERM_NAME = 'MANAGE_TEMPLATES'


class TemplateImporter(Application):
    """
    Class for uploading templates and dictionaries.
    """

    IMPORT_TEMPLATE_FOLDER_NAME = 'Import Templates'
    APPLICATION_ID = 'genestack/study-metainfotemplateeditor'

    def __init__(self, connection):
        super(TemplateImporter, self).__init__(connection)

        self._files_util = FilesUtil(connection)
        self._share_util = ShareUtil(connection)
        self._dictionary_search = DictionarySearch(connection)
        self._groups_util = GroupsUtil(connection)
        self._import_template_folder = self._get_import_template_folder()

    def invoke(self, method, *params):
        try:
            return super(TemplateImporter, self).invoke(method, *params)
        except GenestackServerException as e:
            if TEMPLATE_PERM_NAME in e.message:
                print("TIP: to create or update metainfo template, user has to "
                      "have 'Set up templates' permission; request it from your "
                      "administrator", file=sys.stderr)
            raise e

    def create_from_config(self, config_path):
        config = json_validation.load_json(config_path, schema_name='config_schema.json')
        self._create_from_config(**config)

    def _create_from_config(
            self, template_path, template_name,
            replace=False, mark_default=False
    ):

        template_accession = self._create_template(template_name, template_path, replace=replace)
        if template_accession is None:
            return

        if mark_default:
            self._mark_as_default(template_accession)
            # it would be nice to display the organization's name but as of 21.08.2020 API
            # method for doing this has been removed
            print('Template "%s" is marked as the Default Template'
                  % template_accession)

    def _create_template(self, name, json_path, replace):
        content = json_validation.load_json(json_path, schema_name='template_schema.json')
        accession = self._find_existing_template(name)

        if accession is None:
            print('No template with name "%s" found, creating a new template' %
                  colored(name, Color.BLUE))
            accession = self.invoke('createTemplateFile', name)

            print_result(accession, name, 'Template')
        elif replace:
            print('Template %s / %s already exists and will be reused' %
                  (colored(accession, Color.GREEN), colored(name, Color.BLUE)))
        else:
            print(
                "Template '%s'(%s) already exists in '%s', use '\"replace\": true' in the config "
                "to update existing or choose other name" %
                (name, accession, self._import_template_folder)
            )
            return None

        self._put_content(accession, content)
        return accession

    def _check_is_template(self, name, accession):
        if not accession:
            return False
        try:
            self.invoke('loadTemplate', accession)
        except GenestackException:
            print(
                'File "%s" (%s) has been found but is not a template' % (name, accession)
            )
            return False
        return True

    def _find_existing_template(self, name):
        def find(parent):
            return self._files_util.find_application_page_file_by_name(name, parent)

        folders_to_search = [self._files_util.get_public_folder(),
                             self._import_template_folder,
                             self._files_util.get_special_folder(SpecialFolders.CREATED)
                             ]
        for folder in folders_to_search:
            accession = find(folder)
            if self._check_is_template(name, accession):
                return accession
        return None

    def _get_import_template_folder(self):
        created_folder = self._files_util.get_special_folder(SpecialFolders.CREATED)
        return self._files_util.get_folder(
            created_folder, 'Data samples', self.IMPORT_TEMPLATE_FOLDER_NAME, create=True
        )

    def _put_content(self, accession, fields):
        def process_field(field):
            new_field = field.copy()
            dictionary_name = new_field.pop('dictionaryName', None)
            dictionary_path = new_field.pop('dictionaryPath', None)
            new_field['dictionaryAccession'] = self._find_dict(dictionary_path, dictionary_name)
            return new_field

        processed_fields = map(process_field, fields)

        types = {}
        for item in processed_fields:
            data_type = item['dataType']
            types.setdefault(data_type, []).append(item)

        for data_type, data_type_items in types.items():
            self.invoke('setKeyInfosForFileKind', accession, data_type, data_type_items)

    def _find_dict(self, path, name):
        if not name:
            return None

        dict_accession = self._dictionary_search.find_dictionary(path, name)
        if not dict_accession:
            raise GenestackException(
                "Can't find dictionary '%s' in '%s'" % (name, path)
            )
        return dict_accession

    def _mark_as_default(self, accession):
        self.invoke('setDefaultTemplate', accession)
