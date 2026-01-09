# -*- coding: utf-8 -*-

"""Console script for waterfurnace."""

import click
import logging
import time
import datetime

import waterfurnace.waterfurnace

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


@click.command()
@click.option("-u", "--username", "user", required=True, help="Symphony username")
@click.option(
    "-p",
    "--password",
    "passwd",
    envvar="WF_PASSWORD",
    prompt=True,
    hide_input=True,
    confirmation_prompt=False,
    help="Symphony password (or set WF_PASSWORD env var)",
)
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
    help="Read sensors every 15 seconds continously",
)
@click.option(
    "-D",
    "--device",
    "device",
    required=False,
    default=0,
    show_default=True,
    help="Select device in multi-device system (0,1,2...]",
)
@click.option(
    "-l",
    "--location",
    "location",
    required=False,
    default=0,
    show_default=True,
    help="Select location in multi-location system (0,1,2...]",
)
@click.option(
    "-v",
    "--vendor",
    "vendor",
    required=False,
    default="waterfurnace",
    show_default=True,
    type=click.Choice(["waterfurnace", "geostar"]),
    help="Select vendor",
)
@click.option("-d", "--debug", "debug", required=False, is_flag=True)
@click.option(
    "-e",
    "--energy",
    "energy",
    required=False,
    is_flag=True,
    help="Get energy data instead of sensor readings",
)
@click.option(
    "--start",
    "start_date",
    required=False,
    help="Start date for energy data (YYYY-MM-DD)",
)
@click.option(
    "--end",
    "end_date",
    required=False,
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
def main(
    user,
    passwd,
    sensors,
    continuous,
    device,
    location,
    vendor,
    debug,
    energy,
    start_date,
    end_date,
    frequency,
    timezone_str,
):

    click.echo("\nStep 1: Login")
    if debug:
        logger.setLevel(logging.DEBUG)

    if vendor == "geostar":
        wf = waterfurnace.waterfurnace.GeoStar(
            user, passwd, device=device, location=location
        )
    else:
        wf = waterfurnace.waterfurnace.WaterFurnace(
            user, passwd, device=device, location=location
        )
    wf.login()

    click.echo("Login Succeeded: session_id = {}".format(wf.sessionid))

    if energy:
        # Energy data mode
        if not start_date or not end_date:
            click.echo("Error: --start and --end dates are required for energy data")
            return

        click.echo("\nStep 2: Get Energy Data")
        click.echo(
            "Start: {}, End: {}, Frequency: {}, Timezone: {}".format(
                start_date, end_date, frequency, timezone_str
            )
        )

        try:
            energy_data = wf.get_energy_data(
                start_date, end_date, frequency, timezone_str
            )
            click.echo("\nReceived {} energy readings".format(len(energy_data)))

            if len(energy_data) == 0:
                click.echo("No data available for the specified time range")
                return

            # Calculate summary statistics for key metrics
            click.echo("\nEnergy Data Summary:")

            # Helper function to calculate stats
            def calc_stats(values):
                filtered = [v for v in values if v is not None]
                if not filtered:
                    return None, None, None, None
                total = sum(filtered)
                return (min(filtered), max(filtered), total / len(filtered), total)

            # Collect values for each metric
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

            # Display statistics for each metric
            for metric_name, values in metrics.items():
                min_val, max_val, avg_val, total_val = calc_stats(values)
                if min_val is not None:
                    click.echo("\n{}:".format(metric_name))
                    click.echo("   Min: {:.2f}".format(min_val))
                    click.echo("   Max: {:.2f}".format(max_val))
                    click.echo("   Avg: {:.2f}".format(avg_val))
                    click.echo("   Total: {:.2f}".format(total_val))

        except Exception as e:
            click.echo("Error getting energy data: {}".format(e))
            raise

    else:
        # Normal sensor reading mode
        while True:

            dt = datetime.datetime.now()
            now = dt.strftime("%Y-%m-%d %H:%M:%S")

            click.echo("")
            click.echo("Attempting to read data {}".format(now))
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
                    click.echo("{} = {}".format(sensor, getattr(data, sensor)))

            if continuous:
                time.sleep(15)
            else:
                break


if __name__ == "__main__":
    main()
