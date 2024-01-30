# coding=utf-8
import sys


class Color(object):
    """
    Class that contains constants for coloring the console output.
    """
    BLUE = 34
    GREEN = 32
    RED = 31


def colored(message, color):
    """
    Format the provided message with the given color if the standard output points to the console.
    Otherwise the message is returned as-is.

    :param message: text to format
    :type message: str
    :param color: color of the text (see :class:`format.Color`)
    :type color: int
    :return: str
    """
    if sys.platform == 'win32' or not sys.stdout.isatty():
        return message
    return '\033[%dm%s\033[0m' % (color, message)


def print_result(accession, name, type_name, started=False):
    """
    Print information about a created file using the following format:

    ``Created <type_name> <accession> / <name>``

    :param accession: accession of the created file
    :type accession: str
    :param name: name of the created file
    :type name: str
    :param type_name: type of the created file
    :type type_name: str
    :param started: if *True* the printed message will start with `Created and started`.
           This parameter is useful to indicate that the created file has also started initializing.
    """
    print('%s %s %s / %s' % (
        'Created and started' if started else 'Created',
        type_name,
        colored(accession, Color.GREEN),
        colored(name, Color.BLUE)
    ))
