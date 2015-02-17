from genestack import get_connection, make_connection_parser

parser = make_connection_parser()  # return instance of argparse.ArgumentParser
parser.add_argument('-c', '--unicorn',  dest='unicorn', action='store_true', help='Set if you have unicorn.')
args = parser.parse_args()
connection = get_connection(args)
if args.unicorn:
    print connection.whoami(), 'has unicorn!'
else:
    print connection.whoami(), 'does not have unicorn.'