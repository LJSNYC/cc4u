import time
import pytest


def test_uptime_widget_type():
    from widgets.uptime import UptimeWidget
    assert UptimeWidget.WIDGET_TYPE == "uptime"


def test_uptime_render_returns_time_string(monkeypatch):
    from widgets.uptime import UptimeWidget
    w = UptimeWidget(cfg={})
    w._start = time.time() - 3661  # 1h 1m 1s ago
    result = w.render_content()
    assert "01:01" in result


def test_network_widget_type():
    from widgets.network import NetworkWidget
    assert NetworkWidget.WIDGET_TYPE == "network"


def test_network_render_returns_string():
    from widgets.network import NetworkWidget
    w = NetworkWidget(cfg={})
    result = w.render_content()
    assert isinstance(result, str)
    assert len(result) > 0


def test_file_watcher_widget_type():
    from widgets.file_watcher import FileWatcherWidget
    assert FileWatcherWidget.WIDGET_TYPE == "file_watcher"


def test_file_watcher_shows_not_configured_when_no_path():
    from widgets.file_watcher import FileWatcherWidget
    w = FileWatcherWidget(cfg={})
    result = w.render_content()
    assert "No watch_path" in result


def test_file_watcher_shows_not_found_for_bad_path():
    from widgets.file_watcher import FileWatcherWidget
    w = FileWatcherWidget(cfg={"watch_path": "/nonexistent/path/file.txt"})
    result = w.render_content()
    assert "Not found" in result


def test_dir_tree_widget_type():
    from widgets.dir_tree import DirTreeWidget
    assert DirTreeWidget.WIDGET_TYPE == "dir_tree"


def test_dir_tree_render_returns_string():
    from widgets.dir_tree import DirTreeWidget
    w = DirTreeWidget(cfg={})
    result = w.render_content()
    assert isinstance(result, str)
    assert len(result) > 0
