import logging
from typing import Any

from fastapi import APIRouter, Depends, Body

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.maintenance.model import MaintenanceMode
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

    @bp.get("/core/maintenance")
    def get_maintenance_status() -> bool:
        return service.get_maintenance_status()

    @bp.post("/core/maintenance")
    def set_maintenance_status(
        maintenance: bool,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        request_params = RequestParameters(user=current_user)
        return service.set_maintenance_status(maintenance, request_params)

    @bp.get("/core/maintenance/message")
    def get_message_info() -> str:
        return service.get_message_info()

    @bp.post("/core/maintenance/message")
    def set_message_info(
        message: str = Body(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        request_params = RequestParameters(user=current_user)
        return service.set_message_info(message, request_params)

    return bp
