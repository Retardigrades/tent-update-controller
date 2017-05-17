# Simple update server for tent ESP8266

This is a simple webserver to provide an update source for some ESP8266.
The ESPs deliver the version of the current firmware to the server.
The server decides if there should be an update delivered.

## Usage

For simplicity, the "version" is just the build date.
This makes it easy because the EXP firmware can just use `__DATE__` and `__TIME__` macros.
The exact format of the Version is: `TENT_VERSION::Mmm dd yyyy::hh:mm:ss`.

The Server gets the version of the provided file bei either `stat()`-ing the file or by searching for the date string in the binary.
To force the `stat()` behaviour, please use the `--guess-from stat`.

You can provide two firmwares at the moment: `--led_fw` and `--gyro_fw`.
They will be made available at `http://.../led_fw` and `http://.../gyro_fw`. 

By default files are watched just by monitoring the change date.
So you don't have to restart if you have a new version of the firmware.
If the modification timestamp is newer, the file will automatically reprocessed.

There is a simple inotify watcher that can watch the firmware files on a linux system and update its internal knowledge of them if changed.
This can be handy in developmen, because you don't have to restart the server on every rebuild.
Use `--watch inotify` for this.
To force the chnage-time-behaviour, use `--watch stat`

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
  --watch {inotify,stat}
                        Watch for file system changes with inotify
  --port PORT           The port to bind the server
  --host HOST           The host address to bind the server

```

## Arduino part

The arduino part is described here: http://esp8266.github.io/Arduino/versions/2.0.0/doc/ota_updates/ota_updates.html#http-server

For easy usage, the following code can be put in a header file:
```C++
#include <ESP8266httpUpdate.h>


#define UPDATE(host, port, endpoint) do { \
  t_httpUpdate_return ret = ESPhttpUpdate.update(host, port, endpoint,  "TENT_VERSION::" __DATE__ "::" __TIME__); \
  switch(ret) { \
    case HTTP_UPDATE_FAILED: \
    break; \
    case HTTP_UPDATE_NO_UPDATES: \
    break; \
    case HTTP_UPDATE_OK: \
    break; \
  }; \
} while (0)
```

It can then be used in the setup:
```C++
  UPDATE("host", 6655, "/led_fw");
```


## Installation

The simples way to install this is using a virtualenv:
```
virtualenv -p python3 <some_path>
. <some_path>/bin/activate
pip install -r requirements.txt
```

If you want to use the `--watch inotify` option, you've to run it on linux and install inotify:
```
pip install inotify
```
