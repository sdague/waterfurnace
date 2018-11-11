# -*- coding: utf-8 -*-

"""Console script for waterfurnace."""

import click
import logging

import waterfurnace.waterfurnace

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


@click.command()
@click.option('-u', '--username', 'user', required=True)
@click.option('-p', '--password', 'passwd', required=True)
@click.option('-n', '--unit', 'unit', required=True)
def main(user, passwd, unit):
    click.echo("User: {}, Pass: {}, Unit: {}".format(user, passwd, unit))

    click.echo("\nStep 1: Login")

    wf = waterfurnace.waterfurnace.WaterFurnace(user, passwd, unit)
    wf.login()

    click.echo("Login Succeeded: session_id = {}".format(wf.sessionid))

    click.echo("Attempting to read data")
    data = wf.read()
    click.echo(data)


if __name__ == "__main__":
    main()
