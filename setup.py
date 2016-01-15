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
    packages=['genestack_client', 'genestack_client.settings'],
    url='',
    license='',
    author='Genestack Limited',
    author_email='',
    description='Genestack Python Client Library',
    scripts=['genestack-user-setup', 'genestack-application-manager', 'genestack-uploader', 'genestack-shell'],
    install_requires=['keyring', 'requests']
)
