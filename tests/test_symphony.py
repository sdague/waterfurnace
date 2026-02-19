#!/usr/bin/env python

"""Tests for `waterfurnace` package."""

import json
from unittest import mock
import unittest

import pytest

from waterfurnace import waterfurnace as wf

FAKE_RESPONSE = {
    "err": "",
    "key": 1234,
    "locations": [{"gateways": [{"gwid": "123456"}]}],
}


FAKE_CONTENT = json.dumps(FAKE_RESPONSE)


class FakeRequest(object):
    def __init__(self, status_code=200, content="", cookies=None):
        self.status_code = status_code
        self.content = content
        if cookies is None:
            self.cookies = {}
        else:
            self.cookies = cookies


class TestSymphony(unittest.TestCase):

    @mock.patch("requests.post")
    def test_unknown_failure(self, mock_req):
        mock_req.return_value = FakeRequest(content="Error")
        w = wf.WaterFurnace(mock.sentinel.email, mock.sentinel.passwd)
        with pytest.raises(wf.WFError):
            w.login()

    @mock.patch("requests.post")
    def test_failled_login(self, mock_req):
        LOGIN_MSG = (
            "Something went wrong. Your login failed. "
            "Please check your email address / password and try again."
            " <br/>"
        )

        mock_req.return_value = FakeRequest(content=LOGIN_MSG)
        w = wf.WaterFurnace(mock.sentinel.email, mock.sentinel.passwd)
        with pytest.raises(wf.WFCredentialError):
            w.login()

    @mock.patch("requests.post")
    def test_success_get_session_id(self, mock_req):
        mock_req.return_value = FakeRequest(
            cookies={"sessionid": mock.sentinel.sessionid}
        )
        w = wf.WaterFurnace(mock.sentinel.email, mock.sentinel.passwd)
        w._get_session_id()
        assert w.sessionid == mock.sentinel.sessionid

    @mock.patch("websocket.create_connection")
    @mock.patch("websocket.recv")
    @mock.patch("requests.post")
    def test_success_login(self, mock_req, m_recv, mock_ws_create):
        mock_req.return_value = FakeRequest(
            cookies={"sessionid": str(mock.sentinel.sessionid)},
        )
        m_ws = mock.MagicMock()
        m_ws.recv.return_value = FAKE_CONTENT
        mock_ws_create.return_value = m_ws

        w = wf.WaterFurnace(str(mock.sentinel.email), str(mock.sentinel.passwd))
        w.login()
        assert m_ws.method_calls[0] == mock.call.send(
            json.dumps(
                {
                    "cmd": "login",
                    "tid": 1,
                    "source": "consumer dashboard",
                    "sessionid": "sentinel.sessionid",
                }
            )
        )
        assert m_ws.method_calls[1] == mock.call.recv()

    @mock.patch("websocket.create_connection")
    @mock.patch("websocket.recv")
    @mock.patch("requests.post")
    def test_get_account_id(self, mock_req, m_recv, mock_ws_create):
        mock_req.return_value = FakeRequest(
            cookies={"sessionid": str(mock.sentinel.sessionid)},
        )
        m_ws = mock.MagicMock()
        m_ws.recv.return_value = FAKE_CONTENT
        mock_ws_create.return_value = m_ws

        w = wf.WaterFurnace(str(mock.sentinel.email), str(mock.sentinel.passwd))
        w.login()
        assert w.account_id == 1234

    @mock.patch("websocket.create_connection")
    @mock.patch("requests.post")
    def test_increment_tid(self, mock_req, mock_ws_create):
        mock_req.return_value = FakeRequest(
            cookies={"sessionid": str(mock.sentinel.sessionid)}
        )

        # This starts getting tricky, because we need to change out
        # the mock response after login to a different one for
        # read. Getting pretty close to needing a simulator here.
        m_ws = mock.MagicMock()
        m_ws.recv.return_value = FAKE_CONTENT
        mock_ws_create.return_value = m_ws

        w = wf.WaterFurnace(mock.sentinel.email, mock.sentinel.passwd)
        w.login()

        # we need to give the json return something non magic
        # otherwise it can't deserialize
        m_ws.recv.return_value = '{"a": "b", "err": ""}'
        mock_ws_create.return_value = m_ws

        w.read()
        w.read()
        w.read()
        assert w.tid == 5


class TestReadData(unittest.TestCase):

    @mock.patch("websocket.create_connection")
    @mock.patch("requests.post")
    def test_increment_read_data(self, mock_req, mock_ws_create):
        mock_req.return_value = FakeRequest(
            cookies={"sessionid": str(mock.sentinel.sessionid)}
        )

        fake_data = json.dumps(
            {
                "rsp": "read",
                "tid": 20,
                "err": "",
                "compressorpower": 0,
                "zone": 0,
                "fanpower": 39,
                "auxpower": 0,
                "looppumppower": 0,
                "totalunitpower": 39,
                "awlabctype": 2,
                "modeofoperation": 1,
                "actualcompressorspeed": 0,
                "airflowcurrentspeed": 2,
                "auroraoutputeh1": 0,
                "auroraoutputeh2": 0,
                "auroraoutputcc": 0,
                "auroraoutputcc2": 0,
                "tstatdehumidsetpoint": 50,
                "tstathumidsetpoint": 40,
                "tstatrelativehumidity": 45,
                "leavingairtemp": 67.7,
                "tstatroomtemp": 69.7,
                "enteringwatertemp": 41.4,
                "aocenteringwatertemp": 0,
                "leavingwatertemp": 36.7,
                "waterflowrate": 12.2,
                "lockoutstatus": {"lockoutstatuscode": 0, "lockedout": 0},
                "lastfault": 15,
                "lastlockout": {"lockoutstatuslast": 0},
                "homeautomationalarm1": 0,
                "homeautomationalarm2": 3,
                "roomtemp": 69,
                "activesettings": {
                    "temporaryoverride": 0,
                    "permanenthold": 0,
                    "vacationhold": 0,
                    "onpeakhold": 0,
                    "superboost": 0,
                    "tstatmode": 0,
                    "activemode": 3,
                    "heatingsp_read": 69,
                    "coolingsp_read": 75,
                    "fanmode_read": 1,
                    "intertimeon_read": 0,
                    "intertimeoff_read": 5,
                },
                "tstatactivesetpoint": 69,
                "tstatmode": 0,
                "tstatheatingsetpoint": 69,
                "tstatcoolingsetpoint": 75,
                "awltstattype": 103,
            }
        )

        m_ws = mock.MagicMock()
        # we need to give the json return something non magic
        # otherwise it can't deserialize
        m_ws.recv.return_value = FAKE_CONTENT
        mock_ws_create.return_value = m_ws

        w = wf.WaterFurnace(mock.sentinel.email, mock.sentinel.passwd)
        w.login()

        # Replace the data packet once we get to read
        m_ws.recv.return_value = fake_data

        data = w.read()

        assert data.airflowcurrentspeed == 2
        assert data.mode == "Fan Only"
        assert data.tstathumidsetpoint == 40
        assert data.tstatrelativehumidity == 45
        assert data.enteringwatertemp == 41.4
        assert data.leavingwatertemp == 36.7
        assert data.waterflowrate == 12.2
        assert data.leavingairtemp == 67.7
        assert data.tstatactivesetpoint == 69

    @mock.patch("websocket.create_connection")
    @mock.patch("requests.post")
    def test_catch_error(self, mock_req, mock_ws_create):
        mock_req.return_value = FakeRequest(
            cookies={"sessionid": str(mock.sentinel.sessionid)}
        )
        m_ws = mock.MagicMock()
        # we need to give the json return something non magic
        # otherwise it can't deserialize
        m_ws.recv.return_value = FAKE_CONTENT
        mock_ws_create.return_value = m_ws

        w = wf.WaterFurnace(
            mock.sentinel.email, mock.sentinel.passwd, str(mock.sentinel.unit)
        )
        w.login()

        # Replace the data content once we get to read
        m_ws.recv.return_value = json.dumps(
            {"rsp": "read", "tid": 20, "err": "something went wrong"}
        )

        mock_ws_create.return_value = m_ws
        with pytest.raises(wf.WFWebsocketClosedError):
            w.read()


class TestEnergyData(unittest.TestCase):

    def test_energy_reading_hourly_data(self):
        """Test WFEnergyReading with hourly/15min frequency data."""
        columns = [
            "total_heat_1",
            "total_heat_2",
            "total_cool_1",
            "total_cool_2",
            "total_electric_heat",
            "total_fan_only",
            "total_loop_pump",
            "total_dehumidification",
            "runtime_heat_1",
            "runtime_heat_2",
            "runtime_cool_1",
            "runtime_cool_2",
            "runtime_electric_heat",
            "runtime_fan_only",
            "runtime_dehumidification",
            "total_records",
            "cool_runtime",
            "heat_runtime",
            "total_power",
        ]
        values = [
            0.46,
            0.0,
            0,
            0,
            0.0,
            0.0,
            0,
            0,
            0.47,
            0.0,
            0,
            0,
            0.0,
            0.0,
            0,
            168,
            0,
            0.47,
            0.46,
        ]
        timestamp_ms = 1767578400000

        reading = wf.WFEnergyReading(timestamp_ms, values, columns)

        assert reading.timestamp_ms == timestamp_ms
        assert reading.total_heat_1 == 0.46
        assert reading.total_heat_2 == 0.0
        assert reading.total_power == 0.46
        assert reading.heat_runtime == 0.47
        assert reading.cool_runtime == 0
        assert reading.get("total_heat_1") == 0.46
        assert reading.get("nonexistent", "default") == "default"

    def test_energy_reading_daily_data(self):
        """Test WFEnergyReading with daily frequency data."""
        columns = [
            "id",
            "cool_runtime",
            "defrost_runtime",
            "dehumidification_runtime",
            "heat_runtime",
            "time_zone",
            "total_cool_1",
            "total_cool_2",
            "total_dehumidification",
            "total_electric_heat",
            "total_fan_only",
            "total_heat_1",
            "total_heat_2",
            "total_power",
            "total_records",
        ]
        values = [
            "6CC840023E88",
            0,
            0,
            0,
            23.98,
            "America/New_York",
            0,
            0,
            0,
            0.0,
            0.0,
            17.32,
            2.71,
            20.03,
            8641,
        ]
        timestamp_ms = 1767434400000

        reading = wf.WFEnergyReading(timestamp_ms, values, columns)

        assert reading.id == "6CC840023E88"
        assert reading.time_zone == "America/New_York"
        assert reading.heat_runtime == 23.98
        assert reading.total_power == 20.03
        assert reading.defrost_runtime == 0
        assert reading.dehumidification_runtime == 0

    def test_energy_data_container(self):
        """Test WFEnergyData container with multiple readings."""
        fake_energy_response = {
            "columns": ["total_heat_1", "total_heat_2", "total_power", "heat_runtime"],
            "index": [1767578400000, 1767574800000, 1767571200000],
            "data": [
                [0.46, 0.0, 0.46, 0.47],
                [0.98, 0.0, 0.98, 1.0],
                [1.01, 0.0, 1.01, 1.0],
            ],
        }

        energy_data = wf.WFEnergyData(fake_energy_response)

        assert len(energy_data) == 3
        assert len(energy_data.readings) == 3
        assert energy_data.columns == fake_energy_response["columns"]

        # Test iteration
        count = 0
        for reading in energy_data:
            assert isinstance(reading, wf.WFEnergyReading)
            count += 1
        assert count == 3

        # Test indexing
        first_reading = energy_data[0]
        assert first_reading.total_heat_1 == 0.46
        assert first_reading.total_power == 0.46

        second_reading = energy_data[1]
        assert second_reading.total_heat_1 == 0.98
        assert second_reading.total_power == 0.98

    def test_energy_data_empty(self):
        """Test WFEnergyData with empty data."""
        empty_response = {"columns": [], "index": [], "data": []}

        energy_data = wf.WFEnergyData(empty_response)
        assert len(energy_data) == 0
        assert len(energy_data.readings) == 0

    @mock.patch("requests.get")
    @mock.patch("websocket.create_connection")
    @mock.patch("requests.post")
    def test_get_energy_data_success(self, mock_post, mock_ws_create, mock_get):
        """Test successful get_energy_data call."""
        # Setup login mocks
        mock_post.return_value = FakeRequest(cookies={"sessionid": "test_session_id"})
        m_ws = mock.MagicMock()
        m_ws.recv.return_value = FAKE_CONTENT
        mock_ws_create.return_value = m_ws

        # Setup energy data response
        fake_energy_response = {
            "columns": ["total_heat_1", "total_power", "heat_runtime"],
            "index": [1767578400000, 1767574800000],
            "data": [[0.46, 0.46, 0.47], [0.98, 0.98, 1.0]],
        }

        mock_response = mock.MagicMock()
        mock_response.json.return_value = fake_energy_response
        mock_response.raise_for_status = mock.MagicMock()
        mock_get.return_value = mock_response

        # Create instance and login
        w = wf.WaterFurnace("test@example.com", "password")
        w.login()

        # Get energy data
        energy_data = w.get_energy_data(
            "2026-01-03", "2026-01-04", "1H", "America/New_York"
        )

        # Verify the request was made correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "freq=1H" in call_args[0][0]
        assert "start=2026-01-03" in call_args[0][0]
        assert "end=2026-01-04" in call_args[0][0]
        assert "timezone=America/New_York" in call_args[0][0]
        assert call_args[1]["cookies"]["sessionid"] == "test_session_id"

        # Verify the returned data
        assert isinstance(energy_data, wf.WFEnergyData)
        assert len(energy_data) == 2

    def test_get_energy_data_not_logged_in(self):
        """Test get_energy_data raises error when not logged in."""
        w = wf.WaterFurnace("test@example.com", "password")

        with pytest.raises(wf.WFCredentialError):
            w.get_energy_data("2026-01-03", "2026-01-04")

    @mock.patch("websocket.create_connection")
    @mock.patch("requests.post")
    def test_get_energy_data_invalid_frequency(self, mock_post, mock_ws_create):
        """Test get_energy_data raises error with invalid frequency."""
        # Setup login mocks
        mock_post.return_value = FakeRequest(cookies={"sessionid": "test_session_id"})
        m_ws = mock.MagicMock()
        m_ws.recv.return_value = FAKE_CONTENT
        mock_ws_create.return_value = m_ws

        w = wf.WaterFurnace("test@example.com", "password")
        w.login()

        with pytest.raises(ValueError):
            w.get_energy_data("2026-01-03", "2026-01-04", frequency="invalid")

    @mock.patch("requests.get")
    @mock.patch("websocket.create_connection")
    @mock.patch("requests.post")
    def test_get_energy_data_http_error(self, mock_post, mock_ws_create, mock_get):
        """Test get_energy_data handles HTTP errors."""
        import requests

        # Setup login mocks
        mock_post.return_value = FakeRequest(cookies={"sessionid": "test_session_id"})
        m_ws = mock.MagicMock()
        m_ws.recv.return_value = FAKE_CONTENT
        mock_ws_create.return_value = m_ws

        # Setup error response
        mock_response = mock.MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "HTTP Error"
        )
        mock_get.return_value = mock_response

        w = wf.WaterFurnace("test@example.com", "password")
        w.login()

        with pytest.raises(wf.WFError):
            w.get_energy_data("2026-01-03", "2026-01-04")


class TestSymphonyLocationMethods:
    """Tests for locations and devices properties in SymphonyGeothermal."""

    def _create_symphony_instance(self, location=0, device=0):
        """Helper to create a SymphonyGeothermal instance."""
        return wf.SymphonyGeothermal(
            "http://base.url",
            "http://login.url",
            "ws://ws.url",
            "test@example.com",
            "password",
            device=device,
            location=location,
        )

    def test_locations_before_login_is_none(self):
        """Test location property is None if not logged in."""
        symphony = self._create_symphony_instance()
        assert symphony.locations is None

    def test_locations_returns_list(self):
        """Test locations is a list of WFLocation objects."""
        symphony = self._create_symphony_instance()
        loc_data = [
            {
                "description": "Home",
                "gateways": [{"gwid": "gw-1"}],
            },
            {
                "description": "Office",
                "gateways": [{"gwid": "gw-2"}],
            },
        ]
        symphony._location_data = loc_data
        assert len(symphony.locations) == 2
        assert all(isinstance(loc, wf.WFLocation) for loc in symphony.locations)

    def test_devices_before_login_is_none(self):
        """Test devices property is None if not logged in."""
        symphony = self._create_symphony_instance()

        assert symphony.devices is None

    def test_devices_is_list(self):
        """Test devices is a list of WFGateway objects."""
        symphony = self._create_symphony_instance(location=0)
        loc_data = {
            "description": "Home",
            "gateways": [
                {"gwid": "gw-1", "description": "Device 1"},
                {"gwid": "gw-2", "description": "Device 2"},
            ],
        }
        symphony._location_data = [loc_data]
        devices = symphony.devices

        assert len(devices) == 2
        assert all(isinstance(dev, wf.WFGateway) for dev in devices)
        assert devices[0].gwid == "gw-1"
        assert devices[1].gwid == "gw-2"

    def test_devices_no_devices_in_location(self):
        """Test devices with location that has no devices."""
        symphony = self._create_symphony_instance(location=0)
        loc_data = {"description": "Home", "gateways": []}
        symphony._location_data = [loc_data]

        assert symphony.devices == []
