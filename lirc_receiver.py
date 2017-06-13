#!/usr/bin/env python3

import lirc
import requests
import argparse


class Receiver(object):
    def __init__(self, proc_name, base_url, url_map):
        self.sockid = lirc.init(proc_name, blocking=False)
        self.base_url = base_url
        self.url_map = url_map

    def run(self):
        while True:
            codeIR = lirc.nextcode()

            if not codeIR:
                continue

            command = codeIR[0]

            if command not in self.url_map:
                print("Unknown code: {}".format(command))
                continue

            url = self.url_map[command]

            full_url = '{}{}'.format(self.base_url, url)
            try:
                response = requests.get(full_url)
            except IOError as e:
                print("Could not connect to {}: {}".format(full_url, e))


def parse_command(inp_cmd):
    cmd, url = inp_cmd.split(":")
    return cmd, url


parser = argparse.ArgumentParser(description="Lirc receiver")
parser.add_argument("--name", help="Program name to lircd", default="tent-ir")
parser.add_argument("--base", help="Set base url", required=True)
parser.add_argument("commands", help="The command-url mappings in the form command:url", nargs="+", type=parse_command)

default_commands = {
    "vol-up": '/music/volup',
    "vol-down": '/music/voldown',
    "next-song": '/music/next'
}

if __name__ == "__main__":
    args = parser.parse_args()

    url_map = args.commands

    if not url_map:
        print("use default map")
        url_map = default_commands
    else:
        url_map = dict(url_map)

    handler = Receiver(args.name, args.base, url_map)

    handler.run()
