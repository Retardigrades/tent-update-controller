#!/usr/bin/env python3

import os
import time
import socket
import argparse

import sys
from PIL import Image
import numpy as np

parser = argparse.ArgumentParser(description="Scroll an image through the leds")
parser.add_argument("--max", help="max number of LEDs")
parser.add_argument("--image", help="Image to load")
parser.add_argument("--rate", help="Framerate in fps", default=40)
parser.add_argument("--host", help="Host or ip of the esp")
parser.add_argument("--reboot", help="Just reboot the controller", action="store_true")


def prepare_image(image_file):
    fname = os.path.abspath(os.path.expanduser(image_file))
    image = Image.open(fname)
    data = np.asarray(image, dtype=np.uint8)[0]
    print("INFO: have {} values".format(len(data)))

    return data


if __name__ == "__main__":
    args = parser.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if args.reboot:
        print("INFO: reboot controller")
        sock.sendto(b"\x01", (args.host, 7001))
        sys.exit(0)

    data = prepare_image(args.image)

    interval = 1.0 / int(args.rate)
    max_led = int(args.max)

    bytes_per_packet = 800

    data_len = max_led * 3
    chunks = data_len // bytes_per_packet
    if 0 < (data_len % bytes_per_packet):
        chunks += 1

    while True:
        part = data[:max_led]
        air_data = bytes(bytearray(part.flatten()))

        for chunk in range(chunks):
            sock.sendto(air_data[(chunk * bytes_per_packet):(chunk + 1) * bytes_per_packet], (args.host, 7000))
        data = np.roll(data, 3)

        time.sleep(interval)
