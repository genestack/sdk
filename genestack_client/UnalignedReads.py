import sys

sys.stderr.write('Warning: genestack_client."{0}" module is obsolete, use genestack_client.unaligned_reads instead\n'.format(__name__))

from unaligned_reads import *
