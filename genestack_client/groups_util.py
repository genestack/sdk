# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
from genestack_client import Application


class GroupsUtil(Application):
    APPLICATION_ID = 'genestack/groupsUtil'

    def find_group_by_name(self, name):
        """
        Finds group with specified name.
        If there are no groups or more than one group with this name, an exception is thrown.

        :param name: group name
        :type name: str
        :return: group accession
        :rtype: str
        """
        return self.invoke(
            'findGroupByName', name
        )
