# waterfurnace


[![python package status](https://img.shields.io/pypi/v/waterfurnace.svg)](https://pypi.python.org/pypi/waterfurnace)
[![build status](https://github.com/sdague/waterfurnace/actions/workflows/python-app.yml/badge.svg)](https://github.com/sdague/waterfurnace/actions/workflows/python-app.yml)


Python interface for waterfurnace and geostar geothermal systems.

This provides basic sensor readings for waterfurnace geothermal systems by
using the websocket interface that exists for the symphony website. This is not
a documented or stable interface, so don't use this for critical
systems. However, it is useful to record historical usage of your waterfurnace
system.

## Usage

```python

   from waterfurnace.waterfurnace import WaterFurnace
   wf = WaterFurnace(user, pass)
   wf.login()
   data = wf.read()
```

The waterfurnace symphony service websocket monitors it's usage, so you need to
do a data reading at least every 30 seconds otherwise the websocket is closed
on the server side for resource constraints. The symphony website does a poll
on the websocket every 5 seconds.

The software now supports a CLI.  For details, use waterfurnace --help

## Known Issues / limitations

* The python websocket code goes into a blocked state after long
  periods of usage (always takes at least days if not weeks or months
  to get to this state). I've yet to discover why. Help welcome.


## License

* Free software: Apache Software License 2.0
* Documentation: https://waterfurnace.readthedocs.io.


