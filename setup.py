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

setup(
    name='genestack',
    version='0.1',
    packages=['genestack', 'genestack.settings'],
    url='',
    license='',
    author='Genestack Limited',
    author_email='',
    description='Genestack API',
    scripts=['genestack-user-setup.py', 'genestack-application-manager.py']
)
