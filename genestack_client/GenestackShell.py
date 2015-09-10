import sys

sys.stderr.write('Warning: genestack_client."{0}" module is obsolete, use genestack_client.genestack_shell instead\n'.format(__name__))

from genestack_shell import *
