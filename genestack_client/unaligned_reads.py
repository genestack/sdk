# -*- coding: utf-8 -*-

READS_LOCATION = 'genestack.location:reads'
READS_LINK = 'genestack.url:reads'


class Key(object):
    SPACE = 'space'
    FORMAT = 'format'
    TYPE = 'type'


class Space(object):
    BASESPACE = 'basespace'
    COLORSPACE = 'colorspace'


class Format(object):
    PHRED33 = 'phred33'
    PHRED64 = 'phred64'
    FASTA_QUAL = 'fasta-qual'
    SRA = 'sra'
    SFF = 'sff'
    FAST5 = 'fast5'


class Type(object):
    SINGLE = 'single'
    PAIRED = 'paired'
    PAIRED_WITH_UNPAIRED = 'paired-with-unpaired'


def compose_format_map(space, file_format, file_type):
    return {Key.SPACE: space,
            Key.FORMAT: file_format,
            Key.TYPE: file_type}
