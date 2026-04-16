import json
import pytest


def test_quote_widget_type():
    from widgets.quote import QuoteWidget
    assert QuoteWidget.WIDGET_TYPE == "quote"


def test_quote_renders_fallback_when_no_file(tmp_path, monkeypatch):
    from widgets import quote as quote_mod
    monkeypatch.setattr(quote_mod, "QUOTES_FILE", str(tmp_path / "missing.json"))
    from widgets.quote import QuoteWidget
    w = QuoteWidget(cfg={})
    w._idx = 0
    w._quotes = []
    result = w.render_content()
    assert isinstance(result, str)


def test_quote_renders_first_quote(tmp_path, monkeypatch):
    from widgets import quote as quote_mod
    quotes_file = tmp_path / "quotes.json"
    quotes_file.write_text(json.dumps([{"text": "Ship it.", "author": "Everyone"}]))
    monkeypatch.setattr(quote_mod, "QUOTES_FILE", str(quotes_file))
    from widgets.quote import QuoteWidget
    w = QuoteWidget(cfg={})
    w._idx = 0
    w._quotes = [{"text": "Ship it.", "author": "Everyone"}]
    result = w.render_content()
    assert "Ship it." in result


def test_daily_goal_widget_type():
    from widgets.daily_goal import DailyGoalWidget
    assert DailyGoalWidget.WIDGET_TYPE == "daily_goal"


def test_daily_goal_shows_empty_when_no_goal(tmp_path, monkeypatch):
    import state
    monkeypatch.setattr(state, "WIDGET_DATA_DIR", str(tmp_path))
    from widgets.daily_goal import DailyGoalWidget
    w = DailyGoalWidget(cfg={})
    w._goal = ""
    result = w.render_content()
    assert "No goal" in result


def test_daily_goal_shows_goal_text(tmp_path, monkeypatch):
    import state
    monkeypatch.setattr(state, "WIDGET_DATA_DIR", str(tmp_path))
    from widgets.daily_goal import DailyGoalWidget
    w = DailyGoalWidget(cfg={})
    w._goal = "Ship Phase 2"
    result = w.render_content()
    assert "Ship Phase 2" in result


def test_checklist_widget_type():
    from widgets.checklist import ChecklistWidget
    assert ChecklistWidget.WIDGET_TYPE == "checklist"


def test_checklist_renders_empty():
    from widgets.checklist import ChecklistWidget
    w = ChecklistWidget(cfg={})
    w._items = []
    result = w.render_content()
    assert "empty" in result.lower() or "No items" in result


def test_checklist_renders_items():
    from widgets.checklist import ChecklistWidget
    w = ChecklistWidget(cfg={})
    w._items = [{"text": "Write tests", "done": True}, {"text": "Ship it", "done": False}]
    result = w.render_content()
    assert "Write tests" in result
    assert "Ship it" in result
    assert "✓" in result
    assert "○" in result


def test_task_tracker_widget_type():
    from widgets.task_tracker import TaskTrackerWidget
    assert TaskTrackerWidget.WIDGET_TYPE == "task_tracker"


def test_task_tracker_renders_tasks():
    from widgets.task_tracker import TaskTrackerWidget
    w = TaskTrackerWidget(cfg={})
    w._tasks = [{"text": "Build UI", "done": False}, {"text": "Deploy", "done": True}]
    result = w.render_content()
    assert "Build UI" in result
    assert "Deploy" in result


def test_quick_links_widget_type():
    from widgets.quick_links import QuickLinksWidget
    assert QuickLinksWidget.WIDGET_TYPE == "quick_links"


def test_quick_links_renders_links():
    from widgets.quick_links import QuickLinksWidget
    w = QuickLinksWidget(cfg={})
    w._links = [{"label": "GitHub", "url": "https://github.com"}]
    result = w.render_content()
    assert "GitHub" in result


def test_project_notes_widget_type():
    from widgets.project_notes import ProjectNotesWidget
    assert ProjectNotesWidget.WIDGET_TYPE == "project_notes"


def test_project_notes_renders_text(tmp_path, monkeypatch):
    import state
    monkeypatch.setattr(state, "WIDGET_DATA_DIR", str(tmp_path))
    from widgets.project_notes import ProjectNotesWidget
    w = ProjectNotesWidget(cfg={})
    w._notes = "hello world"
    result = w.render_content()
    assert "hello world" in result


def test_word_count_widget_type():
    from widgets.word_count import WordCountWidget
    assert WordCountWidget.WIDGET_TYPE == "word_count"


def test_word_count_no_path():
    from widgets.word_count import WordCountWidget
    w = WordCountWidget(cfg={})
    result = w.render_content()
    assert "No watch_path" in result


def test_word_count_counts_words(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("hello world foo bar baz")
    from widgets.word_count import WordCountWidget
    w = WordCountWidget(cfg={"watch_path": str(path)})
    result = w.render_content()
    assert "5" in result
