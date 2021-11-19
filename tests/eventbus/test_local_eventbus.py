from antarest.core.interfaces.eventbus import Event
from antarest.eventbus.business.local_eventbus import LocalEventBus


def test_lifecycle():
    eventbus = LocalEventBus()
    event = Event(type="test", payload="foo")
    eventbus.push_event(event)
    assert eventbus.get_events() == [event]
    eventbus.clear_events()
    assert len(eventbus.get_events()) == 0
