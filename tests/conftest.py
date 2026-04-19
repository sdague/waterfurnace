"""Shared test fixtures for waterfurnace tests."""

import json
from unittest import mock

import pytest

from waterfurnace import waterfurnace as wf

# ============================================================================
# Mock Response Classes
# ============================================================================


class MockResponse:
    """Mock HTTP response object."""

    def __init__(self, status_code=200, content="", cookies=None, json_data=None):
        self.status_code = status_code
        self.content = content if isinstance(content, bytes) else content.encode()
        self.cookies = cookies or {}
        self._json_data = json_data

    def json(self):
        """Return JSON data."""
        if self._json_data is not None:
            return self._json_data
        return json.loads(self.content)

    def raise_for_status(self):
        """Raise HTTPError for bad status codes."""
        if self.status_code >= 400:
            import requests

            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")


class MockWebSocket:
    """Mock WebSocket connection."""

    def __init__(self, recv_data=None):
        self.recv_data = recv_data or []
        self.recv_index = 0
        self.sent_messages = []
        self.connected = True

    def send(self, message):
        """Mock send method."""
        self.sent_messages.append(message)

    def recv(self):
        """Mock recv method."""
        if self.recv_index < len(self.recv_data):
            data = self.recv_data[self.recv_index]
            self.recv_index += 1
            return data
        return json.dumps({"err": ""})

    def close(self):
        """Mock close method."""
        self.connected = False

    def abort(self):
        """Mock abort method."""
        self.connected = False


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture
def sample_login_response():
    """Sample login response data."""
    return {
        "err": "",
        "locations": [
            {
                "description": "Home",
                "postal": "12345",
                "city": "Springfield",
                "state": "IL",
                "country": "USA",
                "latitude": 39.7817,
                "longitude": -89.6501,
                "gateways": [
                    {
                        "gwid": "ABC123456",
                        "description": "Main Unit",
                        "type": "ABC",
                        "awltstattype": 103,
                        "awltstattypedesc": "IntelliZone 2",
                        "iz2_max_zones": 2,
                        "awlabctypedesc": "7 Series",
                        "awlabctype": 2,
                        "blowertype": 1,
                        "online": 1,
                        "tstat_name": "Thermostat",
                    }
                ],
            }
        ],
    }


@pytest.fixture
def sample_multi_location_response():
    """Sample response with multiple locations and devices."""
    return {
        "err": "",
        "locations": [
            {
                "description": "Home",
                "gateways": [
                    {"gwid": "HOME-GW-1", "description": "Main Floor"},
                    {"gwid": "HOME-GW-2", "description": "Basement"},
                ],
            },
            {
                "description": "Office",
                "gateways": [
                    {"gwid": "OFFICE-GW-1", "description": "Office Unit"},
                ],
            },
        ],
    }


@pytest.fixture
def sample_reading_data():
    """Sample sensor reading data."""
    return {
        "rsp": "read",
        "tid": 20,
        "err": "",
        "zone": 0,
        "awlid": "ABC123456",
        "compressorpower": 1500,
        "fanpower": 39,
        "auxpower": 0,
        "looppumppower": 125,
        "totalunitpower": 1664,
        "awlabctype": 2,
        "modeofoperation": 5,  # Heating 1
        "actualcompressorspeed": 45,
        "airflowcurrentspeed": 2,
        "auroraoutputeh1": 0,
        "auroraoutputeh2": 0,
        "auroraoutputcc": 0,
        "auroraoutputcc2": 0,
        "tstatdehumidsetpoint": 50,
        "tstathumidsetpoint": 40,
        "tstatrelativehumidity": 45,
        "leavingairtemp": 95.5,
        "tstatroomtemp": 69.7,
        "enteringwatertemp": 41.4,
        "aocenteringwatertemp": 0,
        "leavingwatertemp": 36.7,
        "waterflowrate": 12.2,
        "lockoutstatus": {"lockoutstatuscode": 0, "lockedout": 0},
        "lastfault": 0,
        "lastlockout": {"lockoutstatuslast": 0},
        "homeautomationalarm1": 0,
        "homeautomationalarm2": 0,
        "roomtemp": 69,
        "humidity_offset_settings": {
            "humidity_offset": 0,
            "humdity_control_option": 1,
            "dehumidification_mode": 0,
            "humidification_mode": 0,
        },
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


@pytest.fixture
def sample_write_success():
    """Sample successful write response."""
    return {"rsp": "write", "awlid": "ABC123456", "tid": 2, "err": "", "data": "ok"}


@pytest.fixture
def sample_write_error():
    """Sample error write response."""
    return {
        "rsp": "write",
        "awlid": "ABC123456",
        "tid": 2,
        "err": "invalid parameter",
        "data": "",
    }


@pytest.fixture
def sample_energy_data_hourly():
    """Sample hourly energy data."""
    return {
        "columns": [
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
        ],
        "index": [1767578400000, 1767574800000, 1767571200000],
        "data": [
            [
                0.46,
                0.0,
                0,
                0,
                0.0,
                0.0,
                0.12,
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
                0.58,
            ],
            [
                0.98,
                0.0,
                0,
                0,
                0.0,
                0.0,
                0.25,
                0,
                1.0,
                0.0,
                0,
                0,
                0.0,
                0.0,
                0,
                168,
                0,
                1.0,
                1.23,
            ],
            [
                1.01,
                0.0,
                0,
                0,
                0.0,
                0.0,
                0.26,
                0,
                1.0,
                0.0,
                0,
                0,
                0.0,
                0.0,
                0,
                168,
                0,
                1.0,
                1.27,
            ],
        ],
    }


@pytest.fixture
def sample_energy_data_daily():
    """Sample daily energy data."""
    return {
        "columns": [
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
        ],
        "index": [1767434400000, 1767348000000],
        "data": [
            [
                "ABC123456",
                0,
                0.5,
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
            ],
            [
                "ABC123456",
                0,
                0.3,
                0,
                22.15,
                "America/New_York",
                0,
                0,
                0,
                0.0,
                0.0,
                16.05,
                2.50,
                18.55,
                8640,
            ],
        ],
    }


@pytest.fixture
def sample_location_data():
    """Sample location data."""
    return {
        "description": "Home",
        "postal": "12345",
        "city": "Springfield",
        "state": "IL",
        "country": "USA",
        "latitude": 39.7817,
        "longitude": -89.6501,
        "gateways": [
            {
                "gwid": "ABC123456",
                "description": "Main Unit",
                "type": "ABC",
                "awltstattype": 103,
                "online": 1,
            }
        ],
    }


@pytest.fixture
def sample_gateway_data():
    """Sample gateway data."""
    return {
        "gwid": "ABC123456",
        "description": "Main Unit",
        "type": "ABC",
        "awltstattype": 103,
        "awltstattypedesc": "IntelliZone 2",
        "iz2_max_zones": 2,
        "awlabctypedesc": "7 Series",
        "awlabctype": 2,
        "blowertype": 1,
        "online": 1,
        "tstat_name": "Thermostat",
    }


# ============================================================================
# Mock Client Fixtures
# ============================================================================


@pytest.fixture
def mock_session_id():
    """Mock session ID."""
    return "test_session_id_12345"


@pytest.fixture
def mock_requests_post(mock_session_id):
    """Mock requests.post for login."""
    with mock.patch("requests.post") as mock_post:
        mock_post.return_value = MockResponse(cookies={"sessionid": mock_session_id})
        yield mock_post


@pytest.fixture
def mock_websocket_connection(sample_login_response):
    """Mock websocket connection."""
    with mock.patch("websocket.create_connection") as mock_ws:
        ws = MockWebSocket(recv_data=[json.dumps(sample_login_response)])
        mock_ws.return_value = ws
        yield mock_ws, ws


@pytest.fixture
def mock_waterfurnace_client(mock_requests_post, mock_websocket_connection):
    """Create a mocked WaterFurnace client that's logged in."""
    client = wf.WaterFurnace("test@example.com", "password")
    client.login()
    return client


@pytest.fixture
def mock_geostar_client(mock_requests_post, mock_websocket_connection):
    """Create a mocked GeoStar client that's logged in."""
    client = wf.GeoStar("test@example.com", "password")
    client.login()
    return client


# ============================================================================
# Parametrize Fixtures
# ============================================================================


@pytest.fixture(
    params=[
        ("Standby", 0),
        ("Fan Only", 1),
        ("Cooling 1", 2),
        ("Cooling 2", 3),
        ("Reheat", 4),
        ("Heating 1", 5),
        ("Heating 2", 6),
        ("E-Heat", 7),
        ("Aux Heat", 8),
        ("Lockout", 9),
    ]
)
def furnace_mode_data(request):
    """Parametrized fixture for all furnace modes."""
    return request.param


@pytest.fixture(params=["1D", "1H", "15min"])
def energy_frequency(request):
    """Parametrized fixture for energy data frequencies."""
    return request.param


# ============================================================================
# Helper Functions
# ============================================================================


@pytest.fixture
def create_mock_response():
    """Factory fixture to create mock responses."""

    def _create(status_code=200, content="", cookies=None, json_data=None):
        return MockResponse(status_code, content, cookies, json_data)

    return _create


@pytest.fixture
def create_mock_websocket():
    """Factory fixture to create mock websockets."""

    def _create(recv_data=None):
        return MockWebSocket(recv_data)

    return _create
