from grid import register

from widgets.clock import ClockWidget
from widgets.git_status import GitStatusWidget
from widgets.cost_tracker import CostTrackerWidget
from widgets.pomodoro import PomodoroWidget
from widgets.cpu_memory import CpuMemoryWidget
from widgets.pty_pane import PtyPane

# Tier 1 — system
from widgets.uptime import UptimeWidget
from widgets.network import NetworkWidget
from widgets.file_watcher import FileWatcherWidget
from widgets.dir_tree import DirTreeWidget

# Tier 2 — Claude state
from widgets.session_status import SessionStatusWidget
from widgets.token_usage import TokenUsageWidget
from widgets.tool_log import ToolLogWidget
from widgets.session_log import SessionLogWidget
from widgets.diff_preview import DiffPreviewWidget
from widgets.session_timer import SessionTimerWidget

# Tier 3 — Git
from widgets.git_log import GitLogWidget
from widgets.git_branches import GitBranchesWidget

# Tier 4 — interactive
from widgets.quote import QuoteWidget
from widgets.daily_goal import DailyGoalWidget
from widgets.checklist import ChecklistWidget
from widgets.task_tracker import TaskTrackerWidget
from widgets.quick_links import QuickLinksWidget
from widgets.project_notes import ProjectNotesWidget
from widgets.word_count import WordCountWidget

_ALL = [
    ClockWidget, GitStatusWidget, CostTrackerWidget, PomodoroWidget,
    CpuMemoryWidget, PtyPane,
    UptimeWidget, NetworkWidget, FileWatcherWidget, DirTreeWidget,
    SessionStatusWidget, TokenUsageWidget, ToolLogWidget, SessionLogWidget,
    DiffPreviewWidget, SessionTimerWidget,
    GitLogWidget, GitBranchesWidget,
    QuoteWidget, DailyGoalWidget, ChecklistWidget, TaskTrackerWidget,
    QuickLinksWidget, ProjectNotesWidget, WordCountWidget,
]

for _cls in _ALL:
    register(_cls)

__all__ = [cls.__name__ for cls in _ALL]
