from flask import Flask

from antarest.common.config import Config
from antarest.common.interfaces.eventbus import IEventBus
from antarest.eventbus.business.local_eventbus import LocalEventBus
from antarest.eventbus.business.redis_eventbus import RedisEventBus
from antarest.eventbus.config import get_config
from antarest.eventbus.service import EventBusService
from antarest.eventbus.web import configure_websockets


def build_eventbus(
    application: Flask,
    config: Config,
    autostart: bool = True,
) -> IEventBus:

    event_bus_config = get_config(config)

    eventbus = EventBusService(
        RedisEventBus(event_bus_config.redis)
        if event_bus_config is not None and event_bus_config.redis is not None
        else LocalEventBus(),
        autostart,
    )

    configure_websockets(application, config, eventbus)
    return eventbus
