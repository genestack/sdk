Local setup
===========

Setup users for local installation
----------------------------------

- Find config file location  ``genestack-user-setup.py path''

- Replace it with next one.  (or merge ro your settings)::

     <genestack>
        <users>
            <user>
                <alias>public</alias>
                <email>public@genestack.com</email>
                <host>localhost:8080</host>
                <password>pwdPublic</password>
            </user>
            <user>
                <alias>root</alias>
                <email>root@genestack.com</email>
                <host>localhost:8080</host>
                <password>pwdRoot</password>
            </user>
            <user>
                <alias>tester</alias>
                <email>tester@genestack.com</email>
                <host>localhost:8080</host>
                <password>pwdTester123</password>
            </user>
        </users>
        <default_user>tester</default_user>
    </genestack>

- installAll -db expect to have ``tester`` as default user. To set it use: ``genestack-user-setup.py default tester``

Available hosts
---------------
::

   localhost:8080
   platform.genestack.org
   internal-dev.genestack.com
