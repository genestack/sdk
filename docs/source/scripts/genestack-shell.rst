
genestack-shell
==================

``genestack-shell`` is installed with the Python Client Library and can be accessed from a terminal by typing ``genestack-shell``.


Usage
-----
This script can be used both in interactive shell mode and in static command-line mode:

  .. code-block:: text

    usage: genestack-shell [-H <host>] [-u <user>] [-p <password>] [-h] [<command>]
    
    Shell and commandline application
    
    positional arguments:
      <command>             "call", "time" or empty to use shell
    
    optional arguments:
      -h, --help            show this help message and exit
    
    connection:
      -H <host>, --host <host>
                            server host
      -u <user>             user alias from settings or email
      -p <password>         user password
    

You can get a description for every ``command`` by typing:

  .. code-block:: text

    $ genestack-shell command -h


In shell mode, type ``help`` to get a list of available commands.
Use ``help command`` to get help for a specific command.

See :ref:`Connection` for more information about connection arguments.


Commands
--------
- **call**:

  .. code-block:: text

    usage: genestack-shell call [-h] [-H <host>] [-u <user>] [-p <password>]
                             applicationId method ...
    
    call another application's method
    
    command arguments:
      applicationId         full application id
      method                application method
      params                params
    
    optional arguments:
      -h, --help            show this help message and exit
    
    connection:
      -H <host>, --host <host>
                            server host
      -u <user>             user alias from settings or email
      -p <password>         user password
    


- **time**:

  .. code-block:: text

    usage: genestack-shell time [-h] [-H <host>] [-u <user>] [-p <password>]
                             applicationId method ...
    
    invoke with timer
    
    command arguments:
      applicationId         full application id
      method                application method
      params                params
    
    optional arguments:
      -h, --help            show this help message and exit
    
    connection:
      -H <host>, --host <host>
                            server host
      -u <user>             user alias from settings or email
      -p <password>         user password
    




