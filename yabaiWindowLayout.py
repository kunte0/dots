#!/usr/bin/env python3
import json
import subprocess
import click
from click import echo

YABAI = '/usr/local/bin/yabai'


# put your generated configs here
configs = {
    'default': [
        {'app': 'Google Chrome', 'space': 1},
        {'app': 'Notes', 'space': 1},
        {'app': 'KeePassXC', 'space': 1},
        {'app': 'iTerm2', 'space': 2},
        {'app': 'Code', 'space': 3},
        {'app': 'Slack', 'space': 4}
    ],
    '2monitor': [
        {'app': 'Google Chrome', 'space': 1},
        {'app': 'Notes', 'space': 1},
        {'app': 'KeePassXC', 'space': 1},
        {'app': 'iTerm2', 'space': 2},
        {'app': 'Slack', 'space': 4},
        {'app': 'Mail', 'space': 5},
        {'app': 'Calendar', 'space': 5},
        {'app': 'Code', 'space': 9}, 
    ]
}


def run(cmd: str):
    return subprocess.run(cmd, shell=True, capture_output=True).stdout


@click.command()
@click.argument('config')
def main(config):
    windows = json.loads(run(f'{YABAI} -m query --windows'))
    
    if config not in configs:
        # generate config from open windows
        print({
            config: [
                {
                    'app': window['app'],
                    'space': window['space']
                }
                for window in windows
            ]
        })
    
    else:
        # restore window space from config
        config = configs[config]

        for window in windows:
            space = next((x['space'] for x in config if x['app'] == window.get('app')), None)
            if space:
                # move only if space is diffferent
                if window['space'] != space:
                    run(f'{YABAI} -m window {window["id"]} --space {space}')
                    print(f'{window["app"]} moved to workspace {space}')



if __name__ == '__main__':
    main()