import logging
from typing import Any

from fastapi import APIRouter, Depends

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.maintenance.model import MaintenanceDTO
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
    def get_maintenance_status(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> MaintenanceDTO:
        request_params = RequestParameters(user=current_user)
        return service.get_maintenance_status(request_params)

    @bp.post("/core/maintenance")
    def set_maintenance_status(
        maintenance: MaintenanceDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        request_params = RequestParameters(user=current_user)
        return service.set_maintenance_status(maintenance, request_params)

    return bp
