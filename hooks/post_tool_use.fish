#!/usr/bin/env fish
# CC4U Hook: post_tool_use
# Fired by Claude Code after every tool call.

set event_json (cat)

mkdir -p /tmp/cc4u

set timestamp (date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── snapshot + event log ─────────────────────────────────────────────────────
printf '%s\n' $event_json > /tmp/cc4u/last_tool_use.json
printf '%s\n' $event_json >> /tmp/cc4u/event_log.jsonl

# ── update session last_tool + status ────────────────────────────────────────
if test -f /tmp/cc4u/session.json
    printf '%s\n' $event_json | python3 -c "
import json, sys

with open('/tmp/cc4u/session.json') as f:
    session = json.load(f)
event = json.loads(sys.stdin.read())
session['last_tool'] = event.get('tool_name', 'unknown')
session['last_tool_at'] = '$timestamp'
session['status'] = 'running'
with open('/tmp/cc4u/session.json', 'w') as f:
    json.dump(session, f, indent=2)
" 2>/dev/null
end

# ── token + cost tracking from transcript ────────────────────────────────────
printf '%s\n' $event_json | python3 -c "
import json, sys, os

event = json.loads(sys.stdin.read())
transcript_path = event.get('transcript_path', '')
if not transcript_path or not os.path.exists(transcript_path):
    sys.exit(0)

session_path = '/tmp/cc4u/session.json'
offset_path = '/tmp/cc4u/transcript_offset'

# Load saved offset (bytes already processed)
saved_offset = 0
if os.path.exists(offset_path):
    try:
        data = json.loads(open(offset_path).read())
        if data.get('path') == transcript_path:
            saved_offset = data.get('offset', 0)
    except Exception:
        pass

# Read only new content since last offset
try:
    with open(transcript_path, 'rb') as f:
        f.seek(saved_offset)
        new_bytes = f.read()
        new_offset = saved_offset + len(new_bytes)
except Exception:
    sys.exit(0)

if not new_bytes:
    sys.exit(0)

# Parse new lines for assistant usage
new_input = 0
new_output = 0
new_cache_create = 0
new_cache_read = 0

for line in new_bytes.decode('utf-8', errors='ignore').split('\n'):
    line = line.strip()
    if not line:
        continue
    try:
        obj = json.loads(line)
        # usage lives under obj['message']['usage'] in assistant entries
        msg = obj.get('message', {})
        usage = None
        if isinstance(msg, dict):
            usage = msg.get('usage')
        if not usage and isinstance(obj.get('usage'), dict):
            usage = obj['usage']
        if usage and isinstance(usage, dict):
            new_input      += usage.get('input_tokens', 0)
            new_output     += usage.get('output_tokens', 0)
            new_cache_create += usage.get('cache_creation_input_tokens', 0)
            new_cache_read   += usage.get('cache_read_input_tokens', 0)
    except Exception:
        pass

# Load pricing — check standard install location first, then common clone paths
pricing_path = None
for candidate in [
    os.path.expanduser('~/.local/share/cc4u/pricing.json'),
    os.path.expanduser('~/cc4u/data/pricing.json'),
]:
    if os.path.exists(candidate):
        pricing_path = candidate
        break

input_rate = 3.0    # per million, default (sonnet)
output_rate = 15.0  # per million, default
cache_create_rate = 3.75  # per million (1.25x input)
cache_read_rate = 0.30    # per million (0.1x input)

try:
    if not pricing_path:
        raise FileNotFoundError
    with open(pricing_path) as f:
        pricing = json.load(f)
    # Try to match model from session
    session_path2 = '/tmp/cc4u/session.json'
    model = ''
    if os.path.exists(session_path2):
        try:
            model = json.loads(open(session_path2).read()).get('model', '')
        except Exception:
            pass
    models = pricing.get('models', {})
    # Try exact match, then prefix match
    rates = models.get(model) or next(
        (v for k, v in models.items() if model and model.startswith(k[:20])),
        models.get(pricing.get('default_model', ''), None)
    )
    if rates:
        input_rate = rates.get('input_per_1m', input_rate)
        output_rate = rates.get('output_per_1m', output_rate)
        cache_create_rate = input_rate * 1.25
        cache_read_rate = input_rate * 0.1
except Exception:
    pass

# Load session and accumulate
if os.path.exists(session_path):
    try:
        with open(session_path) as f:
            session = json.load(f)
    except Exception:
        session = {}
else:
    session = {}

session['tokens_input']  = session.get('tokens_input', 0) + new_input
session['tokens_output'] = session.get('tokens_output', 0) + new_output
session['tokens_cache_create'] = session.get('tokens_cache_create', 0) + new_cache_create
session['tokens_cache_read']   = session.get('tokens_cache_read', 0) + new_cache_read

# Cost calculation
total_input  = session['tokens_input']
total_output = session['tokens_output']
total_cc     = session['tokens_cache_create']
total_cr     = session['tokens_cache_read']

cost = (
    total_input  * input_rate        / 1_000_000 +
    total_output * output_rate       / 1_000_000 +
    total_cc     * cache_create_rate / 1_000_000 +
    total_cr     * cache_read_rate   / 1_000_000
)
session['cost_usd'] = round(cost, 6)

with open(session_path, 'w') as f:
    json.dump(session, f, indent=2)

# Save new offset
with open(offset_path, 'w') as f:
    json.dump({'path': transcript_path, 'offset': new_offset}, f)
" 2>/dev/null

# ── git.json — refresh on file-touching tools ────────────────────────────────
set tool_name (printf '%s\n' $event_json | python3 -c "
import json, sys
print(json.loads(sys.stdin.read()).get('tool_name', ''))
" 2>/dev/null)

set file_tools Write Edit MultiEdit Create Bash NotebookEdit

if contains -- $tool_name $file_tools
    python3 -c "
import subprocess, json, os

cwd = os.environ.get('CC4U_CWD', os.getcwd())
git_path = '/tmp/cc4u/git.json'

try:
    # Branch + ahead/behind
    branch_r = subprocess.run(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        capture_output=True, text=True, timeout=3, cwd=cwd
    )
    branch = branch_r.stdout.strip() if branch_r.returncode == 0 else ''

    # Staged / unstaged / untracked counts
    status_r = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True, text=True, timeout=3, cwd=cwd
    )
    staged = unstaged = untracked = 0
    if status_r.returncode == 0:
        for line in status_r.stdout.splitlines():
            if not line: continue
            idx, work = line[0], line[1]
            if idx != ' ' and idx != '?': staged += 1
            if work not in (' ', '?'): unstaged += 1
            if line.startswith('??'): untracked += 1

    # Ahead / behind
    ahead = behind = 0
    ab_r = subprocess.run(
        ['git', 'rev-list', '--left-right', '--count', 'HEAD...@{upstream}'],
        capture_output=True, text=True, timeout=3, cwd=cwd
    )
    if ab_r.returncode == 0 and ab_r.stdout.strip():
        parts = ab_r.stdout.strip().split()
        if len(parts) == 2:
            ahead, behind = int(parts[0]), int(parts[1])

    # Last commit
    log_r = subprocess.run(
        ['git', 'log', '-1', '--format=%H\t%s\t%ci'],
        capture_output=True, text=True, timeout=3, cwd=cwd
    )
    last_hash = last_msg = last_time = ''
    if log_r.returncode == 0 and log_r.stdout.strip():
        parts = log_r.stdout.strip().split('\t', 2)
        if len(parts) >= 2:
            last_hash = parts[0][:8]
            last_msg  = parts[1]
            last_time = parts[2] if len(parts) > 2 else ''

    git_data = {
        'branch': branch,
        'staged': staged,
        'unstaged': unstaged,
        'untracked': untracked,
        'ahead': ahead,
        'behind': behind,
        'last_commit_hash': last_hash,
        'last_commit_msg': last_msg,
        'last_commit_time': last_time,
    }
    with open(git_path, 'w') as f:
        json.dump(git_data, f, indent=2)
except Exception:
    pass
" 2>/dev/null
end

# ── append to per-session tools history ─────────────────────────────────────
printf '%s\n' $event_json | python3 -c "
import json, sys, os

event = json.loads(sys.stdin.read())
tools_path = '/tmp/cc4u/tools.json'

if os.path.exists(tools_path):
    with open(tools_path) as f:
        tools = json.load(f)
else:
    tools = []

entry = {
    'tool': event.get('tool_name', 'unknown'),
    'input': event.get('tool_input', {}),
    'result': event.get('tool_response', {}).get('stdout', '') if isinstance(event.get('tool_response'), dict) else None,
    'at': '$timestamp'
}
tools.append(entry)
tools = tools[-200:]

with open(tools_path, 'w') as f:
    json.dump(tools, f, indent=2)
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
