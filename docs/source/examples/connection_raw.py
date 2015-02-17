from genestack import Connection

# crease connection object for server
connection = Connection('https://platform.genestack.org/endpoint')

# login as user: 'user@email.com' with password 'password'
connection.login('user@email.com', 'password')
print connection.whoami()