#!/usr/bin/python3
import socketserver
import struct


data_structs = [
        struct.Struct("L"),
        struct.Struct("HHHHH")]
data_size = sum(s.size() for s in data_structs)


class UDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0]
        print("packet:", len(data), "bytes, ", len(data) / data_size, "points")

        # iter datapoints
        for i in range(len(data) // data_size):
            offset = i * data_size
            data_items = []

            # iter structs
            for st in data_structs:
                item = data[offset:(off + st.size())]
                data_items.extend(st.unpack(item))
                offset += st.size()

            print("point:", i, "data:", data_items)
        

parser = argparse.ArgumentParser(description="Simple syslog message receiver")
parser.add_argument("--host", help="Hostname to listen on", default="0.0.0.0")
parser.add_argument("--port", help="Port to listen on", default=7000)


if __name__ == "__main__":
    try:
        server = socketserver.UDPServer((args.host, int(args.port)), UDPHandler)
        server.serve_forever(poll_interval=0.5)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        print("Crtl+C Pressed. Shutting down.")
