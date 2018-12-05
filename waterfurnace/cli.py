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
def main(user, passwd):
    click.echo("User: {}, Pass: {}".format(user, passwd))

    click.echo("\nStep 1: Login")

    wf = waterfurnace.waterfurnace.WaterFurnace(user, passwd)
    wf.login()

    click.echo("Login Succeeded: session_id = {}".format(wf.sessionid))

    click.echo("Attempting to read data")
    data = wf.read()
    click.echo(data)


if __name__ == "__main__":
    main()
