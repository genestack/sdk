#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from genestack_client.file_filters import *
from genestack_client.metainfo_scalar_values import *
from genestack_client import BioFileType, Metainfo, FilesUtil, get_connection, make_connection_parser, SortOrder

SOME_KEY = "someKey"
PUBLIC_FOLDER = "public"
PUBLIC_USER = "public@genestack.com"

@pytest.fixture(scope='module')
def files_utils():
    connection = get_connection(make_connection_parser().parse_args())
    files_utils = FilesUtil(connection)
    return files_utils


def test_find_files(files_utils):
    test_filter = OrFileFilter(
        OwnerFileFilter(PUBLIC_USER),
        AndFileFilter(TypeFileFilter(BioFileType.EXPERIMENT), FixedValueFileFilter(True)),
        MetainfoValuePatternFileFilter(Metainfo.ACCESSION, "GSF"),
        ChildrenFileFilter(PUBLIC_FOLDER),
        ContainsFileFilter(PUBLIC_FOLDER),
        ActualOwnerFileFilter(),
        ActualPermissionFileFilter(GenestackPermission.FILE_ACCESS),
        HasInProvenanceFileFilter("public"),
        PermissionFileFilter("world", GenestackPermission.FILE_ACCESS),
        KeyValueFileFilter(Metainfo.NAME, "Test")
    )

    result = files_utils.find_files(test_filter, SortOrder.BY_LAST_UPDATE, True, 4, 80)
    assert result['total'] > 0


def test_find_files_with_metainfo_scalar_values(files_utils):
    values = (BooleanValue(True), FileReference("GSF12345"), DateTimeValue("2015-12-13"),
              IntegerValue(239), DecimalValue(238.486), StringValue("hello"), MemorySizeValue(25738),
              ExternalLink("https://www.ebi.ac.uk/arrayexpress/files/E-MTAB-4265/E-MTAB-4265.raw.1.zip"
                           "/SKMM1_nonorm_NT_A.txt"),
              Person('Rosalind Franklin', "+1-202-555-0123", "rosalind@cam.ac.uk"),
              Publication('My Publication', 'Myself', 'Journal of Me', '23/12/2014', pages="12-23")
    )

    filters = [KeyValueFileFilter(SOME_KEY, v) for v in values]
    test_filter = OrFileFilter(*filters)
    result = files_utils.find_files(test_filter, SortOrder.DEFAULT)
    assert result is not None

if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'long', __file__])
