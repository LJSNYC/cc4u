#!/usr/bin/env fish
# CC4U Hook: stop
# Fired by Claude Code when the session ends.

set event_json (cat)

mkdir -p /tmp/cc4u

set timestamp (date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── append to event log ──────────────────────────────────────────────────────
printf '%s\n' $event_json >> /tmp/cc4u/event_log.jsonl

# ── write final session summary ──────────────────────────────────────────────
printf '%s\n' $event_json | python3 -c "
import json, sys, os

event = json.loads(sys.stdin.read())
session_path = '/tmp/cc4u/session.json'
summary_path = '/tmp/cc4u/session_summary.json'
tools_path = '/tmp/cc4u/tools.json'
history_path = '/tmp/cc4u/task_history.json'

if os.path.exists(session_path):
    with open(session_path) as f:
        session = json.load(f)
else:
    session = {'started_at': '$timestamp'}

session['status'] = 'stopped'
session['stopped_at'] = '$timestamp'

tool_counts = {}
if os.path.exists(tools_path):
    with open(tools_path) as f:
        tools = json.load(f)
    for t in (tools if isinstance(tools, list) else []):
        name = t.get('tool', 'unknown')
        tool_counts[name] = tool_counts.get(name, 0) + 1

task_count = 0
if os.path.exists(history_path):
    with open(history_path) as f:
        task_count = len(json.load(f))

summary = {
    'session': session,
    'tool_usage': tool_counts,
    'total_tools_called': sum(tool_counts.values()),
    'total_tasks': task_count,
    'stop_event': event,
    'summary_at': '$timestamp'
}

with open(session_path, 'w') as f:
    json.dump(session, f, indent=2)

with open(summary_path, 'w') as f:
    json.dump(summary, f, indent=2)
" 2>/dev/null

# Set claude_state = done, record idle_since timestamp
printf '%s\n' '{}' | python3 -c "
import sys, json, os, time
session_path = '/tmp/cc4u/session.json'
if os.path.exists(session_path):
    with open(session_path) as f:
        session = json.load(f)
else:
    session = {}
session['claude_state'] = 'done'
session['idle_since'] = time.time()
with open(session_path, 'w') as f:
    json.dump(session, f, indent=2)
" 2>/dev/null

# ── signal renderer for final redraw, then stop it ───────────────────────────
if test -f /tmp/cc4u/renderer.pid
    set pid (cat /tmp/cc4u/renderer.pid)
    if kill -0 $pid 2>/dev/null
        kill -SIGUSR1 $pid 2>/dev/null
        sleep 0.3
        kill -SIGTERM $pid 2>/dev/null
    end
    rm -f /tmp/cc4u/renderer.pid
end
