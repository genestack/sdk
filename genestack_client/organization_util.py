# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
from genestack_client import (Application)


class OrganizationUtil(Application):
    """
    An application to perform operations with organization of the current user on Genestack.
    """
    APPLICATION_ID = 'genestack/organizationUtil'

    def get_organization_name(self):
        """
        Get name of organization of the current user.

        :return: organization name
        :rtype: str
        """
        return self.invoke('getOrganizationName')

    def add_value_to_metainfo(self, key, metainfo_value):
        """
        Add a value to the metainfo of organization of the current user.

        :param key: metainfo key
        :type key: str
        :param value: metainfo value
        :type value: MetainfoScalarValue
        :rtype: None
        """
        self.invoke('addToOrganizationMetainfo', key, metainfo_value)

    def replace_metainfo_value(self, key, metainfo_value):
        """
        Replace a value in the metainfo of organization of the current user.

        :param key: metainfo key
        :type key: str
        :param value: metainfo value
        :type value: MetainfoScalarValue
        :rtype: None
        """
        self.invoke('replaceOrganizationMetainfoValue', key, metainfo_value)

    def remove_metainfo_value(self, key):
        """
        Remove a value from the metainfo of organization of the current user.

        :param key: metainfo key
        :type key: str
        :rtype: None
        """
        self.invoke('removeFromOrganizationMetainfo', key)
