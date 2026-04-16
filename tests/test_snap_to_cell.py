from grid import register, build_widget


def test_build_widget_passes_cfg():
    cfg = {"type": "cfg_test_widget", "title": "Test"}

    @register
    class CfgTestWidget:
        WIDGET_TYPE = "cfg_test_widget"
        def __init__(self, cfg, id):
            self.cfg = cfg
            self.id = id

    instance = build_widget(cfg)
    assert instance.cfg is cfg


def test_build_widget_generates_id():
    cfg = {"type": "id_test_widget"}

    @register
    class IdTestWidget:
        WIDGET_TYPE = "id_test_widget"
        def __init__(self, cfg, id):
            self.cfg = cfg
            self.id = id

    instance = build_widget(cfg)
    assert instance.id is not None
