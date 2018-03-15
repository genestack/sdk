# -*- coding: utf-8 -*-
from genestack_client import Application


class UserManagement(Application):
    APPLICATION_ID = 'genestack/userManagement'

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

    def get_user_organization(self):
        """
        Gets name of the current users' organization.

        :return: organization name
        :rtype: str
        """
        return self.invoke(
            'getUserOrganization'
        )
