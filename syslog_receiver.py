#!/usr/bin/env python3
import socketserver
import datetime
import argparse


class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = bytes.decode(self.request[0].strip())
        socket = self.request[1]
        print(datetime.datetime.now().strftime("%Y-%d-%m - %H:%M:%S"), "{} : ".format(self.client_address[0]),
              str(data))


parser = argparse.ArgumentParser(description="Simple syslog message receiver")
parser.add_argument("--host", help="Hostname to listen on", default="0.0.0.0")
parser.add_argument("--port", help="Port to listen on", default=6656)

if __name__ == "__main__":
    args = parser.parse_args()

    try:
        server = socketserver.UDPServer((args.host, args.port), SyslogUDPHandler)
        server.serve_forever(poll_interval=0.5)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        print("Crtl+C Pressed. Shutting down.")
