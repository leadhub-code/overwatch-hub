from overwatch_hub.util.observer import ObservableEvent


def test_observable_event_fire_with_no_subscribers():
    event = ObservableEvent()
    event.fire(None)


def test_observable_event_subscribe_and_file():
    log = []
    event = ObservableEvent()
    event.subscribe(lambda params: log.append((1, params)))
    event.subscribe(lambda params: log.append((2, params)))
    event.fire('foo')
    assert log == [
        (1, 'foo'),
        (2, 'foo'),
    ]
