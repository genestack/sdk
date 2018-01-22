# -*- coding: utf-8 -*-

import getpass
import sys

from genestack_client import Application, GenestackException


class SudoUtils(Application):
    """
    An application wrapper to enable superuser mode for the current user.
    This mode is needed to perform actions such as sharing files.
    """
    APPLICATION_ID = 'genestack/sudoutils'

    def is_sudo_active(self):
        """
        Returns a boolean indicating whether superuser mode is still active.

        :return: ``True`` if sudo is active
        :rtype: bool
        """
        return self.invoke('isSudoActive')

    def ensure_sudo(self, password):
        """
        Enable superuser mode for a short amount of time (5 minutes).
        If ``password`` is ``None``, it has the same effect as ``is_sudo_active``

        :param password: password
        :type password: str
        :return: ``True`` if sudo is active
        :rtype: bool
        """
        # TODO rename this method in java and javascript https://trac.genestack.com/ticket/3393
        return self.invoke('ensureSudo', password)

    def ensure_sudo_interactive(self, password):
        """
        Show interactive dialog to enter the superuser password.

        :param password: password
        :type password: str
        :rtype: None
        """
        if self.is_sudo_active():
            return
        if password is None:
            while True:
                pwd = getpass.getpass('Enter sudo password: ')
                if self.ensure_sudo(pwd):
                    return
                # TODO: move this message into getpass() as a prefix:
                sys.stderr.write('Invalid password, try again\n')
        elif not self.ensure_sudo(password):
            raise GenestackException('Invalid password specified')
