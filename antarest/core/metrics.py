import logging
import os
import time

import prometheus_client
from fastapi import FastAPI
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    make_asgi_app,
)
from prometheus_client import multiprocess
from starlette.requests import Request

from antarest.core.config import Config
from antarest.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


_PROMETHEUS_MULTIPROCESS_ENV_VAR = "PROMETHEUS_MULTIPROC_DIR"


def _add_metrics_middleware(
    application: FastAPI, registry: CollectorRegistry, worker_id: str
):
    """
    Registers an HTTP middleware to report metrics about requests count and duration
    """

    request_counter = Counter(
        "request_count",
        "App Request Count",
        ["worker_id", "method", "endpoint", "http_status"],
        registry=registry,
    )
    request_duration_histo = Histogram(
        "request_duration_seconds",
        "Request duration",
        ["worker_id", "method", "endpoint", "http_status"],
        registry=registry,
    )

    @application.middleware("http")
    async def add_metrics(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        if "route" in request.scope:
            request_path = (
                request.scope["root_path"] + request.scope["route"].path
            )
        else:
            request_path = request.url.path

        request_counter.labels(
            worker_id, request.method, request_path, response.status_code
        ).inc()
        request_duration_histo.labels(
            worker_id, request.method, request_path, response.status_code
        ).observe(process_time)
        return response


def add_metrics(application: FastAPI, config: Config) -> None:
    """
    If configured, adds "/metrics" endpoint to report metrics to prometheus.
    Also registers metrics for HTTP requests.
    """
    prometheus_config = config.metrics.prometheus
    if not prometheus_config:
        return

    if _PROMETHEUS_MULTIPROCESS_ENV_VAR not in os.environ:
        raise ConfigurationError(
            f"Environment variable {_PROMETHEUS_MULTIPROCESS_ENV_VAR} must be defined for use of prometheus in a multiprocess environment"
        )

    if prometheus_config.multiprocess:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        worker_id = os.environ["APP_WORKER_ID"]
    else:
        registry = prometheus_client.REGISTRY
        worker_id = "0"

    metrics_app = make_asgi_app(registry=registry)
    application.mount("/metrics", metrics_app)

    _add_metrics_middleware(application, registry, worker_id)
