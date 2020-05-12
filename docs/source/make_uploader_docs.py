from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
import imp
import os
from argparse import ArgumentParser

template = """
{name}
{name_underline}===

``{name}`` is installed with the Python Client Library and can be accessed from a terminal by typing ``{name}``.

.. WARNING!!! Don not edit part from below, it is auto-generated from script help output


Usage
-----
  .. code-block:: text

    {usage}

``{name}`` exits with ``0`` return code in case of success, ``1`` if
recognition failed, and ``13`` if server requires newer Python Client version.
"""


def main():
    with open(os.path.join(os.path.dirname(__file__), '..', '..', 'genestack_client', 'scripts', 'genestack_uploader.py')) as f:
        module = imp.new_module('shell_name')
        exec(f.read(), module.__dict__)

    name = 'genestack-uploader'
    name_underline = '=' * len(name)

    parser = module.parser
    assert (isinstance(parser, ArgumentParser))

    usage = parser.format_help().replace("\n", "\n    ").replace('sphinx-build', name)

    with open('scripts/genestack-uploader.rst', 'w') as f:
        f.write(template.format(name=name, name_underline=name_underline, usage=usage))


if __name__ == '__main__':
    main()
