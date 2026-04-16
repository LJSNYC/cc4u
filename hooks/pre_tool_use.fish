#!/usr/bin/env fish
# CC4U Hook: pre_tool_use
# Fired by Claude Code immediately BEFORE a tool is called.
# Writes a "thinking / tool pending" indicator so the renderer can show
# a spinner or highlight the about-to-run tool.

set event_json (cat)

mkdir -p /tmp/cc4u

set timestamp (date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── snapshot of the pending tool event ──────────────────────────────────────
printf '%s\n' $event_json > /tmp/cc4u/pending_tool_use.json

# ── append to event log ──────────────────────────────────────────────────────
printf '%s\n' $event_json >> /tmp/cc4u/event_log.jsonl

# ── update session with "thinking" state ────────────────────────────────────
printf '%s\n' $event_json | python3 -c "
import json, sys, os

event = json.loads(sys.stdin.read())
session_path = '/tmp/cc4u/session.json'

if os.path.exists(session_path):
    with open(session_path) as f:
        session = json.load(f)
else:
    session = {}

session['status'] = 'thinking'
session['pending_tool'] = event.get('tool_name', event.get('tool', 'unknown'))
session['pending_tool_at'] = '$timestamp'

with open(session_path, 'w') as f:
    json.dump(session, f, indent=2)
" 2>/dev/null

# Set claude_state = thinking, clear idle_since
printf '%s\n' '{}' | python3 -c "
import sys, json, os
session_path = '/tmp/cc4u/session.json'
if os.path.exists(session_path):
    with open(session_path) as f:
        session = json.load(f)
else:
    session = {}
session['claude_state'] = 'thinking'
session['idle_since'] = None
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
