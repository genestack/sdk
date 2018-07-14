#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import datetime
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from genestack_client.metainfo_scalar_values import *
from genestack_client import (get_connection, make_connection_parser, DataImporter, Metainfo, FilesUtil,
                              SpecialFolders, BioMetaKeys)


TEST_URL = "https://www.ebi.ac.uk/arrayexpress/files/E-MTAB-4265/E-MTAB-4265.raw.1.zip/SKMM1_nonorm_NT_A.txt"

@pytest.fixture(scope='module')
def conn():
    conn = get_connection(make_connection_parser().parse_args())
    return conn


def _strptime_local(date, fmt_str):
    '''
    Helper function to wrap `strptime` returning local (TZ-aware) datetime
    '''
    tzless_dt = datetime.datetime.strptime(date, fmt_str)
    ts_now = time.time()
    tz_offset = (datetime.datetime.fromtimestamp(ts_now)
                 - datetime.datetime.utcfromtimestamp(ts_now))
    return tzless_dt + tz_offset

def test_metainfo_io(conn):
    data_importer = DataImporter(conn)
    fu = FilesUtil(conn)

    created = fu.get_special_folder(SpecialFolders.CREATED)
    info = Metainfo()
    info.add_boolean("a", True)
    info.add_file_reference("b", created)
    info.add_date_time("c", "2015-12-13")
    info.add_integer("d", 239)
    info.add_decimal("e", 238.583)
    info.add_decimal("e", -13.4)
    info.add_string("f", "hello")
    info.add_memory_size("g", 2847633)
    info.add_person("i", "Rosalind Franklin", "+1-202-555-0123", "rosalind@cam.ac.uk")
    info.add_publication("j", "My Publication", "Myself", "Journal of Me", "23/12/2014", pages="12-23")
    info.add_value(Metainfo.NAME, StringValue("Test report file"))
    report_file = None
    try:
        report_file = data_importer.create_report_file(metainfo=info, urls=[TEST_URL], parent=created)
        metainfo = next(iter(fu.collect_metainfos([report_file])))
        assert metainfo.get('a')[0].get_boolean()
        assert isinstance(metainfo.get('b')[0].get_accession(), str)
        assert metainfo.get('c')[0].get_date() == _strptime_local('2015-12-13', '%Y-%m-%d')
        assert metainfo.get('d')[0].get_int() == 239
        assert metainfo.get('e')[0].get_decimal() == 238.583
        assert metainfo.get('e')[1].get_decimal() == -13.4
        assert metainfo.get('f')[0].get_string() == "hello"
        assert metainfo.get('g')[0].get_int() == 2847633
        assert metainfo.get('i')[0].get_person() == {'name': 'Rosalind Franklin', 'phone': '+1-202-555-0123',
                                                     'email': 'rosalind@cam.ac.uk'}
        assert metainfo.get('j')[0].get_publication() == {'title': 'My Publication', 'authors': 'Myself',
                                                          'journalName': 'Journal of Me', 'issueDate': '23/12/2014',
                                                          'pages': '12-23', 'issueNumber': None, 'identifiers': {}}
        assert metainfo.get(Metainfo.NAME)[0].get_string() == "Test report file"
        assert metainfo.get(BioMetaKeys.DATA_LINK)[0].get_url() == TEST_URL
    finally:
        if report_file is not None:
            fu.unlink_file(report_file, created)


if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'long', __file__])
