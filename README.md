# Simple update server for tent ESP8266

This is a simple webserver to provide an update source for some ESP8266.
The ESPs deliver the version of the current firmware to the server.
The server decides if there should be an update delivered.

For simplicity, the "version" is just the build date.
This makes it easy because the EXP firmware can just use `__DATE__` and `__TIME__` macros.

The Server gets the version of the provided file bei either `stat()`-ing the file or by searching for the date string in the binary.
To force the `stat()` behaviour, please use the `--guess-from stat`.

You can provide two firmwares at the moment: `--led_fw` and `--gyro_fw`.
They will be made available at `http://.../led_fw` and `http://.../gyro_fw`. 


```
usage: firmware_update.py [-h] [--led_fw LED_FW] [--gyro_fw GYRO_FW]
                          [--guess_from {stat,strings}] [--watch]

Firmware update service

optional arguments:
  -h, --help            show this help message and exit
  --led_fw LED_FW       Filename of led firmware
  --gyro_fw GYRO_FW     Filename for gyro firmware
  --guess_from {stat,strings}
                        Where to get the version from
  --watch               Watch for file system changes with inotify

```
