Connection
==========

Create connection
-----------------

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
-------------------------------
If not arguments specifies will use default user

``-u <alias or email>``
  if not other params is specified try to get alias from settings, if faile will open interactive login to default server
``-H <host>``
  if host is specified user is treated as email
``-p <password>``
  if password is not specified will trigger interactive login.


