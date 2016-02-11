#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2016 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

from distutils.core import setup
exec(open('genestack_client/version.py').read())

setup(
    name='genestack_client',
    version=__version__,
    packages=['genestack_client', 'genestack_client.settings', 'genestack_client.scripts'],
    url='',
    license='',
    author='Genestack Limited',
    author_email='',
    description='Genestack Python Client Library',
    install_requires=['keyring', 'requests'],
    entry_points={
        'console_scripts': [
            'genestack-user-setup = genestack_client.scripts.genestack_user_setup:main',
            'genestack-shell = genestack_client.scripts.genestack_shell:main',
            'genestack-application-manager = genestack_client.scripts.genestack_application_manager:main',
            'genestack-uploader = genestack_client.scripts.genestack_uploader:main',
        ],
    }
)
