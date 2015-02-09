Setup
#####

Install
*******


Internal release
----------------

  - clone repo or download and unpack archive
  - navigate to root folder
  - install

    - install via pip:

      - ``sudo pip install .``

    - install manually:

      - ``sudo python setup.py install``
      - install keyring https://pypi.python.org/pypi/keyring

  - run ``genestack-user-setup.py init`` and input your login and password for dotorg

Reinstall
---------

 - ``sudo python setup.py install`` or ``sudo pip install -U .``


User config
***********

User config needed to store al data to establish connections.

First setup
-----------

- Create genestack account if you don't have one.

- Run init script ``genestack-user-setup.py init``.

- Input email and password.
   If you email and password match setup is finished.

   Password stored in system secure storage (See https://pypi.python.org/pypi/keyring for more information).
   If system storage in not accessible it will ask your permission to store password as plain text.

This is will be you default user.  See more info in :doc:`examples/connection`


Setup additional users
----------------------

If you have more then one account on genestack platforms you may want to add other users.

Each user need to have alias, email, host and password.

To use script with other user add ``-u <alias>`` to you command.

There is alternative way to specify user by adding all its credentials to command line::

   -u <email> -H <host> -p <passwod>

If email or password omitted script will ask them in interactive mode.
**NOTE**: interactive mode work only if you run script in terminal.

User setup script
-----------------

  :doc:`scripts/genestack-user-setup`
