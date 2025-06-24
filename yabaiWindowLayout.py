#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import collections

YABAI = '/opt/homebrew/bin/yabai'
LAYOUT_DIR = os.path.expanduser('~/.window_layouts')
TOTAL_SPACES = 9

def run(cmd):
    """Run a shell command and return its stdout as text."""
    return subprocess.check_output(cmd, shell=True, text=True)

def adjust_spaces(total=TOTAL_SPACES):
    """Ensure exactly total spaces spread evenly over all monitors using global space info."""
    spaces = json.loads(run(f"{YABAI} -m query --spaces"))

    # Determine unique display indices and desired counts
    disp_indices = sorted({s['display'] for s in spaces})
    n = len(disp_indices)
    base, rem = divmod(total, n)
    desired_counts = {disp: base + (1 if i < rem else 0) for i, disp in enumerate(disp_indices)}

    # Group spaces by display and sort by space index
    spaces_by_disp = collections.defaultdict(list)
    for s in spaces:
        spaces_by_disp[s['display']].append(s)
    for disp in disp_indices:
        sp_list = sorted(spaces_by_disp[disp], key=lambda s: s['index'])
        current = len(sp_list)
        want = desired_counts[disp]
        # print(f'display: {disp}, current: {current}, want: {want}')
        if current < want:
            for _ in range(want - current):
                # print(f'Creating space on display {disp}')
                run(f'{YABAI} -m space --create {disp}')
        elif current > want:
            # Remove empty, non-visible spaces first
            to_remove = list(reversed(sp_list))
            removed = 0
            for s in to_remove:
                if removed >= (current - want):
                    break
                # skip non-empty or active spaces
                if s.get('windows') or s.get('is-visible') or s.get('has-focus'):
                    continue
                idx = s['index']
                # print(f'Destroying space on display {disp} index {idx}')
                run(f'{YABAI} -m space --destroy {idx}')
                removed += 1
            if removed < (current - want):
                print(f'Could not destroy enough spaces on display {disp}', file=sys.stderr)

def save_layout(name):
    """Dump current (app -> space) mapping to ~/.window_layouts/<name>.json."""
    os.makedirs(LAYOUT_DIR, exist_ok=True)
    wins = json.loads(run(f"{YABAI} -m query --windows"))
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
    wins = json.loads(run(f"{YABAI} -m query --windows"))
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
