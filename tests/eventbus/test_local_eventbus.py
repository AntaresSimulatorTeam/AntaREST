from antarest.core.interfaces.eventbus import Event, EventType
from antarest.core.model import PermissionInfo, PublicMode
from antarest.eventbus.business.local_eventbus import LocalEventBus


def test_lifecycle():
    eventbus = LocalEventBus()
    event = Event(
        type=EventType.STUDY_EDITED,
        payload="foo",
        permissions=PermissionInfo(public_mode=PublicMode.READ),
    )
    eventbus.push_event(event)
    assert eventbus.get_events() == [event]
    eventbus.clear_events()
    assert len(eventbus.get_events()) == 0
