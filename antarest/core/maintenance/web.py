import logging
from typing import Any

from fastapi import APIRouter, Body, Depends

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.maintenance.service import MaintenanceService
from antarest.core.requests import RequestParameters
from antarest.login.auth import Auth

logger = logging.getLogger(__name__)


def create_maintenance_api(
    service: MaintenanceService, config: Config
) -> APIRouter:
    """
    Endpoints login implementation
    Args:
        service: login facade service
        config: server config

    Returns:

    """
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)

    @bp.get("/core/maintenance", include_in_schema=False)
    def get_maintenance_status() -> bool:
        return service.get_maintenance_status()

    @bp.post("/core/maintenance", include_in_schema=False)
    def set_maintenance_status(
        maintenance: bool,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        request_params = RequestParameters(user=current_user)
        return service.set_maintenance_status(maintenance, request_params)

    @bp.get("/core/maintenance/message", include_in_schema=False)
    def get_message_info() -> str:
        return service.get_message_info()

    @bp.post("/core/maintenance/message", include_in_schema=False)
    def set_message_info(
        message: str = Body(default=""),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        request_params = RequestParameters(user=current_user)
        return service.set_message_info(message, request_params)

    return bp
