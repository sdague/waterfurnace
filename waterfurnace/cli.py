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
def main(user, passwd, sensors, continuous, device, location, vendor, debug):

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
