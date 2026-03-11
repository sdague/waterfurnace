# waterfurnace

[![python package status](https://img.shields.io/pypi/v/waterfurnace.svg)](https://pypi.python.org/pypi/waterfurnace)
[![build status](https://github.com/sdague/waterfurnace/actions/workflows/python-app.yml/badge.svg)](https://github.com/sdague/waterfurnace/actions/workflows/python-app.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/waterfurnace.svg)](https://pypi.python.org/pypi/waterfurnace)

Python interface for WaterFurnace and GeoStar geothermal systems.

This provides basic sensor readings for WaterFurnace geothermal systems by
using the websocket interface that exists for the Symphony website. This is not
a documented or stable interface, so don't use this for critical
systems. However, it is useful to record historical usage of your WaterFurnace
system.

## Installation

```bash
pip install waterfurnace
```

## Quick Start

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

The software now supports a CLI.  For details, use `waterfurnace --help`

## CLI Usage

```bash
# Basic usage
waterfurnace -u user@example.com -p password

# Continuous monitoring (reads every 15 seconds)
waterfurnace -u user@example.com -p password --continuous

# Get energy data
waterfurnace -u user@example.com -p password --energy \
  --start 2024-01-01 --end 2024-01-31 --freq 1H

# Use environment variable for password
export WF_PASSWORD=your_password
waterfurnace -u user@example.com

# GeoStar systems
waterfurnace -u user@example.com -p password --vendor geostar
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/sdague/waterfurnace.git
cd waterfurnace

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=waterfurnace --cov-report=term-missing

# Format code
black waterfurnace tests

# Run all tests across Python versions
tox
```

### Building and Publishing

```bash
# Build package
python -m build

# Check package
twine check dist/*
```

## Known Issues / Limitations

* The python websocket code goes into a blocked state after long
  periods of usage (always takes at least days if not weeks or months
  to get to this state). I've yet to discover why. Help welcome.


## License

* Free software: Apache Software License 2.0
* Documentation: https://waterfurnace.readthedocs.io.


