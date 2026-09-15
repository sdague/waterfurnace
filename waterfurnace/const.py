"""Constants and exceptions shared across the waterfurnace package."""

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

ACTIVE_MODE = (
    "Off",
    "Auto",
    "Cool",
    "Heat",
    "E-Heat",
)

FAN_MODE = (
    "Auto",
    "Continuous",
    "Intermittent",
)

FAILED_LOGIN = (
    "Your login failed. Please check your email address / password and try again."
)

TIMEOUT = 30
ERROR_INTERVAL = 300

# How long to wait for a websocket send/recv round trip before aborting the
# connection, in _WsTransport._ws_abort_timer. Kept shorter than TIMEOUT
# (the HTTP request timeout) since a hung websocket should be detected and
# recovered from faster than a plain HTTP call is allowed to block.
WS_ABORT_TIMEOUT = 10.0

# Poll interval for the CLI's `sensors --continuous` loop, in seconds. No
# server-side requirement drives this value; it's just a reasonable human-
# readable cadence for watching live sensor data.
CONTINUOUS_READ_INTERVAL = 15

# Range specs for the scalar arguments accepted by the set_* write methods.
# "type" is always a tuple of the exact types accepted; bool is deliberately
# never included, since bool is a subclass of int and would otherwise pass
# an int-only check as if True/False were 1/0.
WRITE_FIELD_SPECS = {
    "mode": {"min": 0, "max": 4, "type": (int,)},
    "cooling_setpoint": {"min": 60, "max": 90, "type": (int, float)},
    "heating_setpoint": {"min": 40, "max": 80, "type": (int, float)},
    "fan_mode": {"min": 0, "max": 2, "type": (int,)},
    "humidity": {"min": 15, "max": 95, "type": (int,)},
    "intertimeon": {"min": 1, "max": 60, "type": (int,)},
    "intertimeoff": {"min": 1, "max": 60, "type": (int,)},
}

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


class WFNoDataError(WFException):
    pass
