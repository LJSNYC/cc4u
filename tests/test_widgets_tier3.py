def test_git_log_widget_type():
    from widgets.git_log import GitLogWidget
    assert GitLogWidget.WIDGET_TYPE == "git_log"


def test_git_log_no_data():
    from widgets.git_log import GitLogWidget
    w = GitLogWidget(cfg={})
    w.data = {}
    assert "No git" in w.render_content()


def test_git_log_shows_branch_and_commit():
    from widgets.git_log import GitLogWidget
    w = GitLogWidget(cfg={})
    w.data = {"git": {"branch": "main", "last_commit_msg": "fix the thing"}}
    result = w.render_content()
    assert "main" in result
    assert "fix the thing" in result


def test_git_branches_widget_type():
    from widgets.git_branches import GitBranchesWidget
    assert GitBranchesWidget.WIDGET_TYPE == "git_branches"


def test_git_branches_shows_clean():
    from widgets.git_branches import GitBranchesWidget
    w = GitBranchesWidget(cfg={})
    w.data = {"git": {"branch": "main", "staged": 0, "unstaged": 0, "untracked": 0, "ahead": 0, "behind": 0}}
    result = w.render_content()
    assert "main" in result
    assert "clean" in result


def test_git_branches_shows_dirty_state():
    from widgets.git_branches import GitBranchesWidget
    w = GitBranchesWidget(cfg={})
    w.data = {"git": {"branch": "feat/x", "staged": 2, "unstaged": 1, "untracked": 3, "ahead": 1, "behind": 0}}
    result = w.render_content()
    assert "2 staged" in result
    assert "1 modified" in result
