Setup
#####

Install
*******

- clone repo or download and unpack archive
- navigate to repository folder or unpacked folder
- install

- install via pip:

  - ``sudo pip install .``

- install manually:

  - ``sudo python setup.py install``
  - install keyring https://pypi.python.org/pypi/keyring

- to test installation: ``python -c 'import genestack; print genestack.__version__'``

- init user

  - create genestack account if you don't have one.
  - run init script ``genestack-user-setup.py init``.
  - input email and password for genestack server. If you email and password match setup is finished.
  - to check result ``genestack-user-setup.py list``

  See more information in :ref:`user_config`.

Reinstall
---------

- ``sudo python setup.py install`` or ``sudo pip install -U .``


.. _user_config:

User config
***********

User config allow to store credentials for your account on local machine to establish :doc:`examples/connection` to server.

Password stored in system secure storage (See https://pypi.python.org/pypi/keyring for more information).
If system storage in not accessible it will ask your permission to store password as plain text.

This data is not synchronized with server, if you change password on server you need to change it here too.


Setup additional users
----------------------

If you have more then one account on genestack platform you may want to add other users.

Each user need to have alias, email, host and password. There is not limitation to number of aliases
you can create couple of them to one account.  To add user execute ``genestack-user-setup.py add``


To use script with other user add ``-u <alias>`` to you command.

There is alternative way to specify user by adding all its credentials to command line::

   -u <email> -H <host> -p <passwod>

If email or password omitted script will ask them in interactive mode.
**NOTE**: interactive mode work only if you run script in terminal.

See more info about possible commands: :doc:`scripts/genestack-user-setup`
