#!/usr/bin/env python3

#
# Copyright (c) 2011-2021 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

import sys
import time
from odm_sdk import get_connection

TASKMANAGER_ID = "genestack/taskmanager"
TIMEOUT_IN_SECONDS = 3 * 60 * 60
SLEEP_TIMEOUT_IN_SECONDS = 30

# The number of running tasks must be 0 several times in row to get a success
NO_RUNNING_TASK_ITERATION_LIMIT = 3


def main():
    connection = get_connection()
    task_app = connection.application(TASKMANAGER_ID)

    no_running_task_check_iteration = 1
    start_time = time.time()

    while time.time() - start_time < TIMEOUT_IN_SECONDS:
        time.sleep(SLEEP_TIMEOUT_IN_SECONDS)
        tasks = task_app.invoke('getRecentTaskCountsByStatus', 20)
        print(
            f'Check for no running tasks iteration: {no_running_task_check_iteration} out of {NO_RUNNING_TASK_ITERATION_LIMIT}\n'
            f'Running tasks: {tasks["running"]}\n'
            f'Queued tasks: {tasks["queued"]}'
        )

        if tasks["running"] == 0:
            no_running_task_check_iteration += 1
        else:
            no_running_task_check_iteration = 1
            continue

        if no_running_task_check_iteration > NO_RUNNING_TASK_ITERATION_LIMIT:
            print("All tasks complete.")
            sys.exit(0)

    print("Waiting timeout exceeded.")
    sys.exit(1)


if __name__ == "__main__":
    main()
