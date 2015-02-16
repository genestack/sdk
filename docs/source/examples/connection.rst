Connection
**********

Get connection
==============

To work with platform you should have connection. First thing you need is to have account at genestack sight.

* Connection via arguments


    Preferred way to get connection via helper function.  First thing you need to setup users.
    get_connection use Argparse module to get your credentials from config file. By default it uses credentials of default user.
    You can specify other user by adding ``-u <alias>`` to command line argument.

    **Get connection**::

        from genestack import get_connection

        connection = get_connection()
        print connection.whoami()


    **Run script from commandline**:


    .. code-block:: sh

        # with default user
        $ ./script.py
        user@email.com

        # with user bob@email.com that present in config with alias bob

        $ ./script.py -u bob
        bob@email.com


    In case then you need more arguments you need to add it to connection_parser. Arguments ``-u``, ``-p`` and ``-H`` are reserved for connection.


    **Connection with additional script arguments**::

        from genestack import get_connection, make_connection_parser

        parser = make_connection_parser()  # return instance of argparse.ArgumentParser
        parser.add_argument('-c', '--unicorn',  dest='unicorn', action='store_true', help='Set if you have unicorn.')
        args = parser.parse_args()
        connection = get_connection(args)
        if args.unicorn:
            print connection.whoami(), 'has unicorn!'
        else:
            print connection.whoami(), 'does not have unicorn.'


    .. code-block:: sh

        $ ./script.py -u
        user@email.com has unicorn!

        $ ./script.py -u bob
        bob@email.com does not have unicorn.


    **Arguments for connection parser**

    * Using settings:

      if no argument specified get_connection will return connection to default user

      if only ``-u <alias>`` is specified will be used user from settings. If user is not present system will switch to interactive login with default server.

    * Raw input:

        if ``-H <host>`` or ``-p <password>`` or both will be specified login will treat it as raw input

        ``-u <email>`` expects email

        ``-H <host>`` server host, if it is not specified will use default host.

        ``-p <password>`` if password is not specified user should add it in interactive mode.

        .. code-block:: sh

            $ ./script.py -u user@email.com -H platform.genestack.org -p passwords


* Create connection directly in code

    This approach required more efforts and require so store your password as plain text.

    ::

        from genestack import Connection

        # crease connection object for server
        connection = Connection('https://platform.genestack.org/endpoint')

        # login as user: 'user@email.com' with password 'password'
        connection.login('user@email.com', 'password')
        print connection.whoami()


    Run script from commandline:

    .. code-block:: sh

        $ ./script.py
        user@email.com

Connection usage
================


With connection you can call application methods::

    # whoami implementation.
    application_id = 'signin'
    method = 'whoami'

    application = connection.application(application_id)
    email = application.invoke(method)

Method can access arguments. To invoke method you need to pass exactly same number of arguments of same type.

.. TODO make table java python javascrpt serializable objects.


You can send connection to predefined or your own applications:
 - Operations for managing files :doc:`FileUtils`
 - Importing data :doc:`DataImporter`
 - Calling application methods :doc:`call_methods`



