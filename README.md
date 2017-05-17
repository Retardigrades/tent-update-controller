# Simple update server for tent ESP8266

This is a simple webserver to provide an update source for some ESP8266.
The ESPs deliver the version of the current firmware to the server.
The server decides if there should be an update delivered.

## Usage

For simplicity, the "version" is just the build date.
This makes it easy because the EXP firmware can just use `__DATE__` and `__TIME__` macros.

The Server gets the version of the provided file bei either `stat()`-ing the file or by searching for the date string in the binary.
To force the `stat()` behaviour, please use the `--guess-from stat`.

You can provide two firmwares at the moment: `--led_fw` and `--gyro_fw`.
They will be made available at `http://.../led_fw` and `http://.../gyro_fw`. 

There is a simple inotify watcher that can watch the firmware files on a linux system and update its internal knowledge of them if changed.
This can be handy in developmen, because you don't have to restart the server on every rebuild.
Use `--watch` for this.

The Host and port the server binds can be configured using `--host` and `--port`.
They default to `0.0.0.0` and ´6655`.

Full usage:

```
usage: firmware_update.py [-h] [--led_fw LED_FW] [--gyro_fw GYRO_FW]                      
                          [--guess_from {stat,strings}] [--watch]
                          [--port PORT] [--host HOST]

Firmware update service

optional arguments:
  -h, --help            show this help message and exit
  --led_fw LED_FW       Filename of led firmware
  --gyro_fw GYRO_FW     Filename for gyro firmware
  --guess_from {stat,strings}
                        Where to get the version from
  --watch               Watch for file system changes with inotify
  --port PORT           The port to bind the server
  --host HOST           The host address to bind the server

```

## Installation

The simples way to install this is using a virtualenv:
```
virtualenv -p python3 <some_path>
. <some_path>/bin/activate
pip install -r requirements.txt
```

If you want to use the `--watch` option, you've to run it on linux and install inotify:
```
pip install inotify
```
