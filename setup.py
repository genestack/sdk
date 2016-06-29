#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from distutils.core import setup
exec(open('genestack_client/version.py').read())

setup(
    name='genestack_client',
    version=__version__,
    packages=['genestack_client', 'genestack_client.settings', 'genestack_client.scripts'],
    url='',
    license='MIT',
    author='Genestack Limited',
    author_email='',
    description='Genestack Python Client Library',
    install_requires=['keyring', 'requests'],
    entry_points={
        'console_scripts': [
            'genestack-user-setup = genestack_client.scripts.genestack_user_setup:main',
            'genestack-shell = genestack_client.scripts.shell:main',
            'genestack-application-manager = genestack_client.scripts.genestack_application_manager:main',
            'genestack-uploader = genestack_client.scripts.genestack_uploader:main',
        ],
    },
    classifiers=[
        'License :: OSI Approved :: MIT License',
    ],
)
