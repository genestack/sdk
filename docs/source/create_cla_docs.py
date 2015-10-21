from inspect import getmembers, isclass
from genestack_client import cla


template = '''
{name}
{name_underline}

.. autoclass:: genestack_client.{name}
        :members:
        :show-inheritance:

        .. autoattribute:: genestack_client.{name}.APPLICATION_ID

'''

import os
print os.getcwd()


def main():
    with open('cla_reference._rst', 'w') as f:
        for name, attr in getmembers(cla):
            if isclass(attr) and name != 'CLApplication' and issubclass(attr, cla.CLApplication):
                f.write(template.format(name=name, name_underline='-' * len(name)))