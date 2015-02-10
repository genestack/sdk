import os
from genestack.GenestackShell import get_help
from genestack import make_connection_parser

import sys
sys.path.append('..')


template = """
{name}.py
{name_underline}===

{name} installed with pythonSDK and accessed as ``{name}.py``.


Usage
-----
This script can be used both as shell and command line::

    {usage}

You can get description for every ``command`` by running::

  {name}.py command -h


In shell mode type ``help`` to get list of available commands.
Use ``help command`` to get command help.

See :doc:`../examples/connection` for more information about connection arguments.


Commands
--------
{commands}

{footer}
"""


def generate_rst_doc(shell_name, class_name, footer_file_name, save_path):
    shell_module = __import__(shell_name)
    shell = getattr(shell_module, class_name)

    tool_file_name = os.path.basename(shell_name)
    commands = []

    script_help = get_help(shell().get_shell_parser()).replace("\n", "\n    ").replace('sphinx-build',
                                                                                       tool_file_name + '.py')

    for command in sorted(shell.COMMAND_LIST):
        command = command()
        parser = command.get_command_parser(parser=None if command.OFFLINE else make_connection_parser())
        help_text = get_help(parser).replace("\n", "\n    ").replace('sphinx-build', tool_file_name + '.py')
        text = ' - **%s**::\n\n    %s\n' % (command.COMMAND, help_text)
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
    generate_rst_doc('genestack-application-manager', 'ApplicationManager', 'app-manager_usage.rst', os.path.join('..', 'track_docs', 'genestack-application-manager.rst'))
    generate_rst_doc('genestack-user-setup', 'UserManagement', None, os.path.join('scripts', 'genestack-user-setup.rst'))


if __name__ == '__main__':
    main()
