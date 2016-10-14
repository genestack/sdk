#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from genestack_client import (FilesUtil, get_connection, make_connection_parser, get_user,
                              ExpressionNavigatorforGenes, ExpressionNavigatorforIsoforms,
                              ExpressionNavigatorforMicroarrays, AffymetrixMicroarraysNormalisationApplication,
                              SpecialFolders)

# Tests must be run on internal-dev
RNA_SEQ_GROUPS = [['GSF1431884', 'GSF1431882', 'GSF1431885'], ['GSF1431881', 'GSF1431887'],
                  ['GSF1431886', 'GSF1431883']]
ISOFORM_GROUPS = [['GSF1431850', 'GSF1431861', 'GSF1431860'], ['GSF1431852', 'GSF1431854']]
MICROARRAY_GROUPS = [['GSF10777989', 'GSF10776354'], ['GSF10776502', 'GSF10777824'], ['GSF10776014', 'GSF10774867'],
                     ['GSF10777773', 'GSF10776962']]
RAT_AFFY_ANNOTATION = "GSF14640591"


@pytest.fixture(scope='module')
def conn():
    args = make_connection_parser().parse_args()
    if get_user(args).host != "internal-dev.genestack.com":
        sys.stderr.write("Tests must be run on internal-dev")
        sys.exit(1)
    connection = get_connection()
    return connection


def test_en_rna_seq(conn):
    fu = FilesUtil(conn)
    en = ExpressionNavigatorforGenes(conn)
    en_file = None
    try:
        en_file = en.create_file(RNA_SEQ_GROUPS, r_package=en.PKG_DESEQ, organism="new organism")
    finally:
        if en_file is not None:
            fu.unlink_file(en_file, fu.get_special_folder(SpecialFolders.CREATED))


def test_en_isoforms(conn):
    fu = FilesUtil(conn)
    en = ExpressionNavigatorforIsoforms(conn)
    en_file = None
    try:
        en_file = en.create_file(ISOFORM_GROUPS, multi_mapping_corr=True)
    finally:
        if en_file is not None:
            fu.unlink_file(en_file, fu.get_special_folder(SpecialFolders.CREATED))


def test_en_microarrays(conn):
    fu = FilesUtil(conn)
    en = ExpressionNavigatorforMicroarrays(conn)
    norm_app = AffymetrixMicroarraysNormalisationApplication(conn)
    en_file = None
    norm_file = None
    try:
        norm_file = norm_app.create_file([f for group in MICROARRAY_GROUPS for f in group])
        en_file = en.create_file(norm_file, MICROARRAY_GROUPS, RAT_AFFY_ANNOTATION, control_group=0)
    finally:
        created = fu.get_special_folder(SpecialFolders.CREATED)
        for f in (norm_file, en_file):
            if f is not None:
                fu.unlink_file(f, created)


if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'long', __file__])
