from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine

from antarest.core.config import Config
from antarest.core.configdata.model import ConfigDataAppKeys
from antarest.core.interfaces.eventbus import Event, EventType
from antarest.core.jwt import DEFAULT_ADMIN_USER, JWTUser
from antarest.core.maintenance.model import MaintenanceMode
from antarest.core.maintenance.repository import MaintenanceRepository
from antarest.core.maintenance.service import MaintenanceService
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.persistence import Base
from antarest.core.requests import RequestParameters, UserHasNotPermissionError
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware


def test_service_without_cache() -> MaintenanceService:
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    repo_mock = Mock(spec=MaintenanceRepository)
    cache = Mock()
    event_bus = Mock()
    cache.get.return_value = None
    normal_mode = MaintenanceMode.NORMAL_MODE.value
    maintenance_mode = MaintenanceMode.MAINTENANCE_MODE.value

    service = MaintenanceService(
        config=Config(), repository=repo_mock, event_bus=event_bus, cache=cache
    )

    # Get maintenance status (maintenance mode)
    repo_mock.get_maintenance_mode.return_value = maintenance_mode
    maintenance_status = service.get_maintenance_status(
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )
    cache.put.assert_called_with(
        ConfigDataAppKeys.MAINTENANCE_MODE.value,
        {"maintenance": maintenance_mode},
    )
    assert maintenance_status

    # Get maintenance status (normal mode)
    repo_mock.get_maintenance_mode.return_value = normal_mode
    maintenance_status = service.get_maintenance_status(
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )
    cache.put.assert_called_with(
        ConfigDataAppKeys.MAINTENANCE_MODE.value, {"maintenance": normal_mode}
    )
    assert not maintenance_status

    # Get maintenance status when status not found in cache and db
    repo_mock.get_maintenance_mode.return_value = None
    with pytest.raises(HTTPException):
        service.get_maintenance_status(
            request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
        )

    # Get message info
    ret_message = "Hey"
    repo_mock.get_message_info.return_value = ret_message
    message_info = service.get_message_info(
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )
    cache.put.assert_called_with(
        ConfigDataAppKeys.MESSAGE_INFO.value, {"message": ret_message}
    )
    assert message_info == ret_message

    # Get message info when status not found in cache and db
    repo_mock.get_message_info.return_value = None
    message_info = service.get_message_info(
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER)
    )
    assert message_info == ""

    # Set maintenance mode
    mode = True
    data = MaintenanceMode.to_str(mode)
    service.set_maintenance_status(
        data=mode, request_params=RequestParameters(user=DEFAULT_ADMIN_USER)
    )
    repo_mock.save_maintenance_mode.assert_called_with(0, data)
    cache.put.assert_called_with(
        ConfigDataAppKeys.MAINTENANCE_MODE.value, {"maintenance": data}
    )
    event_bus.push.assert_called_with(
        Event(
            type=EventType.MAINTENANCE_MODE,
            payload=mode,
            permissions=PermissionInfo(public_mode=PublicMode.READ),
        )
    )

    # Set message
    data = "Hey"
    service.set_message_info(
        data=data, request_params=RequestParameters(user=DEFAULT_ADMIN_USER)
    )
    repo_mock.save_message_info.assert_called_with(0, data)
    cache.put.assert_called_with(
        ConfigDataAppKeys.MESSAGE_INFO.value, {"message": data}
    )
    event_bus.push.assert_called_with(
        Event(
            type=EventType.MESSAGE_INFO,
            payload=data,
            permissions=PermissionInfo(public_mode=PublicMode.READ),
        )
    )

    # Set message with no admin permission
    not_admin_user = JWTUser(
        id=1,
        impersonator=1,
        type="users",
        groups=[],
    )
    with pytest.raises(UserHasNotPermissionError):
        service.set_message_info(
            data=data, request_params=RequestParameters(user=not_admin_user)
        )


def test_service_with_cache() -> MaintenanceService:
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    repo_mock = Mock(spec=MaintenanceRepository)
    cache = Mock()
    event_bus = Mock()

    normal_mode = MaintenanceMode.NORMAL_MODE.value
    maintenance_mode = MaintenanceMode.MAINTENANCE_MODE.value

    service = MaintenanceService(
        config=Config(), repository=repo_mock, event_bus=event_bus, cache=cache
    )

    # Get maintenance status (maintenance mode)
    cache.get.return_value = {"maintenance": maintenance_mode}
    maintenance_status = service.get_maintenance_status(
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )
    assert maintenance_status

    # Get maintenance status (normal mode)
    cache.get.return_value = {"maintenance": normal_mode}
    maintenance_status = service.get_maintenance_status(
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )
    assert not maintenance_status

    # Get message info
    ret_message = "Hey"
    cache.get.return_value = {"message": ret_message}
    message_info = service.get_message_info(
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )
    assert message_info == ret_message
