from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
import os
import sys
import types

from odm_sdk import make_connection_parser
from odm_sdk.shell import get_help

sys.path.append('..')


template = """
{name}
{name_underline}===

``{name}`` is installed with the Python Client Library and can be accessed from a terminal by typing ``{name}``.


.. WARNING!!! Don not edit part from below, it is auto-generated from script help output

Usage
-----
This script can be used both in interactive shell mode and in static command-line mode:

  .. code-block:: text

    {usage}

You can get a description for every ``command`` by typing:

  .. code-block:: text

    $ {name} command -h


In shell mode, type ``help`` to get a list of available commands.
Use ``help command`` to get help for a specific command.

See :ref:`Connection` for more information about connection arguments.

``{name}`` exits with ``0`` return code in case of success, ``1`` in case of
various nondescript errors, and ``13`` if server requires newer Python Client
version.

Commands
--------
{commands}

{footer}
"""


def generate_rst_doc(shell_name, file_name, class_name, footer_file_name, save_path):
    with open(os.path.join(os.path.dirname(__file__), '..', '..', 'odm_sdk', 'scripts', file_name)) as f:
        shell_module = types.ModuleType('shell_name')
        exec(f.read(), shell_module.__dict__)

    shell = getattr(shell_module, class_name)

    tool_file_name = os.path.basename(shell_name)
    commands = []

    script_help = get_help(shell().get_shell_parser()).replace("\n", "\n    ").replace('sphinx-build',
                                                                                       tool_file_name)

    for command in sorted(shell.COMMAND_LIST, key=lambda x: x.COMMAND):
        command = command()
        parser = command.get_command_parser(parser=None if command.OFFLINE else make_connection_parser())
        help_text = get_help(parser).replace("\n", "\n    ").replace('sphinx-build', tool_file_name)
        text = '- **%s**:\n\n  .. code-block:: text\n\n    %s\n\n' % (command.COMMAND, help_text)
        commands.append(text)

    if footer_file_name:
        with open(footer_file_name) as f:
            footer = f.read()
    else:
        footer = ''

    with open(save_path, 'w') as f:
        f.write(template.format(
            name=tool_file_name,
            name_underline='=' * len(tool_file_name),
            commands='\n'.join(commands),
            description=shell.DESCRIPTION,
            usage=script_help,
            footer=footer,
        ))


def main():
    generate_rst_doc('odm-shell', 'shell.py', 'Shell', None, os.path.join('scripts', 'odm-shell.rst'))
    generate_rst_doc('odm-user-setup', 'user_setup.py', 'UserManagement', None, os.path.join('scripts', 'odm-user-setup.rst'))


if __name__ == '__main__':
    main()
