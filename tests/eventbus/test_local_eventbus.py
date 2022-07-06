from antarest.core.interfaces.eventbus import Event, EventType
from antarest.eventbus.business.local_eventbus import LocalEventBus


def test_lifecycle():
    eventbus = LocalEventBus()
    event = Event(type=EventType.STUDY_EDITED, payload="foo")
    eventbus.push_event(event)
    assert eventbus.get_events() == [event]
    eventbus.clear_events()
    assert len(eventbus.get_events()) == 0
