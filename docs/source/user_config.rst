User config
###########

User config needed to store user connection data.

First setup
***********

- Create genestack account if you don't have one.

- Run init script ``genestack-user-setup.py init``.

- Input email and password.
   If you email and password match setup is finished.

   Script store password in system secure storage (See https://pypi.python.org/pypi/keyring for more information).
   If system storage in not accessible it will ask your permission to store password as plain text.

This is will be you default user.


Setup additional users
**********************

If you have more then one account on genestack platforms you may want to add other users.

Each user need to have alias, email, host and password.

To use script with other user add ``-u <alias>`` to you command.

There is alternative way to specify user by adding all its credentials to command line::

   -u <email> -H <host> -p <passwod>

If email or password omited script will ask them in interactive mode.
**NOTE**: interactive mode work only if you run script in terminal.


