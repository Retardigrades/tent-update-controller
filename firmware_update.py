#!/usr/bin/env/python

import argparse
import os
import string
import hashlib
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
        self.filename = filename
        self.md5 = gen_md5(filename)

    def __str__(self):
        return "filename: '{}', date: '{}', md5: '{}'".format(self.filename, self.version, self.md5)


class Config(object):
    def __init__(self):
        self.firmwares = {}

    def add(self, name, firmware):
        print("INFO: add firmware: {}".format(firmware))
        self.firmwares[name] = firmware

    def get_firmware(self, type, date):
        firmware = self.firmwares.get(type)
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


parser = argparse.ArgumentParser(description="Firmware update service")
parser.add_argument("--led_fw", help="Filename of led firmware", required=False)
parser.add_argument("--gyro_fw", help="Filename for gyro firmware", required=False)
parser.add_argument("--guess_from", help="Where to get the version from", choices=["stat", "strings"],
                    default="strings")

if __name__ == "__main__":
    config = Config()

    args = parser.parse_args()
    stat = args.guess_from == "stat"

    args = vars(args)
    for name in ("led_fw", "gyro_fw"):
        if name in args and args.get(name):
            led_fw = prepare_fw(args.get(name), stat)
            if led_fw:
                config.add(name, led_fw)
                create_ep(name)
                continue
        print("INFO: No {} given".format(name))

    app.run(host="0.0.0.0", port=6655)
