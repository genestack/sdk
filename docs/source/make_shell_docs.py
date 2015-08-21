import os
import imp
from genestack_client.GenestackShell import get_help
from genestack_client import make_connection_parser

import sys
sys.path.append('..')


template = """
{name}
{name_underline}===

{name} installed with Python Client Library and accessed as ``{name}``.


Usage
-----
This script can be used both as shell and command line:

  .. code-block:: text

    {usage}

You can get description for every ``command`` by running:

  .. code-block:: text

    $ {name} command -h


In shell mode type ``help`` to get list of available commands.
Use ``help command`` to get command help.

See :ref:`Connection` for more information about connection arguments.


Commands
--------
{commands}

{footer}
"""


def generate_rst_doc(shell_name, class_name, footer_file_name, save_path):
    with open(os.path.join(os.path.dirname(__file__), '..', '..', shell_name)) as f:
        shell_module = imp.new_module('shell_name')
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
    generate_rst_doc('genestack-application-manager', 'ApplicationManager', 'app-manager_header.txt', os.path.join('scripts', 'genestack-application-manager.rst'))
    generate_rst_doc('genestack-shell', 'Shell', None, os.path.join('scripts', 'genestack-shell.rst'))
    generate_rst_doc('genestack-user-setup', 'UserManagement', None, os.path.join('scripts', 'genestack-user-setup.rst'))


if __name__ == '__main__':
    main()
