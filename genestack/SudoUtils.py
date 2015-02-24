# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

import getpass
import sys

from Connection import Application
from genestack import GenestackException


class SudoUtils(Application):
    """
    Sudo utils.
    """
    APPLICATION_ID = 'genestack/sudoutils'

    def is_sudo_active(self):
        """
        Return is active. This request extends sudo time.
        """
        return self.invoke('isSudoActive')

    def ensure_sudo(self, password):
        """
        Enable sudo for short amount of time (5 minutes).
        is password is None has same effect as is_sudo_active

        :param password: password
        :type password: str
        :return: True if sudo is active.
        """
        # TODO rename this method in java and javascript https://trac.genestack.com/ticket/3393
        return self.invoke('isPasswordCorrect', password)

    def ensure_sudo_interactive(self, password):
        """
        SHow interactive dialog of entering sudo password.

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
