#!/usr/bin/env python3

import argparse
import hashlib
import os
import string
import threading
from collections import namedtuple, defaultdict
from datetime import datetime

from flask import Flask, send_file, request, abort, make_response


def strings(filename, min_len=4):
    with open(filename, errors="ignore") as f:  # Python 3.x
        result = ""
        for c in f.read():
            if c in string.printable:
                result += c
                continue
            if len(result) >= min_len:
                yield result
            result = ""
        if len(result) >= min_len:  # catch result at EOF
            yield result


def gen_md5(filename):
    msg = hashlib.md5()
    with open(filename, "rb") as fn:
        msg.update(fn.read())

    return msg.hexdigest()


class Firmware(object):
    def __init__(self, version, filename, file_time):
        self.version = version
        self.filename = os.path.abspath(os.path.expanduser(filename))
        self.md5 = gen_md5(filename)
        self.file_time = file_time

    def __str__(self):
        return "filename: '{}', date: '{}', md5: '{}'".format(self.filename, self.version, self.md5)

    @property
    def changed(self):
        return datetime.fromtimestamp(os.path.getmtime(self.filename)) != self.file_time


class Config(object):
    def __init__(self, stat=False, check_before_compare=False):
        self.firmwares = {}
        self.is_dirty = set()
        self.stat = stat
        self.check = check_before_compare
        self.fwlock = threading.RLock()

    def add(self, firmware_name, firmware):
        print("INFO: add firmware: {}".format(firmware))
        self.firmwares[firmware_name] = firmware

    def set_dirty(self, firmware_name):
        with self.fwlock:
            self.is_dirty.add(firmware_name)

    def get_firmware(self, firmare_name, date):
        with self.fwlock:
            firmware = self.firmwares.get(firmare_name)
            if firmare_name in self.is_dirty:
                print("INFO: File {} dirty - recompute .. ".format(firmare_name))
                self.is_dirty.remove(firmare_name)
                firmware = prepare_fw(firmware.filename, self.stat)
                print("INFO: new fw: {}".format(firmware))
                self.firmwares[firmare_name] = firmware

            if firmware:
                if self.check and firmware.changed:
                    print("INFO: firmware {} changed ..".format(firmare_name))
                    firmware = prepare_fw(firmware.filename, self.stat)
                    print("INFO: new fw: {}".format(firmware))
                    self.firmwares[firmare_name] = firmware

                if firmware.version > date:
                    return firmware
                print("INFO: Our firmware is not newer: {}".format(firmware))
                return None
            print("WARN: Ho firmware set for {}".format(firmare_name))

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

    file_time = datetime.fromtimestamp(os.path.getmtime(filename))

    if not stat:
        for item in strings(filename, 8):
            if item.startswith("TENT_VERSION::"):
                version_timestamp = parse_fw(item.strip())
                if version_timestamp:
                    return Firmware(version_timestamp, filename, file_time)

        print("WARN: No timestamp found in {}".format(filename))

    return Firmware(file_time, filename, file_time)


def get_version(request_headers):
    data = request_headers.get("X-Esp8266-Version", request_headers.get("HTTP_X_ESP8266_VERSION", None))
    if not data:
        print("WARN: No version in request header")
        return None

    return parse_fw(data)


config = None
app = Flask(__name__)


@app.route("/<endpoint_name>")
def endpoint(endpoint_name):
    version = get_version(request.headers)
    if version:
        print("INFO: got request with version {}".format(version))
        firmware = config.get_firmware(endpoint_name, version)
        if firmware:
            resp = make_response(
                send_file(firmware.filename, mimetype="application/octet-stream", as_attachment=True))
            resp.headers["x-MD5"] = firmware.md5
            return resp
    return "", 304


class Watcher(threading.Thread):
    def run(self):
        from inotify import constants, adapters

        Watch = namedtuple("Watch", ("name", "file", "dirname"))

        dirs = defaultdict(list)
        for fw in config.firmwares:
            fname = config.firmwares[fw].filename
            watch_instance = Watch(name=fw, file=os.path.basename(fname), dirname=os.path.dirname(fname))
            dirs[watch_instance.dirname].append(watch_instance)

        mask = (constants.IN_CLOSE_WRITE | constants.IN_ATTRIB | constants.IN_CREATE | constants.IN_MOVE)
        ino = adapters.Inotify()
        for dirname in dirs:
            ino.add_watch(dirname.encode("utf-8"), mask=mask)

        print("INFO: Inotify watcher started")

        for event in ino.event_gen():
            if event is not None:
                (header, type_names, watch_path, filename) = event
                for watch_instance in dirs[watch_path.decode("utf-8")]:
                    if watch_instance.file == filename.decode("utf-8"):
                        print("Update {}".format(watch_instance))
                        config.set_dirty(watch_instance.name)


parser = argparse.ArgumentParser(description="Firmware update service")
parser.add_argument("--led_fw", help="Filename of led firmware", required=False)
parser.add_argument("--gyro_fw", help="Filename for gyro firmware", required=False)
parser.add_argument("--guess_from", help="Where to get the version from", choices=["stat", "strings"],
                    default="strings")
parser.add_argument("--watch", help="Watch for file system changes with inotify", choices=["inotify", "stat"],
                    default="stat")
parser.add_argument("--port", help="The port to bind the server", default=6655)
parser.add_argument("--host", help="The host address to bind the server", default="0.0.0.0")

if __name__ == "__main__":

    args = parser.parse_args()
    use_stat = args.guess_from == "stat"
    watch = args.watch
    port = int(args.port)
    host = args.host

    config = Config(stat=use_stat, check_before_compare=(watch == "stat"))

    args = vars(args)
    for name in ("led_fw", "gyro_fw"):
        if name in args and args.get(name):
            led_fw = prepare_fw(args.get(name), use_stat)
            if led_fw:
                config.add(name, led_fw)
                continue
        print("INFO: No {} given".format(name))

    if watch == "inotify":
        Watcher().start()

    app.run(host=host, port=port)
