#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#


class Admin:
    def __init__(self, connection):
        self.connection = connection

    def login(self, user, pwd):
        try:
            self.connection.logout()
        except Exception:
            pass
        self.connection.login(user, pwd)

    def logout(self):
        self.connection.logout()

    def create_user(self, email, pwd, name):
        return self.connection.application('usersadmin').invoke('createUser', email, pwd, name)

    def change_admin_status(self, email):
        return self.connection.application('usersadmin').invoke('changeAdminStatus', email)

    def create_group(self, name):
        return self.connection.application('groupsadmin').invoke('createGroup', name)

    def add_group_member(self, group, email):
        return self.connection.application('groupsadmin').invoke('addMemberToGroup', group, email)

    def invite(self, group, user, comment=''):
        return self.connection.application('groupsadmin').invoke('inviteUserIntoGroup', group, user, comment)

    def get_outgoing_invitations(self):
        return self.connection.application('groupsadmin').invoke('listOutgoingInvitations')

    def get_incoming_invitations(self):
        return self.connection.application('groupsadmin').invoke('listIncomingInvitations')

    def confirm_invitation(self, invitation_id, confirmed=True):
        return self.connection.application('groupsadmin').invoke('setInvitationConfirmed', int(invitation_id),
                                                                 confirmed)

    def dry_run_create_organization(self, organization_name, email):
        self.connection.application('registration').invoke('dryRunCreateOrganization', organization_name, email)

    def registration_request(self, organization_name, email, password, display_name):
        self.connection.application('registration').invoke('registrationRequest', organization_name,
                                                           email, password, display_name)

    def confirm_registration(self, token):
        return self.connection.application('registration').invoke('confirmRegistration', token)

    # TODO: remove this method and use SUPERUSER privilege to activate any user. https://trac.genestack.com/ticket/1864
    def enable_user(self, email):
        return self.connection.application('registration').invoke('enableUser', email)

    def send_feedback_message(self, email, message):
        return self.connection.application('feedback').invoke('sendFeedbackMessage', email, message)

    def password_recovery_request(self, email):
        self.connection.application('registration').invoke('passwordRecoveryRequest', email)

    def recover_password(self, email, token, password):
        return self.connection.application('registration').invoke('recoverPassword', email, token, password)
