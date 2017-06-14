#!/usr/bin/env python3

import pygame
import socket
import argparse
import sys


class PygameOutput(object):
    def __init__(self, strips, strip_len, bundle_size, scale=1, space=0):
        self.height = strip_len
        self.width = strips
        self.scale = scale
        self.space = space
        self.rect = (self.scale, self.scale)
        self._draw = self.draw_rect

        pygame.init()

        screen = pygame.display.set_mode(
            (self.width * scale + self.width * space, self.height * scale + self.height * space))
        pygame.display.set_caption('Test output')
        pygame.mouse.set_visible(0)

        self.surface = pygame.display.get_surface()
        self.display = pygame.display

        self.lookup = lookup_table(strips, strip_len, bundle_size)

    def draw_rect(self, buff):
        for x in range(self.width):
            x_pos = x * self.scale + x * self.space
            line = self.lookup[x]

            for y in range(self.height):
                off = 3 * line[y]
                color = pygame.Color(*buff[off:off + 3])
                pos = (x_pos, y * self.scale + y * self.space)

                self.surface.fill(color, (pos, self.rect))

        self.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == 32: # space
                    self.surface.fill((0, 0, 0))
                    self._draw = self.draw_circles
                if event.key == 27:
                    sys.exit()

    def draw_circles(self, buff):
        for x in range(self.width):
            x_pos = int(x * self.scale + x * self.space + self.scale / 2)
            line = self.lookup[x]

            for y in range(self.height):
                off = 3 * line[y]
                color = pygame.Color(*buff[off:off + 3])
                pos = (x_pos, int(y * self.scale + y * self.space + self.scale / 2))

                pygame.draw.circle(self.surface, color, pos, int(scale/2))

        self.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == 32: # space
                    self.surface.fill((0, 0, 0))
                    self._draw = self.draw_rect
                if event.key == 27:
                    sys.exit()

    def draw(self, buff):
        self._draw(buff)


def lookup_table(strips, strip_len, bundle_size):
    led_cnt = strips * strip_len
    positions = []

    # map
    for strip in range(strips):
        positions.append([])
        off = strip % bundle_size

        for led in range(strip_len):
            if (off % 2) == 0:
                pos = (strip * strip_len) + led
            else:
                pos = (strip * strip_len) + (strip_len - (led + 1))

            positions[-1].append(pos)
        print(positions[-1])

    # transpose
    table = []
    for x in range(strip_len):
        table.append([])
        for strip in positions:
            table[-1].append(strip[x])

    return positions


class UDPHandler(object):
    def __init__(self, host, port, bufflen, fistbuff, output_func):
        self.bufflen = bufflen
        self.firstbuff = firstbuff
        self.output_func = output_func
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = (host, port)
        self.socket.bind(self.server_address)

    def handle(self):
        received = 0
        data = bytearray()
        while True:
            try:
                new_data, address = self.socket.recvfrom(self.bufflen - received)
                new_len = len(new_data)
                if received == 0 and new_len < self.firstbuff:
                    print("Drop frame")
                    continue

                data += new_data
                received += new_len

                if received == self.bufflen:
                    self.output_func(data)
                    data.clear()
                    received = 0

            except (IOError, SystemExit):
                raise
            except KeyboardInterrupt:
                print("Crtl+C Pressed. Shutting down.")
                return


parser = argparse.ArgumentParser(description="Simple color packet receiver")
parser.add_argument("--host", help="Hostname to listen on", default="0.0.0.0")
parser.add_argument("--port", help="Port to listen on", default=7000, type=int)
parser.add_argument("--strips", help="Number of strips", type=int, default=25)
parser.add_argument("--striplen", help="Leds per strip", type=int, default=20)
parser.add_argument("--bundle", help="Strip bundle size", type=int, default=5)
parser.add_argument("--scale", help="Scale the pixels", type=int, default=8)
parser.add_argument("--space", help="Space between leds", type=int, default=5)
parser.add_argument("--firstpacket", help="Size of the first (sync) packet", type=int, default=800)

if __name__ == "__main__":
    args = parser.parse_args()

    strips = args.strips
    strip_len = args.striplen
    bundle = args.bundle
    scale = args.scale
    space = args.space
    port = args.port
    host = args.host
    firstbuff = args.firstpacket

    bufflen = strips * strip_len * 3

    output = PygameOutput(strips, strip_len, bundle, scale, space)

    handler = UDPHandler(host, port, bufflen, firstbuff, output.draw)

    handler.handle()
