#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#
from uuid import uuid4

import pytest

from genestack import (FilesUtil, GenestackException, GenestackServerException, get_connection,
                       make_connection_parser, SpecialFolders, PRIVATE, PUBLIC)

@pytest.fixture(scope='module')
def files_utils():
    connection = get_connection(make_connection_parser().parse_args([]))
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
        files_utils.get_folder(PRIVATE)


def test_get_path_with_wrong_parent(files_utils):
    with pytest.raises(GenestackException):
        files_utils.get_folder('fake folder')


def test_get_path_with_uppercase_parent(files_utils):
    with pytest.raises(GenestackException):
        files_utils.get_folder(PUBLIC, 'Reference genome')


def test_get_path_private_created(files_utils):
    name = '_test_%s' % uuid4()
    f1 = files_utils.get_folder(PRIVATE, name, create=True)
    assert f1, 'file not found in private folder'
    f2 = files_utils.get_folder(PRIVATE, name)
    assert f1 == f2, "Search by None and by 'private' does not much"


def test_get_path_private(files_utils):
    name = 'Reference genome'
    f1 = files_utils.get_folder(PUBLIC, name)
    assert f1, 'file not found in private folder'
    f2 = files_utils.get_folder(PUBLIC, name)
    assert f1 == f2, "Search by None and by 'private' does not much"


def test_get_path_find_long_paths(files_utils):
    assert files_utils.get_folder(PRIVATE, 'Test data created', 'Dependent tasks', 'Multiple dependency')


def test_get_path_public(files_utils):
    assert files_utils.get_folder(PUBLIC, 'Genome annotation')


def test_get_path_public(files_utils):
    with pytest.raises(GenestackException):
        files_utils.get_folder(PUBLIC, 'GENOME ANNOTATION')


def test_get_path_create_paths(files_utils):
    f1 = files_utils.get_folder(PRIVATE, '_test_file_creating', 'subfolder level 1', 'subfolder level 2')
    assert f1
    f2 = files_utils.get_folder(PRIVATE, '_test_file_creating', 'subfolder level 1', 'subfolder level 2')
    assert f1 == f2


if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'long', __file__])
