#!/usr/bin/env python3
import socketserver
import datetime
import argparse
import logging


class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = bytes.decode(self.request[0].strip())
        socket = self.request[1]
        print(datetime.datetime.now().strftime("%Y-%d-%m - %H:%M:%S"), "{} : ".format(self.client_address[0]),
              str(data))
        if log_file:
            logging.info(str(data))


parser = argparse.ArgumentParser(description="Simple syslog message receiver")
parser.add_argument("--host", help="Hostname to listen on", default="0.0.0.0")
parser.add_argument("--port", help="Port to listen on", default=6656, type=int)
parser.add_argument("--file", help="also log to file")

if __name__ == "__main__":
    args = parser.parse_args()

    if "file" in args and args.file:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%d-%m - %H:%M:%S', filename=args.file, filemode='a')
        log_file = True
    else:
        log_file = False

    try:
        server = socketserver.UDPServer((args.host, args.port), SyslogUDPHandler)
        server.serve_forever(poll_interval=0.5)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        print("Crtl+C Pressed. Shutting down.")
