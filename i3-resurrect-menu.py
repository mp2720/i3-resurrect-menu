#!/usr/bin/env python3

import os
import sys
import re
import termios
import termcolor
import time
import tty
import random
import string
import subprocess
import argparse
from functools import partial

MAX_LINES = 30
MAX_COLUMNS = 80
WIN_CLASS_NAME = "i3-resurrect-menu"


def ls_profiles(path: str) -> list[str]:
    """
    Returns json profiles names.
    i3-ressurect ls does not work due to a bug
    """
    try:
        _, _, files = next(os.walk(path))
    except StopIteration:
        return []

    remove_json_suf = lambda s: s.\
        removesuffix('_layout.json').\
        removesuffix('_programs.json')
    filter_json = lambda s: s.endswith('_layout.json') or\
         s.endswith('_programs.json')

    return list(sorted(set(map(remove_json_suf, filter(filter_json, files)))))


CHARS = r'123456789abcdefghijklmnopqrstuvwxyz!@#$%^&?*|_+<>.,\/'


def print_profiles_menu(profiles: list[str]):
    termcolor.cprint('Profiles:\n')
    for i, profile in enumerate(profiles):
        ch = CHARS[i] if i < len(CHARS) else ' '
        num = termcolor.colored(f' [{ch}]', 'light_blue', attrs=['bold'])
        print(f'{num} {profile}')

    if len(profiles) > len(CHARS):
        termcolor.cprint('Too many profiles', color='red', attrs=['bold'])


def getch():
    sys.stdout.flush()
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def select_profile(profiles: list[str]) -> str:
    while True:
        c = getch()

        # ^C ^Z Enter
        if len(c) == 0 or c in '\x04\x03\n\r':
            sys.exit(0)

        if not c in CHARS[:len(profiles)]:
            continue

        return profiles[CHARS.index(c)]


def run_alacritty(lines: int, columns: int, subcmd: str):
    alacritty = [
        'exec', 'alacritty', '--class', WIN_CLASS_NAME, '--option',
        f'window.dimensions.lines={lines}', '--option',
        f'window.dimensions.columns={columns}', '-e', 'python',
        os.path.abspath(sys.argv[0]), '-t', subcmd
    ]
    cmd = ['i3-msg', ' '.join(alacritty)]
    subprocess.run(cmd)


if __name__ == '__main__':
    NO_PROFILES_MSG = 'No profiles'
    ENTER_NAME_MSG = "Save under this profile name:"

    ap = argparse.ArgumentParser(prog='i3-resurrect-menu')
    ap.add_argument('subcmd',
                    action='store',
                    help="'save' or 'restore command'")
    ap.add_argument('-p',
                    action='store',
                    dest='profiles',
                    help='path to i3 resurrect profiles')
    ap.add_argument('-t',
                    action='store_true',
                    dest='in_term',
                    help='run in terminal (for internal use)')

    args = ap.parse_args()

    profiles_path = os.path.expanduser("~/.i3/i3-resurrect/profiles")
    if args.profiles is not None:
        profiles_path = args.profiles

    profiles = ls_profiles(profiles_path)

    if args.subcmd == "save":
        if args.in_term:
            print(ENTER_NAME_MSG)
            session_name = input("> ").strip()

            errmsg = ""
            if not session_name:
                errmsg = "No name was provided"
            else:
                p = subprocess.run(['i3-resurrect', 'save', '-p', session_name],
                                   check=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
                if p.returncode != 0:
                    errmsg = p.stderr.decode()

            if errmsg:
                termcolor.cprint(errmsg, color="red", attrs=['bold'])
                getch()
        else:
            run_alacritty(4, len(ENTER_NAME_MSG), 'save')
    elif args.subcmd == "restore":
        if args.in_term:
            if len(profiles) == 0:
                print(NO_PROFILES_MSG, end='')
                getch()
            else:
                print_profiles_menu(profiles)
                print('\n> ', end='')
                profile = select_profile(profiles)
                p = subprocess.run(['i3-resurrect', 'restore', '-p', profile],
                                   check=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

                errmsg = ""
                if p.returncode != 0:
                    errmsg = p.stderr.decode()

                if errmsg:
                    termcolor.cprint(errmsg, color="red", attrs=['bold'])
        else:
            if len(profiles) == 0:
                lines = 1
                columns = len(NO_PROFILES_MSG) + 1
            else:
                lines = len(profiles) + 4
                columns = max([len('[x] ' + p) for p in profiles]) + 2

            run_alacritty(lines, columns, 'restore')
    else:
        assert False, "invalid command"
