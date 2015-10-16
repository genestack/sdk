
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
    



Usage examples
--------------

If ``-u`` is not specified, the default user is used.

Installing applications
^^^^^^^^^^^^^^^^^^^^^^^

- If you want to install a new JAR file containing applications, simply type::

        genestack-application-manager install my-version path/to/file.jar


- If your JAR file is located in a specific folder, and this folder and its subfolders do not contain any other JAR file,
  you can specify the path to the folder instead of the full path to the JAR file. In that case, the folder and its subfolders
  will be searched for JAR files. If no JAR file or more than one JAR file is found, an error is returned.

    genestack-application-manager install my-version path/to/folder


- If you want to upload a JAR file and also mark all the applications inside it as stable for your current user, you can use ``-s`` option of the ``install`` command (the default scope for marking applications as stable is ``user``)::

    genestack-application-manager install -s my-version path/to/file.jar

- If you want to make an applications stable only for your session, you should specify ``-S session``::

    genestack-application-manager install -s -S session my-version path/to/file.jar

- Otherwise, you can use the ``stable`` command after installing the JAR file::

    JAR=path/to/file.jar
    VERSION=my-version
    genestack-application-manager install $VERSION $JAR
    for A in $(genestack-application-manager info $JAR | tail -n+3); do
        genestack-application-manager stable -S system $VERSION $A
    done

- If you want to reinstall your applications later with the same version (whether or not that version was marked as stable),
  you can simply use the ``-o`` option for the ``install`` command

  This option works exactly as removing the old version before uploading the new one, so there are two things to keep in mind:
  -  ``-o`` can be used to overwrite only your versions, because you cannot overwrite or remove versions uploaded by other users;
  -  ``-o`` removes the global stable mark, so if you overwrite a globally stable version, then after that no globally stable version will be available on the system


    genestack-application-manager install -o my-version path/to/file.jar

- Sometimes you may want to upload a JAR file with many applications, and only mark as stable one of them.
  In this case you should use the ``install`` and ``stable`` commands::

    genestack-application-manager install my-version path/to/file.jar
    genestack-application-manager stable my-version vendor/appIdFromJarFile

Removing all of your applications
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- If you want to remove all your applications, you can use the following bash script::

    for A in $(genestack-application-manager applications); do
        for V in $(genestack-application-manager versions -o $A); do
            genestack-application-manager remove $V $A
        done
    done

- And if you want to remove only those your applications that were loaded from a specific JAR file, then::

    JAR=path/to/file.jar
    for A in $(genestack-application-manager info $JAR | tail -n+3); do
        for V in $(genestack-application-manager versions -o $A); do
            genestack-application-manager remove $V $A
        done
    done


