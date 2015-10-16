from argparse import ArgumentParser
import imp
import os


template = """
{name}
{name_underline}===

``{name}`` is installed with the Python Client Library and can be accessed from a terminal by typing ``{name}``.


Usage
-----
  .. code-block:: text

    {usage}

"""


def main():
    with open(os.path.join(os.path.dirname(__file__), '..', '..', 'genestack-uploader')) as f:
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
