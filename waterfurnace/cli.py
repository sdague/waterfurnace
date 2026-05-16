"""Console script for waterfurnace."""

import datetime
import logging
import time

import click

import waterfurnace.waterfurnace

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

COMMON_OPTIONS = [
    click.option(
        "-u",
        "--username",
        "user",
        envvar="WF_USERNAME",
        required=True,
        help="Symphony username (or set WF_USERNAME env var)",
    ),
    click.option(
        "-p",
        "--password",
        "passwd",
        envvar="WF_PASSWORD",
        prompt=True,
        hide_input=True,
        confirmation_prompt=False,
        help="Symphony password (or set WF_PASSWORD env var)",
    ),
    click.option(
        "--sessionid",
        "sessionid",
        envvar="WF_SESSIONID",
        required=False,
        help="Symphony session ID (or set WF_SESSIONID env var)",
    ),
    click.option(
        "-D",
        "--device",
        "device",
        required=False,
        default=0,
        show_default=True,
        help="Select device in multi-device system (0,1,2...]",
    ),
    click.option(
        "-l",
        "--location",
        "location",
        required=False,
        default=0,
        show_default=True,
        help="Select location in multi-location system (0,1,2...]",
    ),
    click.option(
        "-v",
        "--vendor",
        "vendor",
        required=False,
        default="waterfurnace",
        show_default=True,
        type=click.Choice(["waterfurnace", "geostar"]),
        help="Select vendor",
    ),
    click.option("-d", "--debug", "debug", required=False, is_flag=True),
]


def common_options(func):
    for option in reversed(COMMON_OPTIONS):
        func = option(func)
    return func


def get_client(user, passwd, sessionid, device, location, vendor, debug):
    if debug:
        logger.setLevel(logging.DEBUG)

    if vendor == "geostar":
        wf = waterfurnace.waterfurnace.GeoStar(
            user, passwd, device=device, location=location, sessionid=sessionid
        )
    else:
        wf = waterfurnace.waterfurnace.WaterFurnace(
            user, passwd, device=device, location=location, sessionid=sessionid
        )
    wf.login()

    click.echo(f"Login Succeeded: session_id = {wf.sessionid}")

    if wf.locations and location < len(wf.locations):
        click.echo(f"Selected Location: {wf.locations[location].description}")

    if wf.devices and device < len(wf.devices):
        click.echo(f"Selected Device: {wf.devices[device].description}")

    return wf


@click.group()
def main():
    """WaterFurnace / GeoStar Symphony CLI.

    Username and password are required for all subcommands.
    They can be passed as options or set via environment variables.

    \b
    Environment variables:
      WF_USERNAME   Symphony username
      WF_PASSWORD   Symphony password
      WF_SESSIONID  Existing session ID (optional)
    """
    pass


@main.command("sensors")
@common_options
@click.option(
    "-s",
    "--sensors",
    "sensors",
    required=False,
    help='Comma separated list of sensors.  Can be "all"',
)
@click.option(
    "-c",
    "--continuous",
    "continuous",
    required=False,
    is_flag=True,
    help="Read sensors every 15 seconds continuously",
)
def sensors_cmd(
    user, passwd, sessionid, device, location, vendor, debug, sensors, continuous
):
    """Read live sensor data from the unit."""
    click.echo("\nStep 1: Login")
    wf = get_client(user, passwd, sessionid, device, location, vendor, debug)

    while True:
        dt = datetime.datetime.now()
        now = dt.strftime("%Y-%m-%d %H:%M:%S")

        click.echo("")
        click.echo(f"Attempting to read data {now}")
        data = wf.read()

        if sensors is None:
            click.echo(data)
        else:
            if sensors == "all":
                attrs = dir(data)
                sensorlist = []
                for attr in attrs:
                    if not attr.startswith("_"):
                        sensorlist.append(attr)
            else:
                sensorlist = list(sensors.split(","))

            for sensor in sensorlist:
                click.echo(f"{sensor} = {getattr(data, sensor)}")

        if continuous:
            time.sleep(15)
        else:
            break


@main.command("energy")
@common_options
@click.option(
    "--start",
    "start_date",
    required=True,
    help="Start date for energy data (YYYY-MM-DD)",
)
@click.option(
    "--end",
    "end_date",
    required=True,
    help="End date for energy data (YYYY-MM-DD)",
)
@click.option(
    "--freq",
    "frequency",
    required=False,
    default="1H",
    show_default=True,
    help="Energy data frequency: 1D (daily), 1H (hourly), 15min (15 minutes)",
)
@click.option(
    "--timezone",
    "timezone_str",
    required=False,
    default="America/New_York",
    show_default=True,
    help="Timezone for energy data",
)
def energy_cmd(
    user,
    passwd,
    sessionid,
    device,
    location,
    vendor,
    debug,
    start_date,
    end_date,
    frequency,
    timezone_str,
):
    """Get historical energy data from the unit."""
    click.echo("\nStep 1: Login")
    wf = get_client(user, passwd, sessionid, device, location, vendor, debug)

    click.echo("\nStep 2: Get Energy Data")
    click.echo(
        f"Start: {start_date}, End: {end_date}, Frequency: {frequency}, Timezone: {timezone_str}"
    )

    try:
        energy_data = wf.get_energy_data(start_date, end_date, frequency, timezone_str)
        click.echo(f"\nReceived {len(energy_data)} energy readings")

        if len(energy_data) == 0:
            click.echo("No data available for the specified time range")
            return

        click.echo("\nEnergy Data Summary:")

        def calc_stats(values):
            filtered = [v for v in values if v is not None]
            if not filtered:
                return None, None, None, None
            total = sum(filtered)
            return (min(filtered), max(filtered), total / len(filtered), total)

        metrics = {
            "Total Power": [r.total_power for r in energy_data],
            "Total Heat 1": [r.total_heat_1 for r in energy_data],
            "Total Heat 2": [r.total_heat_2 for r in energy_data],
            "Total Cool 1": [r.total_cool_1 for r in energy_data],
            "Total Cool 2": [r.total_cool_2 for r in energy_data],
            "Total Electric Heat": [r.total_electric_heat for r in energy_data],
            "Total Fan Only": [r.total_fan_only for r in energy_data],
            "Total Loop Pump": [r.total_loop_pump for r in energy_data],
            "Heat Runtime": [r.heat_runtime for r in energy_data],
            "Cool Runtime": [r.cool_runtime for r in energy_data],
        }

        for metric_name, values in metrics.items():
            min_val, max_val, avg_val, total_val = calc_stats(values)
            if min_val is not None:
                click.echo(f"\n{metric_name}:")
                click.echo(f"   Min: {min_val:.2f}")
                click.echo(f"   Max: {max_val:.2f}")
                click.echo(f"   Avg: {avg_val:.2f}")
                click.echo(f"   Total: {total_val:.2f}")

    except waterfurnace.waterfurnace.WFNoDataError as e:
        click.echo(f"No data available: {e}")
    except Exception as e:
        click.echo(f"Error getting energy data: {e}")
        raise


MODE_MAP = {
    "off": 0,
    "auto": 1,
    "cool": 2,
    "heat": 3,
    "eheat": 4,
}


@main.command("set-mode")
@common_options
@click.argument("mode", type=click.Choice(list(MODE_MAP.keys())))
def set_mode(user, passwd, sessionid, device, location, vendor, debug, mode):
    """Set the thermostat mode (off, auto, cool, heat, eheat)."""
    wf = get_client(user, passwd, sessionid, device, location, vendor, debug)
    try:
        wf.set_mode(MODE_MAP[mode])
    except ValueError as e:
        raise click.BadParameter(str(e))
    click.echo(f"Mode set to {mode}")


@main.command("set-cooling-temp")
@common_options
@click.argument("temperature", type=float)
def set_cooling_temp(
    user, passwd, sessionid, device, location, vendor, debug, temperature
):
    """Set the cooling temperature setpoint (60-90F)."""
    wf = get_client(user, passwd, sessionid, device, location, vendor, debug)
    try:
        wf.set_cooling_setpoint(temperature)
    except ValueError as e:
        raise click.BadParameter(str(e))
    click.echo(f"Cooling setpoint set to {temperature}F")


@main.command("set-heating-temp")
@common_options
@click.argument("temperature", type=float)
def set_heating_temp(
    user, passwd, sessionid, device, location, vendor, debug, temperature
):
    """Set the heating temperature setpoint (40-80F)."""
    wf = get_client(user, passwd, sessionid, device, location, vendor, debug)
    try:
        wf.set_heating_setpoint(temperature)
    except ValueError as e:
        raise click.BadParameter(str(e))
    click.echo(f"Heating setpoint set to {temperature}F")


if __name__ == "__main__":
    main()
