#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2016 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

import os
import sys
from uuid import uuid4
import pytest


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from genestack_client import (FilesUtil, GenestackException, GenestackServerException, get_connection,
                       make_connection_parser, SpecialFolders, Metainfo)

@pytest.fixture(scope='module')
def files_utils():
    connection = get_connection(make_connection_parser().parse_args())
    files_utils = FilesUtil(connection)
    return files_utils


def test_get_special_folder_created(files_utils):
    assert isinstance(files_utils, FilesUtil)
    text = files_utils.get_special_folder(SpecialFolders.CREATED)
    assert text == files_utils.get_special_folder(SpecialFolders.CREATED)


def test_get_special_folder_imported(files_utils):
    assert isinstance(files_utils, FilesUtil)
    text = files_utils.get_special_folder(SpecialFolders.IMPORTED)
    assert text == files_utils.get_special_folder(SpecialFolders.IMPORTED)


def test_get_special_folder_temporary(files_utils):
    assert isinstance(files_utils, FilesUtil)
    text = files_utils.get_special_folder(SpecialFolders.TEMPORARY)
    assert text == files_utils.get_special_folder(SpecialFolders.TEMPORARY)


def test_get_special_folder_uploaded(files_utils):
    assert isinstance(files_utils, FilesUtil)
    text = files_utils.get_special_folder(SpecialFolders.UPLOADED)
    assert text == files_utils.get_special_folder(SpecialFolders.UPLOADED)


def test_get_special_folder_with_wrong_name(files_utils):
    with pytest.raises(GenestackException):
        files_utils.get_special_folder("fake special folder")


def test_get_reference_genome(files_utils):
    with pytest.raises(GenestackServerException):
        files_utils.find_reference_genome('fake organism', 'fake assembly', 'fake release')


# get path
def test_get_path_with_empty_paths(files_utils):
    with pytest.raises(GenestackException):
        files_utils.get_folder(files_utils.get_home_folder())


def test_get_path_with_wrong_parent(files_utils):
    with pytest.raises(GenestackException):
        files_utils.get_folder('fake folder')


def test_get_path_private_created(files_utils):
    name = '_test_%s' % uuid4()
    f1 = files_utils.get_folder(files_utils.get_home_folder(), name, create=True)
    assert f1, 'file not found in private folder'
    f2 = files_utils.get_folder(files_utils.get_home_folder(), name)
    assert f1 == f2, "Search by None and by 'private' does not much"


def test_get_path_private(files_utils):
    name = 'Reference genome'
    f1 = files_utils.get_folder(files_utils.get_public_folder(), name)
    assert f1, 'file not found in private folder'
    f2 = files_utils.get_folder(files_utils.get_public_folder(), name)
    assert f1 == f2, "Search by None and by 'private' does not much"


def test_get_path_find_long_paths(files_utils):
    assert files_utils.get_folder(files_utils.get_home_folder(), 'Test data created', 'Dependent tasks', 'Multiple dependency', create=False)


def test_get_path_public(files_utils):
    assert files_utils.find_file_by_name('Genome annotation', file_class=files_utils.FOLDER, parent=files_utils.get_public_folder())


def test_get_path_public_upper_case(files_utils):
    assert files_utils.find_file_by_name('GENOME ANNOTATION', parent=files_utils.get_public_folder(), file_class=files_utils.FOLDER)


def test_get_path_create_paths(files_utils):
    f1 = files_utils.get_folder(files_utils.get_home_folder(), '_test_file_creating', 'subfolder level 1', 'subfolder level 2', create=True)
    assert f1
    f2 = files_utils.get_folder(files_utils.get_home_folder(), '_test_file_creating', 'subfolder level 1', 'subfolder level 2')
    assert f1 == f2


def test_get_complete_infos(files_utils):
    specila_folder = files_utils.get_special_folder(SpecialFolders.CREATED)
    infos = files_utils.get_complete_infos([specila_folder])
    assert len(infos) == 1
    info = infos[0]
    assert info['name'] == 'Created files'
    assert info['accession'] == specila_folder
    assert info['application'] == {'id': None}
    assert info['kind'] == 'Folder'
    assert info['owner'] == 'Tester'
    assert info['typeKey'] == 'folder'
    assert info['permissionsByGroup'] == {'displayStrings': {'GSG000001': ''},
                                          'groupNames': {'GSG000001': 'WORLD'},
                                          'ids': {'GSG000001': []}}
    assert set(info['time']) == {'fileCreation', 'lastMetainfoModification'}
    assert info['initializationStatus'] == {
        'displayString': 'Complete',
        'id': 'NOT_APPLICABLE',
        'isError': False,
        'description': 'Not applicable'
    }
    assert set(info) == {'name', 'accession', 'application', 'kind',
                         'owner', 'typeKey', 'permissionsByGroup', 'time', 'initializationStatus'}


def test_get_infos(files_utils):
    specila_folder = files_utils.get_special_folder(SpecialFolders.CREATED)
    infos = files_utils.get_infos([specila_folder])
    assert len(infos) == 1
    info = infos[0]
    assert info['name'] == 'Created files'
    assert info['accession'] == specila_folder
    assert info['application'] == {'id': None}
    assert info['owner'] == 'Tester'
    assert info['permissionsByGroup'] == {'groupNames': {'GSG000001': 'WORLD'},
                                          'ids': {'GSG000001': []}}
    assert set(info['time']) == {'fileCreation', 'lastMetainfoModification'}
    assert info['initializationStatus'] == {'id': 'NOT_APPLICABLE', 'isError': False, 'description': 'Not applicable'}
    assert set(info) == {'name', 'accession', 'application',
                         'owner', 'permissionsByGroup', 'time', 'initializationStatus'}


def test_get_metainfo_strings(files_utils):
    special_folder = files_utils.get_special_folder(SpecialFolders.CREATED)
    infos = files_utils.get_metainfo_values_as_strings([special_folder],
                                        [Metainfo.NAME, Metainfo.DESCRIPTION])
    assert set(infos[special_folder].keys()) == {Metainfo.NAME, Metainfo.DESCRIPTION}
    assert infos[special_folder][Metainfo.NAME] == "Created files"
    assert infos[special_folder][Metainfo.DESCRIPTION] == "Files you created with various applications"


if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'long', __file__])
