Genestack Python Client Library
===============================

The Genestack Python Client Library is a Python library that allows you to interact programatically with an instance of the Genestack platform.

**Python 2** supported from version `2.7.5`, **Python 3** is not supported.

At a low level, it allows you only to login to Genestack as a specific user (like you would through a web browser) and call the public Java methods of any application that your user has access to.

Importantly, the Genestack Python Client Library includes the ``genestack-application-manager``, a command-line utility that allows you to upload your own applications to a Genestack instance. This tool is essential if you are a third-party developer, as this is currently the only way for you to upload your apps to a Genestack instance.

Several functions are also provided to perform typical Genestack file system operations, such as uploading files to Genestack, finding files, retrieving their metainfo, and so on. Additionally, several wrapper classes allow you to interact with command-line applications on the platform, to create files and edit their parameters.

Apart from uploading apps, typical use cases of the Python Client Library include:

* uploading many files to Genestack at once
* editing the metainfo of Genestack files based on some local data (e.g. an Excel spreadsheet)
* creating / updating files using command-line applications

.. note::
    All communications with the Genestack server use `HTTPS <http://en.wikipedia.org/wiki/HTTP_Secure>`_.

You can read the section :doc:`getting_started` for a gentle introduction to the client library.


Contents
========

.. toctree::
   :maxdepth: 2

   Getting Started <getting_started>
   sample_scripts_doc
   api_reference
   scripts/scripts

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
