# simple connection
from genestack import get_connection

connection = get_connection()
print connection.whoami()


# connection with args
from genestack import get_connection, make_connection_parser

# create instance of argparse.ArgumentParser with predefined arguments for connection
parser = make_connection_parser()
parser.add_argument('-c', '--unicorn',  dest='unicorn', action='store_true', help='Set if you have unicorn.')
args = parser.parse_args()
connection = get_connection(args)
if args.unicorn:
    print connection.whoami(), 'has unicorn!'
else:
    print connection.whoami(), 'does not have unicorn.'


# manual connection
from genestack import Connection

# crease connection object for server
connection = Connection('https://platform.genestack.org/endpoint')

# login as user: 'user@email.com' with password 'password'
connection.login('user@email.com', 'password')
print connection.whoami()