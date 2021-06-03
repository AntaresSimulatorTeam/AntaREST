from fastapi import FastAPI

from antarest.common.config import Config
from antarest.common.interfaces.eventbus import IEventBus
from antarest.eventbus.business.local_eventbus import LocalEventBus
from antarest.eventbus.business.redis_eventbus import RedisEventBus
from antarest.eventbus.service import EventBusService
from antarest.eventbus.web import configure_websockets


def build_eventbus(
    application: FastAPI,
    config: Config,
    autostart: bool = True,
) -> IEventBus:

    redis_conf = config.eventbus.redis
    eventbus = EventBusService(
        RedisEventBus(redis_conf)
        if redis_conf is not None
        else LocalEventBus(),
        autostart,
    )

    configure_websockets(application, config, eventbus)
    return eventbus
