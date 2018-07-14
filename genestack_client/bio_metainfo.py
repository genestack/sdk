# -*- coding: utf-8 -*-

import sys

from genestack_client import BioMetaKeys, Metainfo


# FIXME: add deprecation warning to access for all attributes of class via __getattribute__()
class BioMetainfo(Metainfo, BioMetaKeys):
    """
    A metainfo representation with additional methods for biological metadata.

    This class is deprecated, use :py:class:`~genestack_client.Metainfo` instead.
    Constants are moved to BioMetaKeys.
    """

    def __init__(self, iterable=None, **kwargs):
        sys.stderr.write('BioMetainfo class is deprecated, '
                         'use Metainfo class instead\n')
        super(BioMetainfo, self).__init__(iterable, **kwargs)

    def add_organism(self, key, value):
        """
        Add an organism value.

        This method is deprecated use :py:meth:`~genestack_client.Metainfo.add_string` instead.

        :param key: key
        :type key: str
        :param value: organism name
        :type value: str
        :rtype: None
        """
        sys.stderr.write('BioMetainfo.add_organism method is deprecated, '
                         'use Metainfo.add_string instead\n')

        self.add_string(key, value)

    def add_ethnic_group(self, key, value):
        """
        Add an ethnic group value.

        This method is deprecated use :py:meth:`~genestack_client.Metainfo.add_string` instead.

        :param key: key
        :type key: str
        :param value: ethnic group name
        :type value: str
        :rtype: None
        """
        sys.stderr.write('BioMetainfo.add_ethnic_group method is deprecated, '
                         'use Metainfo.add_string instead\n')
        self.add_string(key, value)
