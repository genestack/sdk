#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os
import time
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
    pytest.skip("Outdated test")
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


@pytest.yield_fixture
def samples_temp_folder(files_utils):
    temp_folder = files_utils.get_special_folder(SpecialFolders.TEMPORARY)

    folder_name = 'Sample_study_folder_%s' % uuid4()
    folder = files_utils.create_folder(folder_name, parent=temp_folder)
    file_info = files_utils.create_sample(name='Sample 1', parent=folder)
    accession = file_info['accession']

    yield folder

    files_utils.unlink_file(accession, folder)
    files_utils.unlink_file(folder, temp_folder)


def test_create_samples_studies(files_utils, samples_temp_folder):
    folder = samples_temp_folder

    # wait for newly created file to be available in Solr
    time.sleep(1)

    samples_in_folder = files_utils.find_samples(parent=folder)

    samples_by_name = files_utils.find_samples(name='Sample 1', parent=folder)

    metainfo = Metainfo()
    metainfo.add_string(Metainfo.NAME, 'Sample 1')
    samples_by_metainfo = files_utils.find_samples(metainfo=metainfo, parent=folder)

    accession = samples_by_metainfo['result'][0]['accession']
    retrieved_metainfo = files_utils.get_metainfo(accession)

    found_studies = files_utils.find_studies(parent=folder)

    assert samples_in_folder['total'] == 1
    assert len(samples_in_folder['result']) == 1
    assert samples_by_name['total'] == 1
    assert len(samples_by_name['result']) == 1
    assert samples_by_metainfo['total'] == 1
    assert len(samples_by_metainfo['result']) == 1
    assert found_studies['total'] == 0
    assert len(found_studies['result']) == 0
    assert Metainfo.NAME in retrieved_metainfo


@pytest.yield_fixture
def metainfo_temp_file(files_utils):
    temp_folder = files_utils.get_special_folder(SpecialFolders.TEMPORARY)
    file_name = 'File for metainfo tests %s' % uuid4()
    file_info = files_utils.create_study(name=file_name, parent=temp_folder)
    accession = file_info['accession']
    yield (accession, file_name)
    files_utils.unlink_file(accession, temp_folder)


def test_metainfo_modification(files_utils, metainfo_temp_file):
    (accession, file_name) = metainfo_temp_file

    metainfo = files_utils.get_metainfo(accession)
    assert metainfo[Metainfo.NAME][0]['value'] == file_name

    metainfo_to_add = Metainfo()
    key = 'test_key'
    value = 'test_value'
    metainfo_to_add.add_string(key, value)
    files_utils.add_metainfo(accession, metainfo_to_add)

    metainfo = files_utils.get_metainfo(accession)
    assert metainfo[key][0]['value'] == value

    metainfo_to_replace = Metainfo()
    replaced_value = 'replaced_value'
    metainfo_to_replace.add_string(key, replaced_value)
    files_utils.replace_metainfo(accession, metainfo_to_replace)

    metainfo = files_utils.get_metainfo(accession)
    assert metainfo[key][0]['value'] == replaced_value

    files_utils.remove_metainfo_key(accession, key)
    files_utils.remove_metainfo_keys(accession, [key])

    metainfo = files_utils.get_metainfo(accession)
    assert key not in metainfo


if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'long', __file__])
