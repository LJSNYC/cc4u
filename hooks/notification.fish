#!/usr/bin/env fish
# CC4U Hook: notification
# Fired by Claude Code when it wants to surface a notification.

set event_json (cat)

mkdir -p /tmp/cc4u

set timestamp (date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── append to event log ──────────────────────────────────────────────────────
printf '%s\n' $event_json >> /tmp/cc4u/event_log.jsonl

# ── extract notification fields and write to notification.json ───────────────
set notif_fields (printf '%s\n' $event_json | python3 -c "
import json, sys, os

event = json.loads(sys.stdin.read())

notification = {
    'id': event.get('notification_id', event.get('id', 'n_unknown')),
    'title': event.get('title', 'Claude Code'),
    'message': event.get('message', event.get('body', event.get('text', str(event)))),
    'level': event.get('level', event.get('type', 'info')),
    'action': event.get('action', None),
    'at': '$timestamp',
    'raw': event
}

with open('/tmp/cc4u/notification.json', 'w') as f:
    json.dump(notification, f, indent=2)

ring_path = '/tmp/cc4u/notification_history.json'
if os.path.exists(ring_path):
    with open(ring_path) as f:
        ring = json.load(f)
else:
    ring = []

ring.append(notification)
ring = ring[-20:]

with open(ring_path, 'w') as f:
    json.dump(ring, f, indent=2)

print(notification['title'])
print(notification['message'])
" 2>/dev/null)

set notif_title (echo $notif_fields | head -1)
set notif_message (echo $notif_fields | tail -1)

# ── Push to CC4U notification queue for top bar flash ────────────────────────
printf '%s\n' $event_json | python3 -c "
import sys, json, os, time
event = json.loads(sys.stdin.read())
msg = event.get('message', event.get('title', event.get('body', 'Notification')))
ntype = 'info'
if event.get('type') == 'error' or 'error' in str(msg).lower():
    ntype = 'error'
elif event.get('type') == 'warning':
    ntype = 'warning'
elif event.get('type') == 'success':
    ntype = 'success'
data = {'message': str(msg), 'type': ntype, 'duration': 5, 'created_at': time.time()}
import os as _os
notif_path = '/tmp/cc4u/notifications.json'
_os.makedirs('/tmp/cc4u', exist_ok=True)
tmp = notif_path + '.tmp'
with open(tmp, 'w') as f:
    json.dump(data, f)
_os.replace(tmp, notif_path)
" 2>/dev/null

# ── macOS Notification Centre ────────────────────────────────────────────────
if test (uname) = Darwin
    set cc4u_config "$HOME/.config/cc4u/config.json"
    set do_notify true

    if test -f $cc4u_config
        set do_notify (python3 -c "
import json
try:
    with open('$cc4u_config') as f:
        cfg = json.load(f)
    print('false' if cfg.get('notifications', {}).get('macos_native', True) == False else 'true')
except:
    print('true')
" 2>/dev/null)
    end

    if test "$do_notify" = true
        set safe_title (echo $notif_title | string replace -a '"' '\\"')
        set safe_msg (echo $notif_message | string replace -a '"' '\\"')

        if test -n "$safe_msg"
            osascript -e "display notification \"$safe_msg\" with title \"$safe_title\" subtitle \"CC4U\"" 2>/dev/null
        end
    end
end

# ── signal renderer ──────────────────────────────────────────────────────────
if test -f /tmp/cc4u/renderer.pid
    set pid (cat /tmp/cc4u/renderer.pid)
    if kill -0 $pid 2>/dev/null
        kill -SIGUSR1 $pid 2>/dev/null
    else
        rm -f /tmp/cc4u/renderer.pid
    end
end
