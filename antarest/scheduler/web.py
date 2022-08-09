from fastapi import APIRouter

from antarest.core.config import Config
from antarest.login.auth import Auth
from antarest.scheduler.service import SchedulerService


def create_scheduler_api(
    service: SchedulerService, config: Config
) -> APIRouter:
    """
    Endpoints for scheduler service
    Args:
        service: scheduler service
        config: server config

    Returns:

    """
    bp = APIRouter(prefix="/v1")

    auth = Auth(config)

    return bp
