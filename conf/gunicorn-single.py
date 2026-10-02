"""
Configuration for notifying prometheus exporter that workers have been killed.
"""

from prometheus_client import multiprocess


def child_exit(server, worker):
    """
    Notify prometheus that this worker has been stopped
    """
    multiprocess.mark_process_dead(worker.pid)

capture_output = True

loglevel = "info"
errorlog = "/logs/gunicorn.error.log"
accesslog = "/logs/gunicorn.access.log"
preload_app = False