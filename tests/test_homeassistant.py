"""Tests mirroring how Home Assistant's waterfurnace integration uses this
library, so a change here that would break that integration fails locally
instead of only being caught downstream.

Usage is drawn from homeassistant/components/waterfurnace/{__init__.py,
config_flow.py,coordinator.py} in home-assistant/core. Keep this file in
sync with that integration's actual usage rather than with this library's
full public API.
"""

import json
from unittest import mock

import pytest
import requests

from waterfurnace import waterfurnace as wf


class TestClientConstruction:
    """__init__.py and config_flow.py: WaterFurnace(username, password[, device=N])."""

    def test_construct_with_username_password(self):
        client = wf.WaterFurnace("test@example.com", "password")
        assert client.user == "test@example.com"

    def test_construct_with_device_index(self):
        client = wf.WaterFurnace("test@example.com", "password", device=1)
        assert client.device == 1


class TestLoginAndIdentity:
    """__init__.py/config_flow.py: client.login(), then .gwid/.account_id/.devices."""

    def test_login_populates_gwid_account_id_devices(self, mock_waterfurnace_client):
        client = mock_waterfurnace_client
        assert client.gwid is not None
        assert client.account_id is not None
        assert client.devices

    def test_devices_have_gwid_attribute(self, mock_waterfurnace_client):
        # coordinator.py matches a device by `device.gwid == self.unit`.
        client = mock_waterfurnace_client
        for device in client.devices:
            assert hasattr(device, "gwid")

    def test_gwid_matches_a_device_in_devices(self, mock_waterfurnace_client):
        # coordinator.py: next(d for d in client.devices if d.gwid == str(client.gwid))
        client = mock_waterfurnace_client
        assert any(device.gwid == str(client.gwid) for device in client.devices)

    def test_login_raises_wfcredentialerror_on_bad_credentials(self):
        with (
            mock.patch("requests.get") as mock_get,
            mock.patch("requests.post") as mock_post,
        ):
            mock_get.return_value = mock.MagicMock(
                text='<input name="_token" value="fake-csrf-token" />',
            )
            mock_post.return_value = mock.MagicMock(
                cookies={}, content=wf.FAILED_LOGIN.encode()
            )
            client = wf.WaterFurnace("test@example.com", "wrong-password")
            with pytest.raises(wf.WFCredentialError):
                client.login()


class TestReadWithRetry:
    """coordinator.py: hass.async_add_executor_job(self.client.read_with_retry)."""

    def test_read_with_retry_returns_reading(
        self, mock_waterfurnace_client, sample_reading_data
    ):
        client = mock_waterfurnace_client
        client._transport.ws.recv_data.append(json.dumps(sample_reading_data))
        reading = client.read_with_retry()
        assert isinstance(reading, wf.WFReading)


class TestEnergyData:
    """coordinator.py: client.get_energy_data(start, end, frequency=, timezone_str=)."""

    def test_get_energy_data_returns_iterable_readings(
        self, mock_waterfurnace_client, sample_energy_data_hourly
    ):
        client = mock_waterfurnace_client
        with mock.patch("requests.get") as mock_get:
            mock_response = mock.MagicMock()
            mock_response.json.return_value = sample_energy_data_hourly
            mock_response.text = '{"ok": true}'
            mock_response.raise_for_status = mock.MagicMock()
            mock_get.return_value = mock_response

            data = client.get_energy_data(
                "2026-01-03",
                "2026-01-04",
                frequency="1H",
                timezone_str="America/New_York",
            )

        # coordinator.py does: [(r.timestamp, r.total_power) for r in data if ...]
        readings = [
            (reading.timestamp, reading.total_power)
            for reading in data
            if reading.total_power is not None
        ]
        assert readings
        for timestamp, total_power in readings:
            assert timestamp is not None
            assert isinstance(total_power, (int, float))

    def test_get_energy_data_raises_wfcredentialerror_before_login(self):
        client = wf.WaterFurnace("test@example.com", "password")
        with pytest.raises(wf.WFCredentialError):
            client.get_energy_data("2026-01-03", "2026-01-04")

    def test_get_energy_data_raises_wferror_on_http_failure(
        self, mock_waterfurnace_client
    ):
        # coordinator.py catches WFCredentialError/WFError and retries once
        # after a fresh login.
        client = mock_waterfurnace_client
        with mock.patch("requests.get") as mock_get:
            mock_response = mock.MagicMock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "500"
            )
            mock_get.return_value = mock_response
            with pytest.raises(wf.WFError):
                client.get_energy_data("2026-01-03", "2026-01-04")


class TestReloginAfterEnergyFailure:
    """coordinator.py's retry path: on WFError/WFCredentialError, re-login."""

    def test_login_can_be_called_again(
        self, mock_waterfurnace_client, sample_login_response
    ):
        client = mock_waterfurnace_client
        # Simulate coordinator.py re-logging in after a failed energy fetch;
        # this must not raise given a valid mocked session.
        client._transport.ws.recv_data.append(json.dumps(sample_login_response))
        client.login()
        assert client.gwid is not None
