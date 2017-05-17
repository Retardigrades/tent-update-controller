#!/usr/bin/env/python

import argparse
import hashlib
import os
import string
import threading
from collections import namedtuple, defaultdict
from datetime import datetime

from flask import Flask, send_file, request, abort, make_response


def strings(filename, min=4):
    with open(filename, errors="ignore") as f:  # Python 3.x
        result = ""
        for c in f.read():
            if c in string.printable:
                result += c
                continue
            if len(result) >= min:
                yield result
            result = ""
        if len(result) >= min:  # catch result at EOF
            yield result


def gen_md5(filename):
    msg = hashlib.md5()
    with open(filename, "rb") as fn:
        msg.update(fn.read())

    return msg.hexdigest()


class Firmware(object):
    def __init__(self, version, filename):
        self.version = version
        self.filename = os.path.abspath(os.path.expanduser(filename))
        self.md5 = gen_md5(filename)

    def __str__(self):
        return "filename: '{}', date: '{}', md5: '{}'".format(self.filename, self.version, self.md5)


class Config(object):
    def __init__(self, stat=False):
        self.firmwares = {}
        self.is_dirty = set()
        self.stat = stat
        self.fwlock = threading.RLock()

    def add(self, name, firmware):
        print("INFO: add firmware: {}".format(firmware))
        self.firmwares[name] = firmware

    def set_dirty(self, name):
        with self.fwlock:
            self.is_dirty.add(name)

    def get_firmware(self, type, date):
        with self.fwlock:
            firmware = self.firmwares.get(type)
            if type in self.is_dirty:
                print("INFO: File {} dirty - recompute .. ".format(name))
                self.is_dirty.remove(type)
                firmware = prepare_fw(firmware.filename, self.stat)
                print("INFO: new fw: {}".format(firmware))
                self.firmwares[type] = firmware
            if firmware:
                if firmware.version > date:
                    return firmware

        return None


def parse_fw(input_str):
    try:
        return datetime.strptime(input_str, "TENT_VERSION::%b %d %Y::%H:%M:%S")
    except ValueError:
        print("WARN: cannot parse version date {}".format(input_str))
        return None


def prepare_fw(filename, stat):
    if not os.path.exists(filename):
        print("WARN: File {} does not exist.".format(filename))
        return None

    timestamp = None
    if not stat:
        for item in strings(filename, 8):
            if item.startswith("TENT_VERSION::"):
                timestamp = parse_fw(item.strip())
                if timestamp:
                    return Firmware(timestamp, filename)

        print("WARN: No timestamp found in {}".format(filename))

    st = os.path.getmtime(filename)
    timestamp = datetime.fromtimestamp(st)

    return Firmware(timestamp, filename)


def get_version(headers):
    data = request.headers.get("HTTP_X_ESP8266_VERSION", None)
    if not data:
        print("WARN: No version in request header")
        return None

    return parse_fw(data)


config = None
app = Flask(__name__)


def create_ep(name):
    @app.route("/{}".format(name))
    def endpoint():
        version = get_version(request.headers)
        if version:
            print("INFO: got request with version {}".format(version))
            firmware = config.get_firmware(name, version)
            if firmware:
                resp = make_response(
                    send_file(firmware.filename, mimetype="application/octet-stream", as_attachment=True))
                resp.headers["x-MD5"] = firmware.md5
                return resp
        abort(403)


class Watcher(threading.Thread):
    def run(self):
        from inotify import constants, adapters

        Watch = namedtuple("Watch", ("name", "file", "dirname"))

        dirs = defaultdict(list)
        for fw in config.firmwares:
            fname = config.firmwares[fw].filename
            watch = Watch(name=fw, file=os.path.basename(fname), dirname=os.path.dirname(fname))
            dirs[watch.dirname].append(watch)

        mask = (constants.IN_CLOSE_WRITE | constants.IN_ATTRIB | constants.IN_CREATE | constants.IN_MOVE)
        ino = adapters.Inotify()
        for dirname in dirs:
            ino.add_watch(dirname.encode("utf-8"), mask=mask)

        print("INFO: Inotify watcher started")

        for event in ino.event_gen():
            if event is not None:
                (header, type_names, watch_path, filename) = event
                for watch in dirs[watch_path.decode("utf-8")]:
                    if watch.file == filename.decode("utf-8"):
                        print("Update {}".format(watch))
                        config.set_dirty(watch.name)


parser = argparse.ArgumentParser(description="Firmware update service")
parser.add_argument("--led_fw", help="Filename of led firmware", required=False)
parser.add_argument("--gyro_fw", help="Filename for gyro firmware", required=False)
parser.add_argument("--guess_from", help="Where to get the version from", choices=["stat", "strings"],
                    default="strings")
parser.add_argument("--watch", help="Watch for file system changes with inotify", action="store_true")

if __name__ == "__main__":
    config = Config()

    args = parser.parse_args()
    stat = args.guess_from == "stat"
    inotify = args.watch

    args = vars(args)
    for name in ("led_fw", "gyro_fw"):
        if name in args and args.get(name):
            led_fw = prepare_fw(args.get(name), stat)
            if led_fw:
                config.add(name, led_fw)
                create_ep(name)
                continue
        print("INFO: No {} given".format(name))

    if inotify:
        Watcher().start()

    app.run(host="0.0.0.0", port=6655)
