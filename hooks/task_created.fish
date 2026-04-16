#!/usr/bin/env fish
# CC4U Hook: task_created
# Fired by Claude Code when a new task / sub-agent task is created.

set event_json (cat)

mkdir -p /tmp/cc4u

set timestamp (date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── append to event log ──────────────────────────────────────────────────────
printf '%s\n' $event_json >> /tmp/cc4u/event_log.jsonl

# ── write current task ───────────────────────────────────────────────────────
printf '%s\n' $event_json | python3 -c "
import json, sys

event = json.loads(sys.stdin.read())

task = {
    'id': event.get('task_id', event.get('id', 'unknown')),
    'title': event.get('task_title', event.get('title', event.get('task', ''))),
    'description': event.get('description', ''),
    'status': 'active',
    'created_at': '$timestamp',
    'tools_used': [],
    'raw_event': event
}

with open('/tmp/cc4u/task.json', 'w') as f:
    json.dump(task, f, indent=2)
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
    session = {
        'started_at': '$timestamp',
        'task_history': []
    }

session['status'] = 'active'
session['current_task_id'] = event.get('task_id', event.get('id', 'unknown'))
session['current_task_title'] = event.get('task_title', event.get('title', event.get('task', '')))
session['last_activity'] = '$timestamp'

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
