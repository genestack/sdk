Connection
**********

Create connection
=================

You need to have genestack account to connect to server.

Connection as default user::

    from genestack import get_connection

    connection = get_connection()

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


