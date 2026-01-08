# -*- coding: utf-8 -*-

"""Main module."""

import copy
import json
import logging
import ssl
import threading
import time
from datetime import datetime, timezone

import requests
import websocket

_LOGGER = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0"
WF_BASE_URL = "https://symphony.mywaterfurnace.com"
WF_LOGIN_URL = f"{WF_BASE_URL}/account/login"
WF_WS_URL = "wss://awlclientproxy.mywaterfurnace.com/"
GS_BASE_URL = "https://symphony.mygeostar.com"
GS_LOGIN_URL = f"{GS_BASE_URL}/account/login"
GS_WS_URL = "wss://awlclientproxy.mygeostar.com/"

FURNACE_MODE = (
    "Standby",
    "Fan Only",
    "Cooling 1",
    "Cooling 2",
    "Reheat",
    "Heating 1",
    "Heating 2",
    "E-Heat",
    "Aux Heat",
    "Lockout",
)

FAILED_LOGIN = (
    "Your login failed. Please check your email address / password and try again."
)

TIMEOUT = 30
ERROR_INTERVAL = 300

DATA_REQUEST = {
    "cmd": "read",
    "tid": None,
    "awlid": None,
    "zone": 0,
    "rlist": [  # the list of sensors to return readings for
        "compressorpower",
        "fanpower",
        "auxpower",
        "looppumppower",
        "totalunitpower",
        "AWLABCType",
        "ModeOfOperation",
        "ActualCompressorSpeed",
        "AirflowCurrentSpeed",
        "AuroraOutputEH1",
        "AuroraOutputEH2",
        "AuroraOutputCC",
        "AuroraOutputCC2",
        "TStatDehumidSetpoint",
        "TStatHumidSetpoint",
        "TStatRelativeHumidity",
        "LeavingAirTemp",
        "TStatRoomTemp",
        "EnteringWaterTemp",
        "AOCEnteringWaterTemp",
        "LeavingWaterTemp",
        "WaterFlowRate",
        "lockoutstatus",
        "lastfault",
        "lastlockout",
        "humidity_offset_settings",
        "humidity",
        "outdoorair",
        "homeautomationalarm1",
        "homeautomationalarm2",
        "roomtemp",
        "activesettings",
        "TStatActiveSetpoint",
        "TStatMode",
        "TStatHeatingSetpoint",
        "TStatCoolingSetpoint",
        "AWLTStatType",
    ],
    "source": "consumer dashboard",
}


class WFException(Exception):
    pass


class WFCredentialError(WFException):
    pass


class WFWebsocketClosedError(WFException):
    pass


class WFError(WFException):
    pass


class SymphonyGeothermal(object):
    def __init__(
        self,
        base_url,
        login_url,
        ws_url,
        user,
        passwd,
        max_fails=5,
        device=0,
        location=0,
    ):
        self.base_url = base_url
        self.login_url = login_url
        self.ws_url = ws_url
        self.user = user
        self.passwd = passwd
        self.location = location
        self.device = device
        self.gwid = None
        self.sessionid = None
        self.tid = 0
        # For retry logic
        self.max_fails = max_fails
        self.fails = 0
        _LOGGER.debug(self)

    def __repr__(self):
        return f"<Symphony user={self.user} passwd={self.passwd}>"

    def next_tid(self):
        self.tid = (self.tid + 1) % 100

    def _get_session_id(self):
        data = dict(
            emailaddress=self.user, password=self.passwd, op="login", redirect="/"
        )
        headers = {
            "user-agent": USER_AGENT,
        }

        res = requests.post(
            self.login_url,
            data=data,
            headers=headers,
            cookies={
                "legal-acknowledge": "yes",
                "energy-base-price": "0.15",
                "temp_unit": "f",
            },
            timeout=TIMEOUT,
            allow_redirects=False,
        )
        try:
            self.sessionid = res.cookies["sessionid"]
        except KeyError:
            _LOGGER.error(
                "Did not find expected session cookie, login failed."
                " A lot of debug info coming..."
            )
            _LOGGER.debug("Response: {}".format(res))
            _LOGGER.debug("Response Cookies: {}".format(res.cookies))
            _LOGGER.debug("Response Content: {}".format(res.content))
            if FAILED_LOGIN in res.content:
                _LOGGER.error(
                    "Failed to log in, are you sure your user / password are correct"
                )
                raise WFCredentialError()
            else:
                raise WFError()

    def _login_ws(self):
        # The following is needed to allow legacy negotiation because
        # WF is kind of slow in updating infrastructure
        sslopt = {}
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        sslopt.update({"context": ctx})

        self.ws = websocket.create_connection(
            self.ws_url, timeout=TIMEOUT, sslopt=sslopt
        )
        login = {
            "cmd": "login",
            "tid": self.tid,
            "source": "consumer dashboard",
            "sessionid": self.sessionid,
        }
        self.ws.send(json.dumps(login))
        # TODO(sdague): we should probably check the response, but
        # it's not clear anything is useful in it.
        recv = self.ws.recv()
        data = json.loads(recv)
        _LOGGER.debug("Login response: %s" % data)

        locations = data["locations"]
        location = None

        if isinstance(self.location, int):
            try:
                location = locations[self.location]
            except Exception:
                raise WFError(
                    "Location index out of range. Max index is {}".format(
                        len(locations) - 1
                    )
                )
        elif isinstance(self.location, str):
            for index, location_data in enumerate(locations):
                location_description = location_data.get("description")
                if location_description == self.location:
                    location = locations[index]
                    break

            if not location:
                raise WFError("Unable to find location: {}".format(self.location))
        else:
            raise WFError(
                "Unknown location type ({}): {}. Should be int or str".format(
                    type(self.location), self.location
                )
            )

        gateways = location["gateways"]
        device = None

        if isinstance(self.device, int):
            try:
                device = gateways[self.device]
            except Exception:
                raise WFError(
                    "Device index out of range. Max index is {}".format(
                        len(gateways) - 1
                    )
                )
        elif isinstance(self.device, str):
            for index, gateway_data in enumerate(gateways):
                gateway_gwid = gateway_data.get("gwid")
                gateway_description = gateway_data.get("description")
                if gateway_gwid == self.device or gateway_description == self.device:
                    device = gateways[index]
                    break

            if not device:
                raise WFError("Unable to find device: {}".format(self.device))
        else:
            raise WFError(
                "Unknown device type ({}): {}. Should be int or str".format(
                    type(self.location), self.location
                )
            )

        self.gwid = device["gwid"]
        self.next_tid()

    def login(self):
        self._get_session_id()
        # reset the transaction id if we start over
        self.tid = 1
        self._login_ws()

    def _abort(self, *args, **kwargs):
        _LOGGER.warning("Timeout on websocket request. Aborting websocket")
        try:
            self.ws.abort()
        except Exception:
            _LOGGER.exception("Can't abort, this might be interesting....")

    def _ws_read(self):
        req = copy.deepcopy(DATA_REQUEST)
        req["tid"] = self.tid
        req["awlid"] = self.gwid

        _LOGGER.debug("Req: %s" % req)
        timer = threading.Timer(10.0, self._abort, [self])
        timer.start()
        self.ws.send(json.dumps(req))
        _LOGGER.debug("Successful send")
        data = self.ws.recv()
        _LOGGER.debug("Successful recv")
        timer.cancel()
        return data

    def read(self):
        try:
            data = self._ws_read()
            self.next_tid()
            datadecoded = json.loads(data)
            _LOGGER.debug("Resp: %s" % datadecoded)
            if not datadecoded["err"]:
                return WFReading(datadecoded)
            else:
                raise WFError(datadecoded["err"])
        except websocket.WebSocketConnectionClosedException:
            _LOGGER.exception("Websocket closed, probably from a timeout")
            raise WFWebsocketClosedError()
        except ValueError:
            _LOGGER.exception("Unable to decode data as json: {}".format(data))
            raise WFWebsocketClosedError()
        except Exception:
            _LOGGER.exception("Unknown exception, socket probably failed")
            raise WFWebsocketClosedError()

    def read_with_retry(self):
        while self.fails <= self.max_fails:
            try:
                if self.fails >= 1:
                    self.login()
                    _LOGGER.debug("Reconnected to furnace")
                data = self.read()
                self.fails = 0
                return data
            except requests.exceptions.RequestException:
                self.fails = self.fails + 1
                _LOGGER.exception("relogin failed, trying again")
                time.sleep(self.fails * ERROR_INTERVAL)
            except WFWebsocketClosedError:
                self.fails = self.fails + 1
                _LOGGER.exception("websocket read failed, reconnecting")
                time.sleep(self.fails * ERROR_INTERVAL)
        raise WFWebsocketClosedError("Failed to refresh credentials after retries")

    def get_energy_data(
        self, start_date, end_date, frequency="1H", timezone_str="America/New_York"
    ):
        """Get energy data for a date range.

        Args:
            start_date: Start date as string in YYYY-MM-DD format
            end_date: End date as string in YYYY-MM-DD format
            frequency: Data frequency - "1D" (daily), "1H" (hourly), or "15min" (15 minutes)
            timezone_str: Timezone string (e.g., "America/New_York")

        Returns:
            WFEnergyData object containing energy readings

        Raises:
            WFCredentialError: If not logged in or session invalid
            WFError: If API request fails
        """
        if not self.sessionid or not self.gwid:
            raise WFCredentialError("Must login before getting energy data")

        # Validate frequency
        valid_frequencies = ["1D", "1H", "15min"]
        if frequency not in valid_frequencies:
            raise ValueError(f"Invalid frequency. Must be one of {valid_frequencies}")

        # Build the API URL
        url = (
            f"{self.base_url}/api.php/v2/gateway/{self.gwid}/energy"
            f"?freq={frequency}&start={start_date}&timezone={timezone_str}&end={end_date}"
        )

        headers = {
            "user-agent": USER_AGENT,
        }

        cookies = {
            "sessionid": self.sessionid,
            "legal-acknowledge": "yes",
        }

        _LOGGER.debug(f"Requesting energy data from: {url}")

        try:
            res = requests.get(
                url,
                headers=headers,
                cookies=cookies,
                timeout=TIMEOUT,
            )
            res.raise_for_status()
            data = res.json()
            _LOGGER.debug(f"Received energy data: {len(data.get('index', []))} records")
            return WFEnergyData(data)
        except requests.exceptions.HTTPError as e:
            _LOGGER.error(f"HTTP error getting energy data: {e}")
            raise WFError(f"Failed to get energy data: {e}")
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Request error getting energy data: {e}")
            raise WFError(f"Failed to get energy data: {e}")
        except (ValueError, KeyError) as e:
            _LOGGER.error(f"Error parsing energy data response: {e}")
            raise WFError(f"Invalid energy data response: {e}")


class WaterFurnace(SymphonyGeothermal):
    def __init__(self, user, passwd, max_fails=5, device=0, location=0):
        super().__init__(
            WF_BASE_URL,
            WF_LOGIN_URL,
            WF_WS_URL,
            user,
            passwd,
            max_fails,
            device,
            location,
        )


class GeoStar(SymphonyGeothermal):
    def __init__(self, user, passwd, max_fails=5, device=0, location=0):
        super().__init__(
            GS_BASE_URL,
            GS_LOGIN_URL,
            GS_WS_URL,
            user,
            passwd,
            max_fails,
            device,
            location,
        )


class WFReading(object):
    def __init__(self, data={}):
        self.zone = data.get("zone", 0)
        self.err = data.get("err", "")
        self.awlid = data.get("awlid", "")
        self.tid = data.get("tid", 0)

        # power (Watts)
        self.compressorpower = data.get("compressorpower")
        self.fanpower = data.get("fanpower")
        self.auxpower = data.get("auxpower")
        self.looppumppower = data.get("looppumppower")
        self.totalunitpower = data.get("totalunitpower")

        # modes (0 - 10)
        self.modeofoperation = data.get("modeofoperation")

        # fan speed (0 - 10)
        self.airflowcurrentspeed = data.get("airflowcurrentspeed")

        # compressor speed
        self.actualcompressorspeed = data.get("actualcompressorspeed")

        # humidity (%)
        self.tstatdehumidsetpoint = data.get("tstatdehumidsetpoint")
        self.tstathumidsetpoint = data.get("tstathumidsetpoint")
        self.tstatrelativehumidity = data.get("tstatrelativehumidity")

        # temps (degrees F)
        self.leavingairtemp = data.get("leavingairtemp")
        self.tstatroomtemp = data.get("tstatroomtemp")
        self.enteringwatertemp = data.get("enteringwatertemp")
        self.leavingwatertemp = data.get("leavingwatertemp")

        # setpoints (degrees F)
        self.tstatheatingsetpoint = data.get("tstatheatingsetpoint")
        self.tstatcoolingsetpoint = data.get("tstatcoolingsetpoint")
        self.tstatactivesetpoint = data.get("tstatactivesetpoint")

        # Loop water flow rate (gallons per minute)
        self.waterflowrate = data.get("waterflowrate")

    @property
    def mode(self):
        return FURNACE_MODE[self.modeofoperation]

    def __repr__(self):
        return (
            "<FurnaceReading power=%d, mode=%s, looptemp=%.1f, "
            "airtemp=%.1f, roomtemp=%.1f, setpoint=%d>"
            % (
                self.totalunitpower,
                self.mode,
                self.enteringwatertemp,
                self.leavingairtemp,
                self.tstatroomtemp,
                self.tstatactivesetpoint,
            )
        )


class WFEnergyReading(object):
    """Represents a single energy data reading for a specific time period."""

    def __init__(self, timestamp_ms, values, columns):
        """Initialize energy reading.

        Args:
            timestamp_ms: Unix timestamp in milliseconds
            values: List of values corresponding to columns
            columns: List of column names
        """
        self.timestamp_ms = timestamp_ms
        # Convert milliseconds to seconds for datetime
        self.timestamp = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)

        # Create a mapping for easy access
        data_dict = {}
        for i, col in enumerate(columns):
            if i < len(values):
                data_dict[col] = values[i]

        # Common fields for all frequencies
        self.total_heat_1 = data_dict.get("total_heat_1")
        self.total_heat_2 = data_dict.get("total_heat_2")
        self.total_cool_1 = data_dict.get("total_cool_1")
        self.total_cool_2 = data_dict.get("total_cool_2")
        self.total_electric_heat = data_dict.get("total_electric_heat")
        self.total_fan_only = data_dict.get("total_fan_only")
        self.total_loop_pump = data_dict.get("total_loop_pump")
        self.total_dehumidification = data_dict.get("total_dehumidification")
        self.total_power = data_dict.get("total_power")
        self.total_records = data_dict.get("total_records")

        # Runtime fields (hour/15min frequency)
        self.runtime_heat_1 = data_dict.get("runtime_heat_1")
        self.runtime_heat_2 = data_dict.get("runtime_heat_2")
        self.runtime_cool_1 = data_dict.get("runtime_cool_1")
        self.runtime_cool_2 = data_dict.get("runtime_cool_2")
        self.runtime_electric_heat = data_dict.get("runtime_electric_heat")
        self.runtime_fan_only = data_dict.get("runtime_fan_only")
        self.runtime_dehumidification = data_dict.get("runtime_dehumidification")
        self.cool_runtime = data_dict.get("cool_runtime")
        self.heat_runtime = data_dict.get("heat_runtime")

        # Daily frequency specific fields
        self.id = data_dict.get("id")
        self.defrost_runtime = data_dict.get("defrost_runtime")
        self.dehumidification_runtime = data_dict.get("dehumidification_runtime")
        self.time_zone = data_dict.get("time_zone")

        # Store all raw data for any custom access
        self._raw_data = data_dict

    def get(self, key, default=None):
        """Get any field by column name.

        Args:
            key: Column name
            default: Default value if key not found

        Returns:
            Value for the given column or default
        """
        return self._raw_data.get(key, default)

    def __repr__(self):
        return f"<WFEnergyReading timestamp={self.timestamp}, power={self.total_power}>"


class WFEnergyData(object):
    """Container for energy data with multiple readings."""

    def __init__(self, data={}):
        """Initialize energy data from API response.

        Args:
            data: Dictionary containing columns, index, and data arrays
        """
        self.columns = data.get("columns", [])
        self.index = data.get("index", [])
        self.data = data.get("data", [])

        # Create reading objects for easier access
        self.readings = []
        for i, timestamp in enumerate(self.index):
            if i < len(self.data):
                reading = WFEnergyReading(timestamp, self.data[i], self.columns)
                self.readings.append(reading)

    def __iter__(self):
        """Allow iteration over readings."""
        return iter(self.readings)

    def __len__(self):
        """Return number of readings."""
        return len(self.readings)

    def __getitem__(self, index):
        """Allow indexed access to readings."""
        return self.readings[index]

    def __repr__(self):
        return (
            f"<WFEnergyData records={len(self.readings)}, "
            f"columns={len(self.columns)}>"
        )
