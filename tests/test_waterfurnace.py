#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `waterfurnace` package."""

import pytest

from click.testing import CliRunner

from waterfurnace import waterfurnace
from waterfurnace import cli


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string


def test_command_line_interface(monkeypatch):
    """Test the CLI."""
    monkeypatch.delenv("WF_USERNAME", raising=False)
    monkeypatch.delenv("WF_PASSWORD", raising=False)
    monkeypatch.delenv("WF_SESSIONID", raising=False)
    runner = CliRunner()
    help_result = runner.invoke(cli.main, ["--help"])
    assert help_result.exit_code == 0
    assert "Usage: main [OPTIONS] COMMAND" in help_result.output
    assert "Show this message and exit." in help_result.output
