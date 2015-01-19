import os
from genestack.GenestackShell import get_help
from genestack import make_connection_parser

import sys
sys.path.append('..')

files = [
    ('genestack-application-manager', 'ApplicationManager'),
    ('genestack-user-setup', 'UserManagement')
]

template = """
{0}


Usage
-----
This application can be used both as shell and command line::

    {usage}

In shell mode type `help` to get list of available commands.
Read :doc:`connection` for more info about connection arguments.

Commands
--------
{1}
"""


def generate_rst_doc(shell_name, class_name):
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

    with open('%s.rst' % shell_name, 'w') as f:
        f.write(template.format(
            '%s\n%s' % (tool_file_name, '=' * len(tool_file_name)),
            '\n'.join(commands),
            description=shell.DESCRIPTION,
            usage=script_help,
        ))


def main():
    for shell_name, class_name in files:
        generate_rst_doc(shell_name, class_name)


if __name__ == '__main__':
    main()
