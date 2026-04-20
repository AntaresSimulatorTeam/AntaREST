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
    Notify prometheus that this worker stops
    """
    multiprocess.mark_process_dead(worker.pid)


# Below: logic to assign a unique identifier to each worker, from 1 to workers count
_worker_ids = [0 for _ in range(workers)]


def pre_fork(server, worker):
    # Runs in master — assign a free slot to this worker's PID
    for i in range(1, workers + 1):
        if _worker_ids[i] == 0:
            _worker_ids[i] = worker.pid
            break


def post_fork(server, worker):
    # Runs in child — find our PID in the inherited array and read our slot
    for i in range(1, workers + 1):
        if _worker_ids[i] == worker.pid:
            os.environ["ANTAREST_WORKER_ID"] = str(i)
            break


def worker_exit(server, worker):
    # Runs in master — release the slot
    for i in range(1, workers + 1):
        if _worker_ids[i] == worker.pid:
            _worker_ids[i] = 0
            break
