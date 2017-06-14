#!/usr/bin/env python3

from collections import namedtuple
import argparse
import socket
import struct
import time
import math
import sys

import pygame


Quaternion = namedtuple("Quaternion", ["w", "x", "y", "z"])


def angle_to_quaternion(angle):
    yaw = angle
    pitch = 1.0
    roll = 2.0

    t0 = math.cos(yaw * 0.5)
    t1 = math.sin(yaw * 0.5)
    t2 = math.cos(roll * 0.5)
    t3 = math.sin(roll * 0.5)
    t4 = math.cos(pitch * 0.5)
    t5 = math.sin(pitch * 0.5)

    return Quaternion(
        w=(t0 * t2 * t4 + t1 * t3 * t5),
        x=(t0 * t3 * t4 - t1 * t2 * t5),
        y=(t0 * t2 * t5 + t1 * t3 * t4),
        z=(t1 * t2 * t4 - t0 * t3 * t5))


def _short_val(val):
    return int(val * 16384.0)


class Sender(object):
    def __init__(self, host, port):
        self.start = int(time.time() * 1000)
        self.counter = 0
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.struct = struct.Struct("=LhhhhH")
#        self.struct = struct.Struct("LHHHHH")

    def send(self, quaternion):
        tp = int(time.time() * 1000) - self.start
        data = self.struct.pack(tp,
                                _short_val(quaternion.w),
                                _short_val(quaternion.x),
                                _short_val(quaternion.y),
                                _short_val(quaternion.z),
                                self.counter % 65535)

        self.sock.sendto(data, (self.host, self.port));

        self.counter += 1
        

class PygameController(object):
    def __init__(self, radius=100, border = 30):
        self.radius = radius
        self.border = border
        self.center = (radius + border, radius + border)
        self.angle = 0
        self.adjust = 0

        self._setup()


    def _setup(self):
        pygame.init()

        size = self.radius * 2 + 2 * self.border

        screen = pygame.display.set_mode((size, size))
        pygame.display.set_caption('Fake Gyro')
        pygame.mouse.set_visible(0)

        self.surface = pygame.display.get_surface()
        self.display = pygame.display


    def _change_angle(self, value):
        self.angle += value

        if self.angle < ( -1 * math.pi + 0.0001):
            self.angle = (math.pi - 0.0001)
        elif self.angle > (math.pi - 0.0001):
            self.angle =  ( -1 * math.pi + 0.0001)

    def _draw(self):
        self.surface.fill((0,0,0))
        pygame.draw.circle(self.surface, (17, 153, 255), self.center, self.radius)
        dx, dy = self.center

        dx += int(math.sin(self.angle) * self.radius)
        dy += int(math.cos(self.angle) * self.radius)

        pygame.draw.circle(self.surface, (255, 153, 17), (dx, dy), 8)

        self.display.flip()

    def get_state(self):
        
        if pygame.event.peek():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)

                elif event.type == pygame.KEYDOWN:
                    print(event.key)
                    if event.key == 275:
                        self.adjust = -0.1 
                    elif event.key == 276:
                        self.adjust = 0.1

                elif event.type == pygame.KEYUP:
                    self.adjust = 0.0
                    
        self._change_angle(self.adjust)
        self._draw()
        return self.angle


class ContinousController(object):
    def __init__(self, step=0.1):
        self.step = 0.01
        self.angle = (-1 * math.pi + 0.001)

    def get_state(self):
        self.angle += self.step

        if self.angle > (math.pi - 0.001):
            self.angle = (-1 * math.pi + 0.001)

        return self.angle


parser = argparse.ArgumentParser(description="Simple gyro simulation")
parser.add_argument("--host", help="Hostname to send to", default="0.0.0.0")
parser.add_argument("--port", help="Port to send to", default=7002, type=int)
parser.add_argument("--auto", help="Number of strips", action="store_true", default=False)


if __name__ == "__main__":

    args = parser.parse_args()

    sender = Sender(args.host, args.port)

    if args.auto:
        controller = ContinousController()
    else:
        controller = PygameController()    


    while True:
        try:
            value = controller.get_state()

            q = angle_to_quaternion(value)
            sender.send(q)
            time.sleep(1.0/50)
        except KeyboardInterrupt:
            sys.exit(0)
