def test_session_status_widget_type():
    from widgets.session_status import SessionStatusWidget
    assert SessionStatusWidget.WIDGET_TYPE == "session_status"


def test_session_status_renders_no_data():
    from widgets.session_status import SessionStatusWidget
    w = SessionStatusWidget(cfg={})
    w.data = {}
    result = w.render_content()
    assert "No session" in result


def test_session_status_renders_state():
    from widgets.session_status import SessionStatusWidget
    w = SessionStatusWidget(cfg={})
    w.data = {"session": {"claude_state": "running", "last_tool": "Read", "idle_since": ""}}
    result = w.render_content()
    assert "running" in result
    assert "Read" in result


def test_token_usage_widget_type():
    from widgets.token_usage import TokenUsageWidget
    assert TokenUsageWidget.WIDGET_TYPE == "token_usage"


def test_token_usage_renders_no_data():
    from widgets.token_usage import TokenUsageWidget
    w = TokenUsageWidget(cfg={})
    w.data = {}
    result = w.render_content()
    assert "No data" in result


def test_token_usage_renders_counts():
    from widgets.token_usage import TokenUsageWidget
    w = TokenUsageWidget(cfg={})
    w.data = {"session": {"tokens_input": 1000, "tokens_output": 500, "tokens_cache_read": 200}}
    result = w.render_content()
    assert "1,000" in result
    assert "500" in result


def test_tool_log_widget_type():
    from widgets.tool_log import ToolLogWidget
    assert ToolLogWidget.WIDGET_TYPE == "tool_log"


def test_tool_log_renders_no_data():
    from widgets.tool_log import ToolLogWidget
    w = ToolLogWidget(cfg={})
    w.data = {}
    assert "No tool calls" in w.render_content()


def test_tool_log_renders_last_entries():
    from widgets.tool_log import ToolLogWidget
    w = ToolLogWidget(cfg={})
    w.data = {"tools": [
        {"tool": "Read", "at": "2026-04-12T10:00:01"},
        {"tool": "Write", "at": "2026-04-12T10:00:02"},
    ]}
    result = w.render_content()
    assert "Read" in result
    assert "Write" in result


def test_session_log_widget_type():
    from widgets.session_log import SessionLogWidget
    assert SessionLogWidget.WIDGET_TYPE == "session_log"


def test_session_log_renders_activity():
    from widgets.session_log import SessionLogWidget
    w = SessionLogWidget(cfg={})
    w.data = {"tools": [{"tool": "Grep", "at": "2026-04-12T10:00:01"}]}
    result = w.render_content()
    assert "Grep" in result


def test_diff_preview_widget_type():
    from widgets.diff_preview import DiffPreviewWidget
    assert DiffPreviewWidget.WIDGET_TYPE == "diff_preview"


def test_diff_preview_no_data():
    from widgets.diff_preview import DiffPreviewWidget
    w = DiffPreviewWidget(cfg={})
    w.data = {}
    assert "No" in w.render_content()


def test_diff_preview_shows_last_write():
    from widgets.diff_preview import DiffPreviewWidget
    w = DiffPreviewWidget(cfg={})
    w.data = {"tools": [
        {"tool": "Write", "input": {"file_path": "/tmp/foo.py"}, "result": "+added line\n-removed line"}
    ]}
    result = w.render_content()
    assert "foo.py" in result


def test_session_timer_widget_type():
    from widgets.session_timer import SessionTimerWidget
    assert SessionTimerWidget.WIDGET_TYPE == "session_timer"


def test_session_timer_render_shows_time():
    import time
    from widgets.session_timer import SessionTimerWidget
    w = SessionTimerWidget(cfg={})
    w._start = time.time() - 65  # 1m 5s
    result = w.render_content()
    assert "01:" in result
