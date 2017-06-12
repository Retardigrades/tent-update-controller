import pygame
import socket


class PygameOutput(object):
    def __init__(self, strips, strip_len, bundle_size, scale = 1, space = 0):
        self.height = strip_len
        self.width = strips
        self.scale = scale
        self.space = space

        pygame.init()

        screen = pygame.display.set_mode((self.width * scale + self.width * space, self.height * scale + self.height * space))
        pygame.display.set_caption('Test output')
        pygame.mouse.set_visible(0)

        self.surface = pygame.display.get_surface()
        self.display = pygame.display

        self.lookup = lookup_table(strips, strip_len, bundle_size)

    def draw(self, buff):
        assert len(buff) == 3 * self.height * self.width

        for x in range(self.width):
            for y in range(self.height):
                off = 3 * self.lookup[x][y]
                color = pygame.Color(*buff[off:off+3])
                pos = (x * self.scale + x * self.space, y * self.scale + y * self.space)

                self.surface.fill(color, (pos, (self.scale, self.scale)))

        self.display.flip()


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
                if received == 0 and len(new_data) < self.firstbuff:
                    print("Drop frame")
                    continue

                data += new_data
                received += len(new_data)

                if received == self.bufflen:
                    self.output_func(data)
                    data.clear()
                    received = 0

            except (IOError, SystemExit):
                raise
            except KeyboardInterrupt:
                print("Crtl+C Pressed. Shutting down.")
                return


if __name__ == "__main__":
    strips = 25
    strip_len = 20
    bundle = 5
    scale = 10
    space = 4
    port = 7000
    host = "0.0.0.0"
    firstbuff = 800

    bufflen = strips * strip_len * 3

    output = PygameOutput(strips, strip_len, bundle, scale, space)
    
    handler = UDPHandler(host, port, bufflen, firstbuff, output.draw)

    handler.handle()

