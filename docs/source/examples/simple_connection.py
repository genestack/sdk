from genestack import get_connection

connection = get_connection()
print connection.whoami()