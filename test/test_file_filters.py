#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from genestack_client.file_filters import *
from genestack_client import BioFileType, Metainfo, FilesUtil, get_connection

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

c = get_connection()
fu = FilesUtil(c)
print fu.find_files(test_filter)['total']