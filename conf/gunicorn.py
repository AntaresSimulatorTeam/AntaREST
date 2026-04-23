# Reference: https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py

import multiprocessing
import os

from prometheus_client import multiprocess

bind = "0.0.0.0:5000"

"""
Gunicorn relies on the operating system to provide all of the load balancing
when handling requests. Generally we recommend (2 x $num_cores) + 1
as the number of workers to start off with. While not overly scientific,
the formula is based on the assumption that for a given core,
one worker will be reading or writing from the socket
while the other worker is processing a request.
https://docs.gunicorn.org/en/stable/design.html#how-many-workers
"""

workers = os.getenv("GUNICORN_WORKERS")
if workers == "ALL_AVAILABLE" or workers is None:
    workers = multiprocessing.cpu_count() * 2 + 1
else:
    workers = int(workers)

timeout = 10 * 60  # 10 minutes
keepalive = 24 * 60 * 60  # 1 day

capture_output = True

loglevel = "info"
errorlog = "-"
accesslog = "-"
preload_app = False


def child_exit(server, worker):
    """
    Notify prometheus that this worker stops, and release its ID slot.
    Runs in master process.
    """
    multiprocess.mark_process_dead(worker.pid)
    worker_id = getattr(worker, "_antarest_worker_id", None)
    if worker_id is not None:
        _taken_worker_ids.discard(worker_id)


# Below: logic to assign a unique identifier to each worker, from 1 to workers count.
_taken_worker_ids: set[int] = set()


def pre_fork(server, worker):
    # Runs in master before fork — find a free slot and attach it to the worker object.
    # worker.pid is not yet set at this point, so we store the slot on the worker itself.
    for i in range(1, workers + 1):
        if i not in _taken_worker_ids:
            _taken_worker_ids.add(i)
            worker._antarest_worker_id = i
            break


def post_fork(server, worker):
    # Runs in child after fork — export the pre-assigned slot as an env var so that
    # antarest.globals.ANTAREST_WORKER_ID (read at import time) picks it up.
    os.environ["ANTAREST_WORKER_ID"] = str(getattr(worker, "_antarest_worker_id", 0))
