#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

import pytest

from genestack import FilesUtil, GenestackException, GenestackServerException
from genestack.FilesUtil import CREATED, IMPORTED, TEMPORARY, UPLOADED
from genestack import Connection
import environment


@pytest.fixture(scope='module')
def files_utils():
    connection = Connection(environment.server_url)
    connection.login(environment.userTester, environment.pwdTester)
    files_utils = FilesUtil(connection)
    return files_utils


def test_get_special_folder_created(files_utils):
    assert isinstance(files_utils, FilesUtil)
    text = files_utils.get_special_folder(CREATED)
    assert text == files_utils.get_special_folder(CREATED)


def test_get_special_folder_imported(files_utils):
    assert isinstance(files_utils, FilesUtil)
    text = files_utils.get_special_folder(IMPORTED)
    assert text == files_utils.get_special_folder(IMPORTED)


def test_get_special_folder_temporary(files_utils):
    assert isinstance(files_utils, FilesUtil)
    text = files_utils.get_special_folder(TEMPORARY)
    assert text == files_utils.get_special_folder(TEMPORARY)


def test_get_special_folder_uploaded(files_utils):
    assert isinstance(files_utils, FilesUtil)
    text = files_utils.get_special_folder(UPLOADED)
    assert text == files_utils.get_special_folder(UPLOADED)


def test_get_special_folder_with_wrong_name(files_utils):
    with pytest.raises(GenestackException):
        files_utils.get_special_folder("fake special folder")


def test_get_reference_genome(files_utils):
    with pytest.raises(GenestackServerException):
        files_utils.find_reference_genome('fake organism', 'fake assembly', 'fake release')


if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'short', __file__])
