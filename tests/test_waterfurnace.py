#!/usr/bin/env python

"""Tests for `waterfurnace` package."""

import pytest
from click.testing import CliRunner

from waterfurnace import cli


@pytest.fixture
def response():
    """Sample pytest fixture."""


@pytest.fixture(autouse=True)
def clear_wf_env(monkeypatch):
    monkeypatch.delenv("WF_USERNAME", raising=False)
    monkeypatch.delenv("WF_PASSWORD", raising=False)
    monkeypatch.delenv("WF_SESSIONID", raising=False)


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    help_result = runner.invoke(cli.main, ["--help"])
    assert help_result.exit_code == 0
    assert "Usage: main [OPTIONS] COMMAND" in help_result.output
    assert "Show this message and exit." in help_result.output


def test_sensors_command_in_help():
    """sensors command appears in top-level help."""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["--help"])
    assert result.exit_code == 0
    assert "sensors" in result.output


def test_energy_command_in_help():
    """energy command appears in top-level help."""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["--help"])
    assert result.exit_code == 0
    assert "energy" in result.output


def test_read_command_removed():
    """read command no longer exists."""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["--help"])
    assert result.exit_code == 0
    assert "read" not in result.output


def test_sensors_help():
    """sensors subcommand shows correct options."""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["sensors", "--help"])
    assert result.exit_code == 0
    assert "--sensors" in result.output
    assert "--continuous" in result.output
    assert "--energy" not in result.output
    assert "--start" not in result.output
    assert "--end" not in result.output


def test_energy_help():
    """energy subcommand shows correct options."""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["energy", "--help"])
    assert result.exit_code == 0
    assert "--start" in result.output
    assert "--end" in result.output
    assert "--freq" in result.output
    assert "--timezone" in result.output
    assert "--sensors" not in result.output
    assert "--continuous" not in result.output


def test_energy_requires_start():
    """energy command fails without --start."""
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["energy", "-u", "user@example.com", "-p", "pass", "--end", "2026-01-31"],
    )
    assert result.exit_code != 0
    assert "start" in result.output.lower() or "missing" in result.output.lower()


def test_energy_requires_end():
    """energy command fails without --end."""
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["energy", "-u", "user@example.com", "-p", "pass", "--start", "2026-01-01"],
    )
    assert result.exit_code != 0
    assert "end" in result.output.lower() or "missing" in result.output.lower()
