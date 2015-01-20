Local setup
===========


Available hosts
---------------
::

   localhost:8080
   platform.genestack.org
   internal-dev.genestack.com

Setup users for local installation
----------------------------------

To use local system installation add users via `genestack-user-setup.py add`::

    root
        root@genestack.com
        localhost:8080
        pwdRoot

    public
        public@genestack.com
        localhost:8080
        pwdPublic

    tester
        tester@genestack.com
        localhost:8080
        pwdTester123

Make tester default user. `genestack-user-setup.py default tester`


