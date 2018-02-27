#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from genestack_client import (FilesUtil, get_connection, make_connection_parser, get_user,
                              ExpressionNavigatorforGenes, ExpressionNavigatorforIsoforms,
                              ExpressionNavigatorforMicroarrays, AffymetrixMicroarraysNormalizationApplication,
                              SpecialFolders, GenomeQuery)

# Tests must be run on internal-dev
RNA_SEQ_GROUPS = [['GSF1431884', 'GSF1431882', 'GSF1431885'], ['GSF1431881', 'GSF1431887'],
                  ['GSF1431886', 'GSF1431883']]
ISOFORM_GROUPS = [['GSF1431850', 'GSF1431861', 'GSF1431860'], ['GSF1431852', 'GSF1431854']]
MICROARRAY_GROUPS = [['GSF10777989', 'GSF10776354'], ['GSF10776502', 'GSF10777824'], ['GSF10776014', 'GSF10774867'],
                     ['GSF10777773', 'GSF10776962']]
RAT_AFFY_ANNOTATION = "GSF14640591"
EN_TUTORIAL_FILE = 'GSF1433129'

@pytest.fixture(scope='module')
def args():
    p = make_connection_parser()
    p.add_argument('--keep', action='store_true', help='Keep created test files for manual inspection or initialization')
    return p.parse_args()


@pytest.fixture(scope='module')
def keep_files(args):
    return args.keep


@pytest.fixture(scope='module')
def conn(args):
    if get_user(args).host != "internal-dev.genestack.com":
        sys.stderr.write("Tests must be run on internal-dev")
        sys.exit(1)
    connection = get_connection(args)
    return connection


def test_en_rna_seq(conn, keep_files):
    fu = FilesUtil(conn)
    en = ExpressionNavigatorforGenes(conn)
    en_file = None
    try:
        groups = [{'accessions': accs} for accs in RNA_SEQ_GROUPS]
        en_file = en.create_file(groups, r_package=en.PKG_DESEQ, organism="new organism")
    finally:
        if (not keep_files) and (en_file is not None):
            fu.unlink_file(en_file, fu.get_special_folder(SpecialFolders.CREATED))


def test_en_isoforms(conn, keep_files):
    fu = FilesUtil(conn)
    en = ExpressionNavigatorforIsoforms(conn)
    en_file = None
    try:
        groups = [{'accessions': accs} for accs in ISOFORM_GROUPS]
        en_file = en.create_file(groups, multi_mapping_corr=True)
    finally:
        if (not keep_files) and (en_file is not None):
            fu.unlink_file(en_file, fu.get_special_folder(SpecialFolders.CREATED))


def test_en_microarrays(conn, keep_files):
    fu = FilesUtil(conn)
    en = ExpressionNavigatorforMicroarrays(conn)
    norm_app = AffymetrixMicroarraysNormalizationApplication(conn)
    en_file = None
    norm_file = None
    try:
        groups = [{'accessions': accs} for accs in MICROARRAY_GROUPS]
        groups[0]['is_control'] = True
        norm_file = norm_app.create_file([f for group in MICROARRAY_GROUPS for f in group])
        en_file = en.create_file(groups, norm_file, RAT_AFFY_ANNOTATION)
    finally:
        if not keep_files:
            created = fu.get_special_folder(SpecialFolders.CREATED)
            for f in (norm_file, en_file):
                if f is not None:
                    fu.unlink_file(f, created)


def test_get_en_stats(conn):
    en = ExpressionNavigatorforGenes(conn)
    query = GenomeQuery().set_order_ascending(True).set_limit(15).set_offset(0)
    query.set_sorting_order(GenomeQuery.SortingOrder.BY_FDR).set_contrasts(["r1", "r2"])
    query.add_filter(GenomeQuery.Filter.MAX_FDR, 0.2)
    query.add_filter(GenomeQuery.Filter.MIN_LOG_FOLD_CHANGE, 0.1)
    query.add_filter(GenomeQuery.Filter.REGULATION, GenomeQuery.Regulation.UP)

    result = en.get_differential_expression_stats({EN_TUTORIAL_FILE: query})
    entries = result.values()[0]
    assert len(entries) == 30  # limit of 15 * 2 contrasts in file
    assert entries[0]['genomeFeature']['featureName'] == u'ENSG00000175745'

if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'long', __file__])
