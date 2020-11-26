# Reference: https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py

import multiprocessing
import os

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
if workers == "ALL_AVAILABLE":
    workers = multiprocessing.cpu_count() * 2 + 1

timeout = 3 * 60  # 3 minutes
keepalive = 24 * 60 * 60  # 1 day

capture_output = True

loglevel = "info"
errorlog = "-"
accesslog = "-"
