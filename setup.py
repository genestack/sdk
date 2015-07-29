#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

from distutils.core import setup
exec(open('genestack_cli/version.py').read())

setup(
    name='genestack_cli',
    version=__version__,
    packages=['genestack_cli', 'genestack_cli.settings'],
    url='',
    license='',
    author='Genestack Limited',
    author_email='',
    description='Genestack Python Client Library',
    scripts=['genestack-user-setup', 'genestack-application-manager', 'genestack-uploader', 'genestack-shell'],
    install_requires=['keyring', 'requests[security]']
)
