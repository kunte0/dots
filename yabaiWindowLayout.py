#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys

YABAI = '/opt/homebrew/bin/yabai'
LAYOUT_DIR = os.path.expanduser('~/.window_layouts')
TOTAL_SPACES = 9

def run(cmd):
    """Run a shell command and return its stdout as text."""
    return subprocess.check_output(cmd, shell=True, text=True)

def query_windows():
    return json.loads(run(f'{YABAI} -m query --windows'))

def query_displays():
    return json.loads(run(f'{YABAI} -m query --displays'))

def adjust_spaces(total=TOTAL_SPACES):
    """Ensure exactly `total` spaces spread evenly over all monitors."""
    displays = query_displays()
    if not displays:
        print("No displays found.", file=sys.stderr)
        sys.exit(1)

    n = len(displays)
    base, rem = divmod(total, n)
    # sort by display index so distribution is stable
    displays.sort(key=lambda d: d.get('index', d.get('display', 0)))
    desired = [base + (1 if i < rem else 0) for i in range(n)]

    for disp, want in zip(displays, desired):
        current = len(disp.get('spaces', []))
        if current < want:
            for _ in range(want - current):
                run(f'{YABAI} -m space --create {disp["index"]}')
        elif current > want:
            # destroy the highest-numbered spaces first
            to_remove = disp['spaces'][-(current - want):]
            for sid in to_remove:
                run(f'{YABAI} -m space --destroy {sid}')

def save_layout(name):
    """Dump current (app -> space) mapping to ~/.window_layouts/<name>.json."""
    os.makedirs(LAYOUT_DIR, exist_ok=True)
    wins = query_windows()
    layout = [{'app': w['app'], 'space': w['space']} for w in wins]
    path = os.path.join(LAYOUT_DIR, f'{name}.json')
    with open(path, 'w') as f:
        json.dump(layout, f, indent=2)
    print(f'Saved layout "{name}" -> {path}')

def restore_layout(name):
    """Load ~/.window_layouts/<name>.json, fix spaces, then move windows."""
    path = os.path.join(LAYOUT_DIR, f'{name}.json')
    if not os.path.isfile(path):
        print(f'No such layout: {name}', file=sys.stderr)
        sys.exit(1)

    with open(path) as f:
        layout = json.load(f)

    adjust_spaces(TOTAL_SPACES)
    wins = query_windows()
    for w in wins:
        target = next((e['space'] for e in layout if e['app'] == w['app']), None)
        if target and w['space'] != target:
            run(f'{YABAI} -m window {w["id"]} --space {target}')
            print(f'Moved "{w["app"]}" -> space {target}')

def list_layouts():
    """Show all saved layout names."""
    os.makedirs(LAYOUT_DIR, exist_ok=True)
    names = [f[:-5] for f in os.listdir(LAYOUT_DIR) if f.endswith('.json')]
    if names:
        print("Available layouts:", ", ".join(sorted(names)))
    else:
        print("No layouts saved.")

def main():
    p = argparse.ArgumentParser(
        description='Save/restore yabai window layouts; enforce 9 spaces evenly spread.'
    )
    subs = p.add_subparsers(dest='cmd', required=True)

    subs.add_parser('list', help='List saved layouts')

    ps = subs.add_parser('save', help='Save current layout')
    ps.add_argument('name', help='Layout name (will create name.json)')

    pr = subs.add_parser('restore', help='Restore a saved layout')
    pr.add_argument('name', help='Layout name to restore')

    args = p.parse_args()

    if args.cmd == 'list':
        list_layouts()
    elif args.cmd == 'save':
        save_layout(args.name)
    elif args.cmd == 'restore':
        restore_layout(args.name)

if __name__ == '__main__':
    main()
