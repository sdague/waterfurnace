"""Tests for write control commands."""

import json

import pytest
import websocket

from waterfurnace import waterfurnace as wf


class TestWsWrite:
    """Tests for the _ws_write core method."""

    def test_sends_correct_json(self, mock_waterfurnace_client, sample_write_success):
        client = mock_waterfurnace_client
        client.ws.recv_data.append(json.dumps(sample_write_success))
        client._ws_write(activemode_write=3)

        sent = json.loads(client.ws.sent_messages[-1])
        assert sent["cmd"] == "write"
        assert sent["source"] == "tstat"
        assert sent["awlid"] == client.gwid
        assert sent["activemode_write"] == 3
        assert "tid" in sent

    def test_increments_tid(self, mock_waterfurnace_client, sample_write_success):
        client = mock_waterfurnace_client
        tid_before = client.tid
        client.ws.recv_data.append(json.dumps(sample_write_success))
        client._ws_write(activemode_write=0)
        assert client.tid == (tid_before + 1) % 100

    def test_raises_wferror_on_error_response(
        self, mock_waterfurnace_client, sample_write_error
    ):
        client = mock_waterfurnace_client
        client.ws.recv_data.append(json.dumps(sample_write_error))
        with pytest.raises(wf.WFError, match="invalid parameter"):
            client._ws_write(activemode_write=99)

    def test_raises_on_websocket_closed(self, mock_waterfurnace_client):
        client = mock_waterfurnace_client
        client.ws.send = lambda msg: (_ for _ in ()).throw(
            websocket.WebSocketConnectionClosedException()
        )
        with pytest.raises(wf.WFWebsocketClosedError):
            client._ws_write(activemode_write=0)

    def test_success_returns_response(
        self, mock_waterfurnace_client, sample_write_success
    ):
        client = mock_waterfurnace_client
        client.ws.recv_data.append(json.dumps(sample_write_success))
        result = client._ws_write(activemode_write=0)
        assert result["data"] == "ok"


class TestSetMode:
    """Tests for set_mode."""

    @pytest.mark.parametrize("mode", [0, 1, 2, 3, 4])
    def test_valid_modes(self, mock_waterfurnace_client, sample_write_success, mode):
        client = mock_waterfurnace_client
        client.ws.recv_data.append(json.dumps(sample_write_success))
        client.set_mode(mode)

        sent = json.loads(client.ws.sent_messages[-1])
        assert sent["cmd"] == "write"
        assert sent["activemode_write"] == mode

    def test_invalid_type(self, mock_waterfurnace_client):
        with pytest.raises(ValueError, match="mode must be an integer"):
            mock_waterfurnace_client.set_mode("heat")

    @pytest.mark.parametrize("mode", [-1, 5, 100])
    def test_out_of_range(self, mock_waterfurnace_client, mode):
        with pytest.raises(ValueError, match="mode must be an integer"):
            mock_waterfurnace_client.set_mode(mode)

    def test_rejects_bool(self, mock_waterfurnace_client):
        with pytest.raises(ValueError, match="mode must be an integer"):
            mock_waterfurnace_client.set_mode(True)


class TestSetCoolingSetpoint:
    """Tests for set_cooling_setpoint."""

    def test_sends_correct_json(self, mock_waterfurnace_client, sample_write_success):
        client = mock_waterfurnace_client
        client.ws.recv_data.append(json.dumps(sample_write_success))
        client.set_cooling_setpoint(73)

        sent = json.loads(client.ws.sent_messages[-1])
        assert sent["cmd"] == "write"
        assert sent["coolingsp_write"] == 73

    def test_accepts_float(self, mock_waterfurnace_client, sample_write_success):
        client = mock_waterfurnace_client
        client.ws.recv_data.append(json.dumps(sample_write_success))
        client.set_cooling_setpoint(72.5)

        sent = json.loads(client.ws.sent_messages[-1])
        assert sent["coolingsp_write"] == 72.5

    def test_invalid_type(self, mock_waterfurnace_client):
        with pytest.raises(ValueError, match="temperature must be numeric"):
            mock_waterfurnace_client.set_cooling_setpoint("73")

    @pytest.mark.parametrize("temp", [60, 90])
    def test_boundary_values(
        self, mock_waterfurnace_client, sample_write_success, temp
    ):
        client = mock_waterfurnace_client
        client.ws.recv_data.append(json.dumps(sample_write_success))
        client.set_cooling_setpoint(temp)

        sent = json.loads(client.ws.sent_messages[-1])
        assert sent["coolingsp_write"] == temp

    @pytest.mark.parametrize("temp", [59, 91])
    def test_out_of_range(self, mock_waterfurnace_client, temp):
        with pytest.raises(ValueError, match="cooling temperature must be between"):
            mock_waterfurnace_client.set_cooling_setpoint(temp)


class TestSetHeatingSetpoint:
    """Tests for set_heating_setpoint."""

    def test_sends_correct_json(self, mock_waterfurnace_client, sample_write_success):
        client = mock_waterfurnace_client
        client.ws.recv_data.append(json.dumps(sample_write_success))
        client.set_heating_setpoint(67)

        sent = json.loads(client.ws.sent_messages[-1])
        assert sent["cmd"] == "write"
        assert sent["heatingsp_write"] == 67

    def test_accepts_float(self, mock_waterfurnace_client, sample_write_success):
        client = mock_waterfurnace_client
        client.ws.recv_data.append(json.dumps(sample_write_success))
        client.set_heating_setpoint(67.5)

        sent = json.loads(client.ws.sent_messages[-1])
        assert sent["heatingsp_write"] == 67.5

    def test_invalid_type(self, mock_waterfurnace_client):
        with pytest.raises(ValueError, match="temperature must be numeric"):
            mock_waterfurnace_client.set_heating_setpoint("67")

    @pytest.mark.parametrize("temp", [40, 80])
    def test_boundary_values(
        self, mock_waterfurnace_client, sample_write_success, temp
    ):
        client = mock_waterfurnace_client
        client.ws.recv_data.append(json.dumps(sample_write_success))
        client.set_heating_setpoint(temp)

        sent = json.loads(client.ws.sent_messages[-1])
        assert sent["heatingsp_write"] == temp

    @pytest.mark.parametrize("temp", [39, 81])
    def test_out_of_range(self, mock_waterfurnace_client, temp):
        with pytest.raises(ValueError, match="heating temperature must be between"):
            mock_waterfurnace_client.set_heating_setpoint(temp)


class TestSetFanMode:
    """Tests for set_fan_mode."""

    def test_auto(self, mock_waterfurnace_client, sample_write_success):
        client = mock_waterfurnace_client
        client.ws.recv_data.append(json.dumps(sample_write_success))
        client.set_fan_mode(0)

        sent = json.loads(client.ws.sent_messages[-1])
        assert sent["fanmode_write"] == 0
        assert "intertimeon_write" not in sent
        assert "intertimeoff_write" not in sent

    def test_continuous(self, mock_waterfurnace_client, sample_write_success):
        client = mock_waterfurnace_client
        client.ws.recv_data.append(json.dumps(sample_write_success))
        client.set_fan_mode(1)

        sent = json.loads(client.ws.sent_messages[-1])
        assert sent["fanmode_write"] == 1

    def test_intermittent(self, mock_waterfurnace_client, sample_write_success):
        client = mock_waterfurnace_client
        client.ws.recv_data.append(json.dumps(sample_write_success))
        client.set_fan_mode(2, intertimeon=5, intertimeoff=10)

        sent = json.loads(client.ws.sent_messages[-1])
        assert sent["fanmode_write"] == 2
        assert sent["intertimeon_write"] == 5
        assert sent["intertimeoff_write"] == 10

    def test_intermittent_missing_times(self, mock_waterfurnace_client):
        with pytest.raises(
            ValueError, match="intertimeon and intertimeoff are required"
        ):
            mock_waterfurnace_client.set_fan_mode(2)

    def test_intermittent_missing_off_time(self, mock_waterfurnace_client):
        with pytest.raises(
            ValueError, match="intertimeon and intertimeoff are required"
        ):
            mock_waterfurnace_client.set_fan_mode(2, intertimeon=5)

    def test_non_intermittent_with_times(self, mock_waterfurnace_client):
        with pytest.raises(ValueError, match="only valid for intermittent"):
            mock_waterfurnace_client.set_fan_mode(0, intertimeon=5, intertimeoff=5)

    def test_invalid_mode(self, mock_waterfurnace_client):
        with pytest.raises(ValueError, match="fan mode must be an integer"):
            mock_waterfurnace_client.set_fan_mode(5)


class TestSetHumidity:
    """Tests for set_humidity."""

    def test_sends_correct_json(
        self, mock_waterfurnace_client, sample_write_success, sample_reading_data
    ):
        client = mock_waterfurnace_client
        # Queue read response then write response
        client.ws.recv_data.append(json.dumps(sample_reading_data))
        client.ws.recv_data.append(json.dumps(sample_write_success))
        client.set_humidity(48)

        sent = json.loads(client.ws.sent_messages[-1])
        assert sent["cmd"] == "write"
        assert sent["dehumid_humid_sp"]["humidification"] == 48
        assert sent["dehumid_humid_sp"]["dehumidification"] == 50

    def test_preserves_humidity_offset_settings(
        self, mock_waterfurnace_client, sample_write_success
    ):
        client = mock_waterfurnace_client
        reading_data = {
            "rsp": "read",
            "tid": 3,
            "err": "",
            "zone": 0,
            "awlid": "ABC123456",
            "compressorpower": 0,
            "fanpower": 0,
            "auxpower": 0,
            "looppumppower": 0,
            "totalunitpower": 0,
            "modeofoperation": 0,
            "airflowcurrentspeed": 0,
            "actualcompressorspeed": 0,
            "tstatdehumidsetpoint": 50,
            "tstathumidsetpoint": 40,
            "tstatrelativehumidity": 45,
            "leavingairtemp": 70.0,
            "tstatroomtemp": 70.0,
            "enteringwatertemp": 40.0,
            "leavingwatertemp": 35.0,
            "tstatheatingsetpoint": 69,
            "tstatcoolingsetpoint": 75,
            "tstatactivesetpoint": 69,
            "waterflowrate": 10.0,
            "activesettings": {"activemode": 1},
            "humidity_offset_settings": {
                "humidity_offset": 0,
                "humdity_control_option": 1,
                "dehumidification_mode": 0,
                "humidification_mode": 0,
            },
        }
        client.ws.recv_data.append(json.dumps(reading_data))
        client.ws.recv_data.append(json.dumps(sample_write_success))
        client.set_humidity(48)

        sent = json.loads(client.ws.sent_messages[-1])
        # The typo "humdity_control_option" from the API should be preserved
        assert sent["humidity_offset_settings"]["humdity_control_option"] == 1
        assert sent["humidity_offset_settings"]["humidity_offset"] == 0

    def test_out_of_range_low(self, mock_waterfurnace_client):
        with pytest.raises(ValueError, match="humidity must be an integer"):
            mock_waterfurnace_client.set_humidity(14)

    def test_out_of_range_high(self, mock_waterfurnace_client):
        with pytest.raises(ValueError, match="humidity must be an integer"):
            mock_waterfurnace_client.set_humidity(96)

    def test_invalid_type(self, mock_waterfurnace_client):
        with pytest.raises(ValueError, match="humidity must be an integer"):
            mock_waterfurnace_client.set_humidity(45.5)
