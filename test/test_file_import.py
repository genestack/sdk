#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import os
import pytest


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from genestack_client.metainfo_scalar_values import *
from genestack_client import get_connection, make_connection_parser, DataImporter, Metainfo, FilesUtil, SpecialFolders


TEST_URL = "https://www.ebi.ac.uk/arrayexpress/files/E-MTAB-4265/E-MTAB-4265.raw.1.zip/SKMM1_nonorm_NT_A.txt"

@pytest.fixture(scope='module')
def conn():
    conn = get_connection(make_connection_parser().parse_args())
    return conn


def test_create_report_with_info(conn):
    data_importer = DataImporter(conn)
    fu = FilesUtil(conn)
    values = (BooleanValue(True), FileReference("GSF12345"), DateTimeValue("2015-12-13"),
              IntegerValue(239), DecimalValue(238.486), StringValue("hello"), MemorySizeValue(25738),
              ExternalLink("https://www.ebi.ac.uk/arrayexpress/files/E-MTAB-4265/E-MTAB-4265.raw.1.zip"
                           "/SKMM1_nonorm_NT_A.txt"),
              Person('Rosalind Franklin', "+1-202-555-0123", "rosalind@cam.ac.uk"),
              Publication('My Publication', 'Myself', 'Journal of Me', '23/12/2014', pages="12-23")
    )

    created = fu.get_special_folder(SpecialFolders.CREATED)
    info = Metainfo()
    info.add_boolean("a", True)
    info.add_file_reference("b", created)
    info.add_date_time("c", "2015-12-13")
    info.add_integer("d", 239)
    info.add_decimal("e", 238.583)
    info.add_string("f", "hello")
    info.add_memory_size("g", 2847633)
    info.add_person("i", "Rosalind Franklin", "+1-202-555-0123", "rosalind@cam.ac.uk")
    info.add_publication("j", "My Publication", "Myself", "Journal of Me", "23/12/2014", pages="12-23")
    info.add_value(Metainfo.NAME, StringValue("Test report file"))
    report_file = None
    try:
        report_file = data_importer.create_report_file(metainfo=info, urls=[TEST_URL], parent=created)
    finally:
        if report_file is not None:
            fu.unlink_file(report_file, created)


if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'long', __file__])
