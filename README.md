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

The CLI uses subcommands. Common options (`-u`, `-p`, `-v`, etc.) go after the
subcommand.

### Reading sensor data

```bash
# One-shot sensor reading (password prompted if not provided)
waterfurnace read -u user@example.com -p password

# Read specific sensors
waterfurnace read -u user@example.com -p password -s enteringwatertemp,leavingairtemp

# Read all available sensors
waterfurnace read -u user@example.com -p password -s all

# Continuous monitoring (reads every 15 seconds)
waterfurnace read -u user@example.com -p password --continuous
```

### Energy data

```bash
# Get hourly energy data for a date range
waterfurnace read -u user@example.com -p password --energy \
  --start 2024-01-01 --end 2024-01-31

# Daily energy data in a specific timezone
waterfurnace read -u user@example.com -p password --energy \
  --start 2024-01-01 --end 2024-01-31 --freq 1D --timezone America/Chicago

# 15-minute resolution energy data
waterfurnace read -u user@example.com -p password --energy \
  --start 2024-01-01 --end 2024-01-07 --freq 15min
```

### Controlling the thermostat

```bash
# Set thermostat mode (off, auto, cool, heat, eheat)
waterfurnace set-mode -u user@example.com -p password auto

# Set cooling setpoint (60-90F)
waterfurnace set-cooling-temp -u user@example.com -p password 74

# Set heating setpoint (40-80F)
waterfurnace set-heating-temp -u user@example.com -p password 68
```

### Multi-device and vendor options

```bash
# GeoStar systems (--vendor accepts "waterfurnace" or "geostar")
waterfurnace read -u user@example.com -p password --vendor geostar

# Select a specific device in a multi-device system (0-indexed)
waterfurnace read -u user@example.com -p password -D 1

# Select a specific location in a multi-location system (0-indexed)
waterfurnace read -u user@example.com -p password -l 1
```

### Environment variables

```bash
# Set credentials via environment variables to avoid repeating them
export WF_USERNAME=user@example.com
export WF_PASSWORD=your_password

waterfurnace read
waterfurnace set-mode auto

# Reuse an existing session ID
export WF_SESSIONID=your_session_id
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/sdague/waterfurnace.git
cd waterfurnace

# Install all dependencies (creates .venv automatically)
uv sync --extra dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=waterfurnace --cov-report=term-missing

# Format and lint code
uv run ruff format waterfurnace tests
uv run ruff check waterfurnace tests
```

### Building and Publishing

```bash
# Build package
uv build
```

## Known Issues / Limitations

* The python websocket code goes into a blocked state after long
  periods of usage (always takes at least days if not weeks or months
  to get to this state). I've yet to discover why. Help welcome.


## License

* Free software: Apache Software License 2.0


