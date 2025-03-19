#!/usr/bin/env python3

import argparse
import sys
import time

import requests

EXPECTED_RESPONSE_CODE = 200
ALLOWED_WAIT_CYCLES = 120
TIMEOUT_IN_SECONDS = 10


def is_api_ready(odm_url):
    try:
        endpoint = '/frontend/endpoint/actuator/health'
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

    args = arg_parser.parse_args()

    wait_cycle = 0

    while wait_cycle < ALLOWED_WAIT_CYCLES:
        time.sleep(TIMEOUT_IN_SECONDS)
        if is_api_ready(args.odm_url):
            print(f'Host {args.odm_url} is ready!')
            sys.exit(0)
        else:
            wait_cycle += 1
            print(
                f'Iteration {wait_cycle}: {args.odm_url}'
                f'is not ready yet. Waiting another {TIMEOUT_IN_SECONDS} '
                'seconds to re-check.'
            )

    print('Waiting timeout exceeded. Host is not ready.')
    sys.exit(1)


if __name__ == "__main__":
    main()
