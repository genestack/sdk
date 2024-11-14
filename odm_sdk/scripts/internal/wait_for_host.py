#!/usr/bin/env python3

#
# Copyright (c) 2011-2022 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

import sys
import time
import requests
import argparse

EXPECTED_RESPONSE_CODE = 200
ALLOWED_WAIT_CYCLES = 120
TIMEOUT_IN_SECONDS = 10


def is_api_ready(odm_url, endpoint='frontend/health'):
    try:
        response = requests.get(
            url=f'{odm_url}/{endpoint}',
        )
        return response.status_code not in [404, 500]  #  we need to wait till endpoint is actually available
    except Exception:
        return False


def main():
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument(
        '--odm-url',
        type=str, help='host address', required=True
    )

    arg_parser.add_argument(
        '--odm-endpoint', default='frontend/health',
        type=str, help='(optional) specific endpoint to query', required=False
    )

    args = arg_parser.parse_args()

    wait_cycle = 0

    while wait_cycle < ALLOWED_WAIT_CYCLES:
        time.sleep(TIMEOUT_IN_SECONDS)
        if is_api_ready(args.odm_url, args.odm_endpoint):
            print(f'Host {args.odm_url}/{args.odm_endpoint} is ready!')
            sys.exit(0)
        else:
            wait_cycle += 1
            print(
                f'Iteration {wait_cycle}: {args.odm_url}/{args.odm_endpoint} '
                f'is not ready yet. Waiting another {TIMEOUT_IN_SECONDS} '
                'seconds to re-check.'
            )

    print('Waiting timeout exceeded. Host is not ready.')
    sys.exit(1)


if __name__ == "__main__":
    main()
