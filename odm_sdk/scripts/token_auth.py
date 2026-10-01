# -*- coding: utf-8 -*-
# Command line arguments and HTTP headers shared by the scripts that call ODM REST API:
# the host and the authentication by either an API token or an access token.

from __future__ import print_function, unicode_literals

import argparse
import sys

from odm_sdk.scripts.utils import colored, RED

DEFAULT_HOST = "https://odm-demos.genestack.com"

_TOKEN_CONFLICT_MESSAGE = ("only one token can be specified. "
                           "Please choose the authentication method: "
                           "through the Access Token or "
                           "through the Genestack-API-token")


# pylint: disable-next=protected-access
class _SingletonAction(argparse._StoreAction):
    """ Ensures that only one argument is passed """

    def __init__(self, mutually_exclusive, err_msg, *args, **kwargs):
        super(_SingletonAction, self).__init__(*args, **kwargs)
        self.err_msg = err_msg
        self.mutually_exclusive = mutually_exclusive

    def __call__(self, parser_, namespace, values, option_string=None):
        already_defined = any(getattr(namespace, v) is not None
                              for v in self.mutually_exclusive)
        if already_defined:
            raise argparse.ArgumentError(self, self.err_msg)
        setattr(namespace, self.dest, values)


# pylint: disable-next=protected-access
class _StoreServerName(argparse._StoreAction):
    """ Ensures that server name is not ended wit `/` """

    def __call__(self, parser_, namespace, values, option_string=None):
        setattr(namespace, self.dest, values.rstrip("/"))


def prevent_redundant_parameters(mutually_exclusive, err_msg):
    return lambda *args, **kwargs: _SingletonAction(mutually_exclusive, err_msg, *args, **kwargs)


def add_host_argument(parser, help_text):
    """Adds the host option to ``parser``. The value is stored in ``SERVER``."""
    parser.add_argument("-H", "--host", "-srv", "--server",
                        action=_StoreServerName,
                        const=DEFAULT_HOST,
                        default=DEFAULT_HOST,
                        nargs="?",
                        dest="SERVER",
                        help=help_text)


def add_token_arguments(parser):
    """Adds the mutually exclusive API token and access token options. Values are stored in
    ``API_TOKEN`` and ``ACCESS_TOKEN``."""
    parser.add_argument("-t", "--token",
                        action=prevent_redundant_parameters(("API_TOKEN", "ACCESS_TOKEN"),
                                                            _TOKEN_CONFLICT_MESSAGE),
                        dest="API_TOKEN",
                        nargs="?",
                        help="API_TOKEN")
    parser.add_argument("-at", "--access-token",
                        action=prevent_redundant_parameters(("API_TOKEN", "ACCESS_TOKEN"),
                                                            _TOKEN_CONFLICT_MESSAGE),
                        dest="ACCESS_TOKEN",
                        nargs="?",
                        help="ACCESS_TOKEN")


class Headers(dict):
    """Derives http-headers from arguments"""

    def __init__(self, args):
        super(dict, self).__init__()
        self["Genestack-API-Token"] = args.API_TOKEN
        self["Authorization"] = "Bearer {}".format(args.ACCESS_TOKEN) if args.ACCESS_TOKEN else None
        self["Accept"] = "application/json"
        self["Content-Type"] = "application/json"
        self._validate()

    def _validate(self):
        if self["Genestack-API-Token"] and self["Authorization"]:
            print(colored("Please provide a Genestack-Api-Token or an Access Token but not both", RED),
                  file=sys.stderr)
            sys.exit(1)
        if self["Genestack-API-Token"] is None and self["Authorization"] is None:
            print(colored("Please provide a Genestack-Api-Token or an Access Token", RED),
                  file=sys.stderr)
            sys.exit(1)

    def __getstate__(self):
        return self
