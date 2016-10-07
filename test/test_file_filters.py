#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from genestack_client.file_filters import *
from genestack_client import BioFileType, Metainfo, FilesUtil, get_connection, make_connection_parser, SortOrder


@pytest.fixture(scope='module')
def files_utils():
    connection = get_connection(make_connection_parser().parse_args())
    files_utils = FilesUtil(connection)
    return files_utils


def test_find_files(files_utils):
    test_filter = OrFileFilter(
        OwnerFileFilter("public@genestack.com"),
        KeyValueFileFilter(Metainfo.NAME, "Test"),
        AndFileFilter(TypeFileFilter(BioFileType.EXPERIMENT), FixedValueFileFilter(True)),
        MetainfoValuePatternFileFilter(Metainfo.ACCESSION, "GSF"),
        ChildrenFileFilter("public"),
        ContainsFileFilter("public"),
        ActualOwnerFileFilter(),
        ActualPermissionFileFilter(GenestackPermission.FILE_ACCESS),
        HasInProvenanceFileFilter("public"),
        PermissionFileFilter("world", GenestackPermission.FILE_ACCESS)
    )

    result = files_utils.find_files(test_filter, SortOrder.BY_LAST_UPDATE, True, 4, 80)
    assert result['total'] > 0


if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'long', __file__])
