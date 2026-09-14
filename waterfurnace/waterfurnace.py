"""Main module."""

import functools
import logging
import time
from datetime import datetime

import requests

from .const import (
    ACTIVE_MODE,
    DATA_REQUEST,
    ERROR_INTERVAL,
    FAILED_LOGIN,
    FAN_MODE,
    FURNACE_MODE,
    GS_BASE_URL,
    GS_LOGIN_URL,
    GS_WS_URL,
    TIMEOUT,
    USER_AGENT,
    WF_BASE_URL,
    WF_LOGIN_URL,
    WF_WS_URL,
    WRITE_FIELD_SPECS,
    WFCredentialError,
    WFError,
    WFException,
    WFNoDataError,
    WFWebsocketClosedError,
)
from .models import (
    ActiveSettings,
    WFEnergyData,
    WFEnergyReading,
    WFGateway,
    WFLocation,
    WFReading,
)
from .transport import _AuthSession, _WsTransport

__all__ = [
    "ACTIVE_MODE",
    "ActiveSettings",
    "DATA_REQUEST",
    "ERROR_INTERVAL",
    "FAILED_LOGIN",
    "FAN_MODE",
    "FURNACE_MODE",
    "GS_BASE_URL",
    "GS_LOGIN_URL",
    "GS_WS_URL",
    "GeoStar",
    "SymphonyGeothermal",
    "TIMEOUT",
    "USER_AGENT",
    "WFCredentialError",
    "WFEnergyData",
    "WFEnergyReading",
    "WFError",
    "WFException",
    "WFGateway",
    "WFLocation",
    "WFNoDataError",
    "WFReading",
    "WFWebsocketClosedError",
    "WF_BASE_URL",
    "WF_LOGIN_URL",
    "WF_WS_URL",
    "WRITE_FIELD_SPECS",
    "WaterFurnace",
]

_LOGGER = logging.getLogger(__name__)


def _with_retry(func):
    """Retry a websocket-facing method on connection/auth failure.

    The furnace's websocket auth can drop at any point, with no way to know
    in advance when that will happen, so any call onto the wire needs to be
    prepared to relogin and retry rather than fail outright. On
    RequestException/WFWebsocketClosedError, this reconnects (self.login())
    and retries with increasing backoff, up to self.max_fails times.
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        fails = 0
        while fails <= self.max_fails:
            try:
                if fails >= 1:
                    self.login()
                    _LOGGER.debug("Reconnected to furnace")
                return func(self, *args, **kwargs)
            except requests.exceptions.RequestException:  # noqa: PERF203
                fails += 1
                _LOGGER.exception("relogin failed, trying again")
            except WFWebsocketClosedError:
                fails += 1
                _LOGGER.exception("websocket read failed, reconnecting")
            if fails <= self.max_fails:
                time.sleep(fails * ERROR_INTERVAL)
        raise WFWebsocketClosedError("Failed to refresh credentials after retries")

    return wrapper


def _with_http_auth_retry(func):
    """Retry an HTTP-facing method once on a 401/403, after refreshing the
    session.

    Unlike _with_retry (websocket reconnect, backoff, several attempts),
    this is for a single HTTP call whose only recoverable failure is an
    expired session: refresh via self._auth.get_session_id() and retry
    immediately, exactly once. Any other requests.exceptions.HTTPError
    status, or a second 401/403, is not retried; a second 401/403 is raised
    as WFCredentialError instead.
    """

    def _is_auth_failure(exc):
        return exc.response is not None and exc.response.status_code in (401, 403)

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if not _is_auth_failure(e):
                raise
            _LOGGER.debug("Session expired, refreshing and retrying once")
            self._auth.get_session_id()
            try:
                return func(self, *args, **kwargs)
            except requests.exceptions.HTTPError as retry_e:
                if _is_auth_failure(retry_e):
                    _LOGGER.error(
                        "Session refresh did not resolve authentication failure"
                    )
                    raise WFCredentialError() from retry_e
                raise

    return wrapper


class SymphonyGeothermal:
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
        sessionid=None,
    ):
        self.user = user
        self.max_fails = max_fails
        self.locations = None
        self.devices = None
        self.gwid = None
        self.account_id = None
        self._auth = _AuthSession(base_url, login_url, user, passwd, sessionid)
        self._transport = _WsTransport(ws_url, device, location)
        _LOGGER.debug(self)

    def __repr__(self):
        return f"<Symphony user={self.user}>"

    @property
    def location(self):
        return self._transport.location

    @property
    def device(self):
        return self._transport.device

    def login(self):
        self._auth.get_session_id()
        self._transport.login(self._auth.sessionid)
        self.locations = self._transport.locations
        self.devices = self._transport.devices
        self.gwid = self._transport.gwid
        self.account_id = self._transport.account_id

    def _ws_write(self, **kwargs):
        return self._transport.write(**kwargs)

    @_with_retry
    def read(self):
        return self._transport.read()

    # Deprecated alias kept for backwards compatibility: read() has included
    # retry/relogin behavior since 1.9.3, so read_with_retry is no longer a
    # distinct method. Existing callers (e.g. Home Assistant's coordinator)
    # still call it by this name.
    read_with_retry = read

    @staticmethod
    def _validate(field, value):
        """Validate value against the WRITE_FIELD_SPECS entry for field."""
        spec = WRITE_FIELD_SPECS[field]
        label = field.replace("_", " ")
        kind = "numeric" if spec["type"] == (int, float) else "an integer"
        # bool is a subclass of int, so check the exact type rather than
        # isinstance() to keep True/False from passing as 0/1.
        if type(value) not in spec["type"]:
            raise ValueError(f"{label} must be {kind}, got: {type(value).__name__}")
        if value < spec["min"] or value > spec["max"]:
            raise ValueError(
                f"{label} must be {kind} between {spec['min']}-{spec['max']}, "
                f"got: {value}"
            )

    def set_mode(self, mode):
        """Set the active thermostat mode.

        Args:
            mode: Integer 0-4 (Off=0, Auto=1, Cool=2, Heat=3, E-Heat=4)
        """
        self._validate("mode", mode)
        return self._ws_write(activemode_write=mode)

    def set_cooling_setpoint(self, temperature):
        """Set the cooling temperature setpoint.

        Only effective when in Cool or Auto mode.

        Args:
            temperature: Temperature in degrees Fahrenheit (60-90)
        """
        self._validate("cooling_setpoint", temperature)
        return self._ws_write(coolingsp_write=temperature)

    def set_heating_setpoint(self, temperature):
        """Set the heating temperature setpoint.

        Only effective when in Heat, Auto, or E-Heat mode.

        Args:
            temperature: Temperature in degrees Fahrenheit (40-80)
        """
        self._validate("heating_setpoint", temperature)
        return self._ws_write(heatingsp_write=temperature)

    def set_fan_mode(self, mode, intertimeon=None, intertimeoff=None):
        """Set the fan mode.

        Args:
            mode: Integer 0-2 (Auto=0, Continuous=1, Intermittent=2)
            intertimeon: Minutes on-time (1-60), required when mode=2
            intertimeoff: Minutes off-time (1-60), required when mode=2
        """
        self._validate("fan_mode", mode)
        if mode == 2:
            if intertimeon is None or intertimeoff is None:
                raise ValueError(
                    "intertimeon and intertimeoff are required for intermittent mode"
                )
            self._validate("intertimeon", intertimeon)
            self._validate("intertimeoff", intertimeoff)
            return self._ws_write(
                fanmode_write=mode,
                intertimeon_write=intertimeon,
                intertimeoff_write=intertimeoff,
            )
        else:
            if intertimeon is not None or intertimeoff is not None:
                raise ValueError(
                    "intertimeon and intertimeoff are only valid for intermittent mode"
                )
            return self._ws_write(fanmode_write=mode)

    def set_humidity(self, humidity):
        """Set the humidification target.

        Reads current sensor values first to preserve existing
        humidity_offset_settings and dehumidification setpoint.

        Args:
            humidity: Target humidity percentage (15-95)
        """
        self._validate("humidity", humidity)
        reading = self.read()
        return self._ws_write(
            humidity_offset_settings=reading.raw_humidity_offset_settings,
            dehumid_humid_sp={
                "dehumidification": reading.tstatdehumidsetpoint,
                "humidification": humidity,
            },
        )

    @_with_http_auth_retry
    def _request_energy_data(self, start_date, end_date, frequency, timezone_str):
        """Fetch and parse one energy-data response.

        Raises requests.exceptions.HTTPError (uncaught) for a non-auth HTTP
        failure, or WFCredentialError if a 401/403 survives the decorator's
        refresh-and-retry. Also raises WFNoDataError (uncaught) if the
        server returns an empty body, since that's never worth retrying.
        """
        # The API takes a number of periods counting forward from start,
        # rather than an end date, so convert the date range to a count.
        seconds_per_period = {"1D": 86400, "1H": 3600, "15min": 900}
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        periods = (
            int((end_dt - start_dt).total_seconds() // seconds_per_period[frequency])
            + 1
        )

        # Build the API URL
        url = (
            f"{self._auth.base_url}/api/v2/gateway/{self._transport.gwid}/energy"
            f"?awluserkey={self._transport.account_id}&freq={frequency}"
            f"&start={start_date}&timezone={timezone_str}&periods={periods}"
        )

        headers = {
            "user-agent": USER_AGENT,
        }

        cookies = {
            "sessionid": self._auth.sessionid,
            "legal-acknowledge": "yes",
        }

        _LOGGER.debug(f"Requesting energy data from: {url}")

        res = requests.get(
            url,
            headers=headers,
            cookies=cookies,
            timeout=TIMEOUT,
        )
        res.raise_for_status()
        if not res.text.strip():
            raise WFNoDataError(
                f"No energy data available for {start_date} to {end_date}"
            )
        data = res.json()
        _LOGGER.debug(f"Received energy data: {len(data.get('index', []))} records")
        return WFEnergyData(data)

    def get_energy_data(
        self, start_date, end_date, frequency="1H", timezone_str="America/New_York"
    ):
        """Get energy data for a date range.

        Args:
            start_date: Start date as string in YYYY-MM-DD format
            end_date: End date as string in YYYY-MM-DD format
            frequency: Data frequency - "1D" (daily),
                       "1H" (hourly), or "15min" (15 minutes)
            timezone_str: Timezone string (e.g., "America/New_York")

        Returns:
            WFEnergyData object containing energy readings

        Raises:
            WFCredentialError: If not logged in, or if the session has
                expired and a refresh-and-retry also fails to authenticate
            WFError: If API request fails
        """
        if not self._auth.sessionid or not self._transport.gwid:
            raise WFCredentialError("Must login before getting energy data")

        # Validate frequency
        valid_frequencies = ["1D", "1H", "15min"]
        if frequency not in valid_frequencies:
            raise ValueError(f"Invalid frequency. Must be one of {valid_frequencies}")

        try:
            return self._request_energy_data(
                start_date, end_date, frequency, timezone_str
            )
        except (WFNoDataError, WFCredentialError):
            raise
        except requests.exceptions.HTTPError as e:
            _LOGGER.exception(f"HTTP error getting energy data: {e}")
            raise WFError(f"Failed to get energy data: {e}") from e
        except requests.exceptions.RequestException as e:
            _LOGGER.exception(f"Request error getting energy data: {e}")
            raise WFError(f"Failed to get energy data: {e}") from e
        except (ValueError, KeyError) as e:
            _LOGGER.exception(f"Error parsing energy data response: {e}")
            raise WFError(f"Invalid energy data response: {e}") from e


class WaterFurnace(SymphonyGeothermal):
    def __init__(self, user, passwd, max_fails=5, device=0, location=0, sessionid=None):
        super().__init__(
            WF_BASE_URL,
            WF_LOGIN_URL,
            WF_WS_URL,
            user,
            passwd,
            max_fails,
            device,
            location,
            sessionid=sessionid,
        )


class GeoStar(SymphonyGeothermal):
    def __init__(self, user, passwd, max_fails=5, device=0, location=0, sessionid=None):
        super().__init__(
            GS_BASE_URL,
            GS_LOGIN_URL,
            GS_WS_URL,
            user,
            passwd,
            max_fails,
            device,
            location,
            sessionid=sessionid,
        )
