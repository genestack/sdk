Connection
**********

Get connection
==============

To work with platform you should have connection. First thing you need is to have account at genestack sight.

You have different way to create connection:

Create connection directly::

    from genestack import Connection

    # crease connection object for server
    connection = Connection('https://platform.genestack.org/endpoint')

    # login as user: 'your-email@mail.com' with password 'your-email@mail.com'
    connection.login('your-email@mail.com', 'your password')

Now connection is ready. But this approach has some disadvantages: you need to store passwords as plain text, that is not secure.

Preferred way to get connection via helper function.  First thing you need to setup users.
get_connection use Argparse module to get you credentials from config file. By default it uses credentials of default user.
You can specify other user by adding ``-u <alias>`` to command line argument.

Get connection::

    from genestack import get_connection

    connection = get_connection()


In case then you need more arguments you need to add it to connection_parser. Arguments ``-u``, ``-p`` and ``-H`` are reserved for connection.


Connection with additional arguments::

    from genestack import get_connection, make_connection_parser

    parser = make_connection_parser()
    parser.add_argument('-c', '--cool',  dest='cool', action='store_true', help='Add unicorns and stuff')
    connection = get_connection(parser.parse_args())


Arguments for connection parser
===============================

There are two way to specify user:

Using settings:
^^^^^^^^^^^^^^^

  if not argument specified get_connection will return connection to default user

  if only ``-u <alias>`` specified will be used user form settings. If user is not present system will switch to interactive login with default server.

Raw input:
^^^^^^^^^^
  if ``-H <host>`` or ``-p <password>`` or both will be specified login will treat it as raw input

  ``-u <email>`` expect email

  ``-H <host>`` full server host if not specified default host will be used.

  ``-p <password>`` if not password specified will ask it in interactive mode.


