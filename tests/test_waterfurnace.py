#!/usr/bin/env python

"""Tests for `waterfurnace` package."""

import json
from unittest import mock

import pytest
from click.testing import CliRunner

from waterfurnace import cli
from waterfurnace.models import WFReading


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


SENSOR_RESPONSE = {
    "err": "",
    "modeofoperation": 12,
    "outdoorair": 55.2,
    "leavingairtemp": -999.9,
    "lockoutstatus": {"lockoutstatuscode": 0, "lockedout": 0},
    "activesettings": {"activemode": 3},
}


@pytest.fixture
def fake_client(monkeypatch):
    client = mock.MagicMock()
    client.sessionid = "sess"
    client.locations = []
    client.devices = []
    client.read.return_value = WFReading(dict(SENSOR_RESPONSE))
    monkeypatch.setattr(
        cli.waterfurnace.waterfurnace, "WaterFurnace", lambda *a, **kw: client
    )
    return client


def _sensors(*args):
    runner = CliRunner()
    return runner.invoke(
        cli.main, ["sensors", "-u", "user@example.com", "-p", "pass", *args]
    )


def test_sensors_json_stdout_is_only_json(fake_client):
    result = _sensors("--format", "json")
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data["mode"] == "Hydronic"
    assert data["outdoorair"] == 55.2
    assert data["leavingairtemp"] is None
    assert data["activesettings"]["mode"] == "Heat"
    assert "Login Succeeded" in result.stderr


def test_sensors_json_selected(fake_client):
    result = _sensors("--format", "json", "-s", "mode,outdoorair")
    assert json.loads(result.stdout) == {"mode": "Hydronic", "outdoorair": 55.2}


def test_sensors_json_omits_unreported(fake_client):
    result = _sensors("--format", "json", "-s", "mode,load_tank_temp")
    assert json.loads(result.stdout) == {"mode": "Hydronic"}


def test_sensors_text_skips_unreported(fake_client):
    result = _sensors("-s", "outdoorair,load_tank_temp")
    assert result.exit_code == 0, result.output
    assert "outdoorair = 55.2" in result.stdout
    assert "load_tank_temp" not in result.stdout
    assert "Not available on this unit: load_tank_temp" in result.stderr


def test_sensors_continuous_json_one_object_per_line(fake_client, monkeypatch):
    # Stop the loop after the second sleep.
    sleeps = []

    def fake_sleep(_):
        sleeps.append(1)
        if len(sleeps) == 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(cli.time, "sleep", fake_sleep)
    result = _sensors("--format", "json", "--continuous")
    lines = result.stdout.splitlines()
    assert len(lines) == 2
    assert all(json.loads(line)["mode"] == "Hydronic" for line in lines)


def test_sensors_raw_is_unmodified_response(fake_client):
    result = _sensors("--format", "raw")
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == SENSOR_RESPONSE


def test_sensors_text_all_lists_fields_not_methods(fake_client):
    result = _sensors("-s", "all")
    assert result.exit_code == 0, result.output
    assert "outdoorair = 55.2" in result.stdout
    assert "mode = Hydronic" in result.stdout
    assert "as_dict" not in result.stdout
    assert "raw =" not in result.stdout


def test_sensors_text_default_shows_summary(fake_client):
    result = _sensors()
    assert result.exit_code == 0, result.output
    assert "Login Succeeded" in result.stdout
    assert "<FurnaceReading" in result.stdout
