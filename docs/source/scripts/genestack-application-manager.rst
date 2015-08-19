
genestack-application-manager
================================

``genestack-application-manager`` is installed with the Python Client Library and can be accessed from a terminal by typing ``genestack-application-manager``.


Usage
-----
This script can be used both in interactive shell mode and in static command-line mode:

  .. code-block:: text

    usage: genestack-application-manager [-H <host>] [-u <user>] [-p <password>] [-h] [<command>]
    
    The Genestack Application Manager is a command-line utilitythat allows you to
    upload and manageyour applications on a specific Genestack instance
    
    positional arguments:
      <command>             "info", "invoke", "versions", "remove",
                            "applications", "reload", "install", "stable" or empty
                            to use shell
    
    optional arguments:
      -h, --help            show this help message and exit
    
    connection:
      -H <host>, --host <host>
                            server host
      -u <user>             user alias from settings or email
      -p <password>         user password
    

You can get a description for every ``command`` by typing:

  .. code-block:: text

    $ genestack-application-manager command -h


In shell mode, type ``help`` to get a list of available commands.
Use ``help command`` to get help for a specific command.

See :ref:`Connection` for more information about connection arguments.


Commands
--------
- **applications**:

  .. code-block:: text

    usage: genestack-application-manager applications [-h] [-H <host>] [-u <user>] [-p <password>]
    
    Show information about available applications.
    
    optional arguments:
      -h, --help            show this help message and exit
    
    connection:
      -H <host>, --host <host>
                            server host
      -u <user>             user alias from settings or email
      -p <password>         user password
    


- **info**:

  .. code-block:: text

    usage: genestack-application-manager info [-h] [-f] [-F] [--vendor]
                             <jar_file_or_folder> [<jar_file_or_folder> ...]
    
    Display information about an application's JAR file.
    
    command arguments:
      -f, --with-filename   show file names for each JAR
      -F, --no-filename     do not show file names
      --vendor              show only vendor for each JAR file
      <jar_file_or_folder>  file to upload or folder with single JAR file inside
                            (recursively)
    
    optional arguments:
      -h, --help            show this help message and exit
    


- **install**:

  .. code-block:: text

    usage: genestack-application-manager install [-h] [-H <host>] [-u <user>] [-p <password>] [-o]
                                [-s] [-S <scope>]
                                <version> <jar_file_or_folder>
                                [<jar_file_or_folder> ...]
    
    Upload and install an application's JAR file to a Genestack instance.
    
    command arguments:
      -o, --override        overwrite old version of the applications with the new
                            one
      -s, --stable          mark installed applications as stable
      -S <scope>, --scope <scope>
                            scope in which application will be stable (default is
                            'user'): session | system | user
      <version>             version of applications to upload
      <jar_file_or_folder>  file to upload or folder with single JAR file inside
                            (recursively)
    
    optional arguments:
      -h, --help            show this help message and exit
    
    connection:
      -H <host>, --host <host>
                            server host
      -u <user>             user alias from settings or email
      -p <password>         user password
    


- **invoke**:

  .. code-block:: text

    usage: genestack-application-manager invoke [-h] [-H <host>] [-u <user>] [-p <password>]
                               <appId> <method> [<args> [<args> ...]]
    
    Invoke method of a stable application.
    
    command arguments:
      <appId>               application identifier
      <method>              application method to call
      <args>                application method to call
    
    optional arguments:
      -h, --help            show this help message and exit
    
    connection:
      -H <host>, --host <host>
                            server host
      -u <user>             user alias from settings or email
      -p <password>         user password
    


- **reload**:

  .. code-block:: text

    usage: genestack-application-manager reload [-h] [-H <host>] [-u <user>] [-p <password>]
                               <version> <appId> [<appId> ...]
    
    Reload a specific version of an application.
    
    command arguments:
      <version>             application version
      <appId>               ID of the application to be marked as stable
    
    optional arguments:
      -h, --help            show this help message and exit
    
    connection:
      -H <host>, --host <host>
                            server host
      -u <user>             user alias from settings or email
      -p <password>         user password
    


- **remove**:

  .. code-block:: text

    usage: genestack-application-manager remove [-h] [-H <host>] [-u <user>] [-p <password>]
                               <version> <appId> [<appId> ...]
    
    Remove a specific version of an application.
    
    command arguments:
      <version>             application version
      <appId>               identifier of the application to remove
    
    optional arguments:
      -h, --help            show this help message and exit
    
    connection:
      -H <host>, --host <host>
                            server host
      -u <user>             user alias from settings or email
      -p <password>         user password
    


- **stable**:

  .. code-block:: text

    usage: genestack-application-manager stable [-h] [-H <host>] [-u <user>] [-p <password>]
                               [-S <scope>]
                               <version> <appId> [<appId> ...]
    
    Mark applications with the specified version as stable.
    
    command arguments:
      <version>             applications version or '-' (minus sign) to remove
                            stable version
      <appId>               ID of the application to be marked as stable
      -S <scope>, --scope <scope>
                            scope in which the application will be stable (default
                            is 'user'): session | system | user
    
    optional arguments:
      -h, --help            show this help message and exit
    
    connection:
      -H <host>, --host <host>
                            server host
      -u <user>             user alias from settings or email
      -p <password>         user password
    


- **versions**:

  .. code-block:: text

    usage: genestack-application-manager versions [-h] [-H <host>] [-u <user>] [-p <password>] [-s]
                                 [-o]
                                 <appId>
    
    Show information about available applications.
    
    command arguments:
      -s                    display stable scopes in output (S: System, U: User,
                            E: sEssion)
      -o                    show only versions owned by current user
      <appId>               application identifier to show versions
    
    optional arguments:
      -h, --help            show this help message and exit
    
    connection:
      -H <host>, --host <host>
                            server host
      -u <user>             user alias from settings or email
      -p <password>         user password
    



Useful commands
---------------

If ``-u`` is not specified default user is used. User need to have rights to reproduce this commands.

Installing applications
^^^^^^^^^^^^^^^^^^^^^^^

- If you want to install new JAR file with applications, you simply execute::

        genestack-application-manager -r root install my-version path/to/file.jar


- If you have your JAR file inside some folder, and this is the only JAR file inside the folder and all its subfolders,
  then you can specify path to the folder instead for the full path to JAR file

  **NOTE**: when you specify folder path instead of JAR path, then the folder and all its subfolders are searched for JAR files; if only one JAR is found — it is installed, otherwise error is reported.
  ::

    genestack-application-manager -r root install my-version path/to/folder


- If you want to install new JAR and also mark all applications from that JAR as stable for your current user, then you can use ``-s`` key of ``install`` command (application manager has default stable scope "user")::

    genestack-application-manager install -s my-version path/to/file.jar

- If you want to make applications globally stable, you should specify ``system`` scope with ``-S`` key::

    genestack-application-manager install -s -S system my-version path/to/file.jar

- Otherwise, you can use ``stable`` command after installing JAR file::

    JAR=path/to/file.jar
    VERSION=my-version
    genestack-application-manager install $VERSION $JAR
    for A in $(genestack-application-manager info $JAR | tail -n+3); do
        genestack-application-manager stable -S system $VERSION $A
    done

- If you want to reinstall your applications later with the same version (no matter if this version was marked as stable),
  you can simply use ``-o`` key of ``install`` command

  **NOTE:** key ``-o`` works exactly as removing old version before uploading new one, so there are two things to keep in mind:
  - key ``-o`` can be used to overwrite only your versions, because you cannot overwrite or remove versions uploaded by other users;
  - key ``-o`` removes global stable mark, so if you overwrite globally stable version, then after that no globally stable version will be available.
  ::

    genestack-application-manager install -o my-version path/to/file.jar

- Sometimes you need to upload JAR file with many applications and mark as stable only one application from that JAR.
  In this case you should use ``install`` and ``stable`` commands::

    genestack-application-manager install my-version path/to/file.jar
    genestack-application-manager stable my-version vendor/appIdFromJarFile

Removing all your applications
------------------------------

- If you want to remove all your applications, just enter the following command::

    for A in $(genestack-application-manager applications); do
        for V in $(genestack-application-manager versions -o $A); do
            genestack-application-manager remove $V $A
        done
    done

- If you want to remove only those your applications that were loaded from specific JAR file, then::

    JAR=path/to/file.jar
    for A in $(genestack-application-manager info $JAR | tail -n+3); do
        for V in $(genestack-application-manager versions -o $A); do
            genestack-application-manager remove $V $A
        done
    done


