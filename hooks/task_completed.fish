#!/usr/bin/env fish
# CC4U Hook: task_completed
# Fired by Claude Code when a task finishes (success or failure).

set event_json (cat)

mkdir -p /tmp/cc4u

set timestamp (date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── append to event log ──────────────────────────────────────────────────────
printf '%s\n' $event_json >> /tmp/cc4u/event_log.jsonl

# ── merge completion data into task.json and move to history ─────────────────
printf '%s\n' $event_json | python3 -c "
import json, sys, os

event = json.loads(sys.stdin.read())
task_path = '/tmp/cc4u/task.json'
history_path = '/tmp/cc4u/task_history.json'

if os.path.exists(task_path):
    with open(task_path) as f:
        task = json.load(f)
else:
    task = {'id': event.get('task_id', 'unknown')}

task['status'] = event.get('status', 'completed')
task['completed_at'] = '$timestamp'
task['result'] = event.get('result', event.get('output', ''))
task['error'] = event.get('error', None)

with open(task_path, 'w') as f:
    json.dump(task, f, indent=2)

if os.path.exists(history_path):
    with open(history_path) as f:
        history = json.load(f)
else:
    history = []

history.append(task)
history = history[-50:]

with open(history_path, 'w') as f:
    json.dump(history, f, indent=2)
" 2>/dev/null

# ── update session ───────────────────────────────────────────────────────────
printf '%s\n' $event_json | python3 -c "
import json, sys, os

event = json.loads(sys.stdin.read())
session_path = '/tmp/cc4u/session.json'

if os.path.exists(session_path):
    with open(session_path) as f:
        session = json.load(f)
else:
    session = {}

session['status'] = 'idle'
session['last_completed_task_id'] = event.get('task_id', event.get('id', 'unknown'))
session['last_activity'] = '$timestamp'
session['pending_tool'] = None

with open(session_path, 'w') as f:
    json.dump(session, f, indent=2)
" 2>/dev/null

# ── signal renderer ──────────────────────────────────────────────────────────
if test -f /tmp/cc4u/renderer.pid
    set pid (cat /tmp/cc4u/renderer.pid)
    if kill -0 $pid 2>/dev/null
        kill -SIGUSR1 $pid 2>/dev/null
    else
        rm -f /tmp/cc4u/renderer.pid
    end
end
