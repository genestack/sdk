Getting Started with the Genestack Python Client Library
########################################################

Installing the Library
**********************

.. note::

    At the moment, the Genestack SDK is not available to the public.
    To get the library sources or to access the GitHub repository, ask somebody at Genestack.


If you have access to the GitHub repository, you can either `clone it <https://github.com/genestack/python-client/>`_ or download and unpack  `the latest release <https://github.com/genestack/python-client/releases/latest/>`_.

Once inside the directory, you can install the library using ``pip`` if it is available on your system (if not, have a look at the `pip install instructions <https://pip.pypa.io/en/latest/installing.html>`_):

.. code-block:: sh

    $ sudo pip install .

.. note::

    You can also install the library without ``pip``, by typing ``python setup.py install``.
    In that case make sure that the dependencies `keyring <https://pypi.python.org/pypi/keyring>`_
    and `requests <http://docs.python-requests.org/en/latest/user/install/#install>`_ are installed


Then, you can test your installation by executing:

.. code-block:: sh

    $ python -c 'import genestack_client; print genestack_client.__version__'

If the command executes without returning an error, you have successfully installed the Genestack Python Client Library. Yay!


.. note::

    If you see a warning such as ``InsecurePlatformWarning: A true SSLContext object is not available`` in the console,
    you can either update your Python to the latest ``2.7.*`` version, or install the ``security`` package extras using ``pip``:

    .. code-block:: sh

        $ sudo pip install 'requests[security]'


Configuring Credentials
***********************

The Genestack Python Client Library works by logging in to a Genestack instance (by default `platform.genestack.org <https://platform.genestack.org/endpoint/application/run/genestack/signin>`_).
Therefore, before doing anything you need to have an account on the Genestack instance to which you want to connect.

To avoid typing in your credentials every time you connect to a Genestack instance programmatically, the library comes with a utility ``genestack-user-setup`` which allows you to store locally, in a secure manner, a list of user identities to login to Genestack. To configure your first user identity, type in the following command in a terminal:

.. code-block:: sh

    $ genestack-user-setup init

You will be prompted for your email and password to connect to Genestack. If they are valid and the connection to the Genestack server is successful, you're all set!

To check the result, you can run:

.. code-block:: sh

    $ genestack-user-setup list
    user@email.com (default):
    email     user@email.com
    host      platform.genestack.org

.. warning::

   By default, your password will be stored using a secure storage system provided by your OS (See https://pypi.python.org/pypi/keyring for more information)
   If the secure storage system is not accessible, you will be asked for permission to store your password in plain text in a configuration file. However, this option is **strongly discouraged**. You have been warned!


.. note::

   The information you supply to ``genestack-user-setup`` is only stored locally on your computer. Therefore, if you change your password online, you will need to update your local configuration as well.


Setting up additional users
---------------------------

If you have multiple accounts on Genestack (or you are using multiple instances of Genestack), you can define multiple identities with the ``genestack-user-setup``.

Each user has an alias (unique identifier), an email address, a host address and a password. The host name will be ``platform.genestack.com`` by default. There is no limitation to the number of identities you can store locally, and you can even use different aliases for the same account. To add a new identity, type in:

.. code-block:: sh

    $ genestack-user-setup add

.. note::

    To know more about user management, have a look at: :doc:`scripts/genestack-user-setup`

.. _Connection:

Connecting to a Genestack instance
**********************************

To communicate with a Genestack instance using the library, the first thing you need is to open a connection to the server.

Passing Connection Parameters via Command-line Arguments
--------------------------------------------------------

The easiest way to open a connection is through the helper function: :py:func:`~genestack.get_connection`.
It uses command line arguments parsed by an :py:class:`argparse.ArgumentParser` to find your credentials in the local config file. If no arguments are supplied to your script, the connection will attempt to log in with the default user specified by ``genestack-user-setup``.
You can specify another user by appending ``-u <user_alias>`` to your command line call. For example, let's consider the following script, saved in ``my_genestack_script.py``, that simply creates a connection to the Genestack server and returns the e-mail address of the current user:

.. code-block:: python

    from genestack_client import get_connection

    connection = get_connection()
    print connection.whoami()

Using the connection parameters, you can run this script from a terminal using different Genestack identities:

.. code-block:: sh

    # login with default user
    $ python my_genestack_script.py
    user@email.com

    # login as bob@email.com, present in the config file under the alias "bob"
    $ python my_genestack_script.py -u bob
    bob@email.com


.. TODO talk more about the parser and how you shouldn't use get_connection()

If your script accepts custom command-line arguments, you can add them to the arguments parser returned by :py:func:`~genestack.make_connection_parser`.
The arguments ``-u``, ``-p`` and ``-H`` are reserved for the connection parameters.
Have a look at the following example:

.. code-block:: python

    from genestack_client import get_connection, make_connection_parser

    # create an instance of argparse.ArgumentParser with predefined arguments for connection
    parser = make_connection_parser()
    parser.add_argument('-c', '--unicorn',  dest='unicorn', action='store_true', help='Set if you have a unicorn.')
    args = parser.parse_args()
    connection = get_connection(args)
    email = connection.whoami()
    if args.unicorn:
        print '%s has a UNICORN!!' % email
    else:
        print '%s does not have a unicorn :(' % email

.. code-block:: sh

    $ python my_script.py --unicorn
    user@email.com has a UNICORN!!

    $ python my_script.py -u bob
    bob@email.com does not have a unicorn :(

.. warning::
    
    If you use custom arguments, make sure to follow the syntax of the previous script: first, retrieve the parser with ``make_connection_parser()``, then add the new argument to it, parse the command-line arguments and finally send them to ``get_connection``.

Arguments Accepted by the Connection Parser
---------------------------------------------

If no connection parameter is passed to your script, ``get_connection`` will attempt a connection using the default identity from your local configuration file (you can change it via the command ``genestack-user-setup default``).

If only the parameter ``-u <alias>`` is supplied, the parser will look for the corresponding identity in the local configuration file. If no match is found, the script will switch to interactive login.

You can also supply the parameters ``-u <email> -H <host> -p <password>``. By default, the host is ``platform.genestack.com`` and if no password is provided, you will be prompted for one.

.. code-block:: sh

    $ python my_script.py -u user@email.com -H platform.genestack.org -p password


Using Hard-coded Connection Parameters 
--------------------------------------

You can also supply hard-coded parameters for the connection directly inside your script.

.. warning::
    
    This approach is only provided for reference, but it is **strongly discouraged**, as it requires you (among other things) to store your e-mail and password in plain text inside your code.


.. code-block:: python

    from genestack_client import Connection

    # crease connection object for server
    connection = Connection('https://platform.genestack.org/endpoint')

    # login as user: 'user@email.com' with password 'password'
    connection.login('user@email.com', 'password')
    print connection.whoami()


.. code-block:: sh

    $ python my_script.py
    user@email.com

Calling an Application's Methods
********************************

You can use the client library to call the public Java methods of any application that is available to the current user. You just need to supply the application ID and the method name

.. code-block:: python

    from genestack_client import get_connection

    connection = get_connection()
    print connection.application('genestack/signin').invoke('whoami')

And here is how to call a Java method with arguments:

.. code-block:: python

    from genestack_client import get_connection, Metainfo, PRIVATE


    connection = get_connection()
    metainfo = Metainfo()
    metainfo.add_string(Metainfo.NAME, "New folder")
    print connection.application('genestack/filesUtil').invoke('createFolder', PRIVATE, metainfo)

The number, order and type of the arguments should match between your Java methods and the Python call to ``invoke``. Type conversion between Python and Java generally behaves in the way you would expect (a Python numeric variable will be either an ``int`` or ``double``, a Python list will become a ``List``, a dictionary will become a ``Map``, etc.)

The client library comes with a lot of wrapper classes around common Genestack applications, which allow you to use a more convenient syntax to invoke the methods of specific application (see section below).

If you need to make extensive use of an application that does not already have a wrapper class in the client library, you can easily create your own wrapper class in a similar way. Your class simply needs to inherit from ``Application`` and declare an ``APPLICATION_ID``:

.. code-block:: python

    from genestack_client import Application, get_connection


    class SignIn(Application):
        APPLICATION_ID = 'genestack/signin'

        def whoami(self):
            return self.invoke('whoami')


    connection = get_connection()
    signin = SignIn(connection)
    print signin.whoami()


Pre-defined Application Wrappers
********************************

This section illustrates briefly some of the things you can do using the pre-defined application wrappers from the client library.
For a more detailed description of these wrappers, have a look at :ref:`ApplicationWrappers`.

FilesUtil
---------

``FilesUtil`` is a Genestack application used for typical file system operations: finding, linking, removing and sharing files.

First, let's open a connection::

    >>> from genestack_client import get_connection
    >>> connection = get_connection()

Then we create a new instance of the class::

    >>> from genestack_client import FilesUtil
    >>> file_utils = FilesUtil(connection)


Then we can create a new empty folder::

    >>> folder_accession = file_utils.create_folder("My new folder")
    >>> print folder_accession
    GSF000001

By default, this one was created in the "Created Files" folder of the current user, but we can define any folder as parent::

    >>> inner_folder_accession = file_utils.create_folder("My inner folder", parent=folder_accession)
    >>> print inner_folder_accession
    GSF000002


Finding a folder by its name::

    >>> folder_accession = file_utils.find_file_by_name("My inner folder", file_class=FilesUtil.IFolder)
    >>> print folder_accession
    GSF000002


See :ref:`FilesUtil` for more methods.


Importers
---------

As always, we start by creating a connection::

    >>> from genestack_client import get_connection
    >>> connection = get_connection()

Then we create a new instance of the app::

    >>> from genestack_client import DataImporter
    >>> importer = DataImporter(connection)

Then let's create an experiment in ``Imported files``::

    >>> experiment = importer.create_experiment(name='Sample of paired-end reads from A. fumigatus WGS experiment',
    ... description='A segment of a paired-end whole genome sequencing experiment of A. fumigatus')


We can add a sequencing assay to the experiment, using local files as sources::


    >>> assay = importer.create_sequencing_assay(experiment,
    ...                                          name='Test paired-end sequencing of A. fumigatus',
    ...                                          links=['ds1.gz', 'ds2.gz'],
    ...                                          organism='Aspergillus fumigatus',
    ...                                          method='genome variation profiling by high throughput sequencing')
    Uploading ds1.gz - 100.00%
    Uploading ds2.gz - 100.00%

Let's print the results to know the accession of our files::

    >>> print 'Successfully load assay with accession %s to experiment %s' % (assay, experiment)
    Successfully load assay with accession GSF000002 to experiment GSF000001

And finally we can start the initialization of the file::

    >>> from genestack_client import FileInitializer
    >>> initializer = FileInitializer(connection)
    >>> initializer.initialize([assay])
    >>> print 'Start initialization of %s' % assay
    Start initialization of GSF000002

As a result you should have

    - an ``Experiment`` folder in ``Imported files``
    - a ``Sequencing assay`` file inside the experiment
    - Two ``Raw Upload`` files in the ``Uploaded files`` folder. (these are just plain copies of your raw uploaded files; they can be removed once the sequencing assays have been initialized)

See :ref:`DataImporter` for more info.

TaskLogViewer
-------------

The Task Log Viewer allows you to access the contents of initialization logs programatically. 

Again, we start by opening a connection and instantiating the class::

    >>> from genestack_client import get_connection
    >>> connection = get_connection()
    >>> from genestack_client import TaskLogViewer
    >>> log_viewer = TaskLogViewer(connection)

Then we can check the error log of a file::

    >>> log_viewer.view_log('GSF000001', log_type=TaskLogViewer.STDERR, follow=False)
    This log is empty (perhaps there was no log produced)


See :ref:`TaskLogViewer` for more info.

