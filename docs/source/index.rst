Genestack Python Client
=======================

The Genestack Python Client Library is a Python library that allows you to interact programatically with an instance of the Genestack platform.

At a low level, it allows you to login to Genestack as a specific user (like you would through a web browser), and call the public Java methods of any application that user has access to. 

Importantly, the Genestack Python Client Library includes the ``genestack-application-manager``, a command-line utility that allows you to upload your own applications to a Genestack instance. 

Several functions are also provided to perform typical Genestack file system operations, such as uploading files to Genestack, finding files, retrieving their metainfo, and so on. Additionally, several wrapper classes allow you to interact with command-line applications on the platform (to create files and edit their parameters).

Apart from uploading apps, typical use cases of the Python Client Library include:
  * uploading many files to Genestack at once
  * editing the metainfo of Genestack files based on some local data (e.g. an Excel table)
  * creating / updating files using command-line applications
  
All communications with the Genestack server use `HTTPS <http://en.wikipedia.org/wiki/HTTP_Secure>`_.

If you have never used ``genestack_client`` before, you should read the :doc:`getting_started` guide to get familiar with the library.


Contents:

.. toctree::
   :maxdepth: 2

   Getting Started <getting_started>
   api_reference
   scripts/scripts

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

