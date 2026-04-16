from grid import WIDGET_REGISTRY, register, build_widget


def test_register_adds_to_registry():
    @register
    class DummyWidget:
        WIDGET_TYPE = "dummy_register"

    assert "dummy_register" in WIDGET_REGISTRY
    assert WIDGET_REGISTRY["dummy_register"] is DummyWidget


def test_build_widget_known_type():
    @register
    class KnownWidget:
        WIDGET_TYPE = "known_widget"
        def __init__(self, cfg, id):
            self.cfg = cfg
            self.id = id

    instance = build_widget({"type": "known_widget"})
    assert isinstance(instance, KnownWidget)


def test_build_widget_unknown_type():
    instance = build_widget({"type": "nonexistent"})
    assert instance.WIDGET_TYPE == "nonexistent"
