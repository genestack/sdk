from setuptools import setup
import re
"""
Python library that allows you to interact programmatically with an instance of
the Genestack platform.
"""

regex = re.compile(r'^--.*$')
# Read requirements file to download deps with filtering params.
with open('requirements.txt') as f:
    required = [line for line in f.read().splitlines() if not regex.match(line)]

# Import version directly, without execute __init__.py script
exec(open('genestack_client/version.py').read())

setup(
    name='genestack_client',
    install_requires=required,
    version=__version__,
    packages=['genestack_client', 'genestack_client.settings', 'genestack_client.scripts'],
    url='https://github.com/genestack/python-client',
    license='MIT',
    author='Genestack Limited',
    author_email='',
    description='Genestack Python Client Library',
    long_description=__doc__,
    long_description_content_type="text/markdown",
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'genestack-user-setup = genestack_client.scripts.genestack_user_setup:main',
            'genestack-shell = genestack_client.scripts.shell:main',
            'genestack-uploader = genestack_client.scripts.genestack_uploader:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        'Topic :: Software Development',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],

    project_urls={
        'Documentation': 'https://genestack-client.readthedocs.io/en/stable/',
        'Source': 'https://github.com/genestack/python-client/',
        'Tracker': 'https://github.com/genestack/python-client/issues',
    },
    keywords=['genestack', 'genomics', 'api'],
)
