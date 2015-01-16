import os
from genestack.GenestackShell import get_help

import sys
sys.path.append('..')

files = [
    ('genestack-application-manager','ApplicationManager'),
    ('genestack-user-setup', 'UserManagement')
]

template = """
{0}

Commands
--------
{1}
"""


def generate_rst_doc(shell_name, class_name):
    shell_module = __import__(shell_name)
    shell = getattr(shell_module, class_name)

    tool_file_name = os.path.basename(shell_name)
    commands = []
    for command in sorted(shell.COMMAND_LIST):
        command = command()
        help_text = get_help(command.get_command_parser()).replace("\n", "\n            ").replace('make_shell_docs.py',
                                                                                           tool_file_name)
        text = ' - **%s**::\n\n        %s\n' % (command.COMMAND, help_text)
        commands.append(text)

    with open('%s.rst' % shell_name, 'w') as f:
        f.write(template.format(
            '%s\n%s' % (tool_file_name, '=' * len(tool_file_name)),
            '\n'.join(commands)
        ))


def main():
    for shell_name, class_name in files:
        generate_rst_doc(shell_name, class_name)


if __name__ == '__main__':
    main()
