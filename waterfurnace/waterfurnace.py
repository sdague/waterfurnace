# -*- coding: utf-8 -*-

"""Main module."""
import json

import requests
import websocket


USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/42.0.2311.90 Safari/537.36")
WF_LOGIN_URL = 'https://symphony.mywaterfurnace.com/account/login'

FURNACE_MODE = (
    'Standby',
    'Fan Only',
    'Cooling 1',
    'Cooling 2',
    'Reheat',
    'Heating 1',
    'Heating 2',
    'E-Heat',
    'Aux Heat',
    'Lockout')


class WaterFurnace(object):

    def __init__(self, user, passwd, unit):
        self.user = user
        self.passwd = passwd
        self.unit = unit
        self.session_id = None

    def _get_session_id(self):
        data = dict(emailaddress=self.user, password=self.passwd, op="login")
        headers = {"user-agent": USER_AGENT}
        res = requests.post(WF_LOGIN_URL, data=data, headers=headers,
                            allow_redirects=False)
        self.sessionid = res.cookies["sessionid"]

    def _login_ws(self):
        self.ws = websocket.create_connection(
            "wss://awlclientproxy.mywaterfurnace.com/")
        login = {"cmd": "login", "tid": 2, "source": "consumer dashboard",
                 "sessionid": self.sessionid}
        self.ws.send(json.dumps(login))
        # TODO(sdague): we should probably check the response, but
        # it's not clear anything is useful in it.
        self.ws.recv()

    def login(self):
        self._get_session_id()
        self._login_ws()

    def read(self):
        req = {
            "cmd": "read",
            "tid": 3,
            "awlid": self.unit,
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
                "AWLTStatType"],
            "source": "consumer dashboard"}
        self.ws.send(json.dumps(req))
        data = self.ws.recv()
        datadecoded = json.loads(data)
        return WFReading(datadecoded)


class WFReading(object):

    def __init__(self, data={}):
        self.zone = data.get('zone', 0)
        self.err = data.get('err', '')
        self.awlid = data.get('awlid', '')
        self.tid = data.get('tid', 0)

        # power (Watts)
        self.compressorpower = data.get('compressorpower')
        self.fanpower = data.get('fanpower')
        self.auxpower = data.get('auxpower')
        self.looppumppower = data.get('looppumppower')
        self.totalunitpower = data.get('totalunitpower')

        # modes (0 - 10)
        self.modeofoperation = data.get('modeofoperation')

        # fan speed (0 - 10)
        self.airflowcurrentspeed = data.get('airflowcurrentspeed')

        # humidity (%)
        self.tstatdehumidsetpoint = data.get('tstatdehumidsetpoint')
        self.tstathumidsetpoint = data.get('tstathumidsetpoint')
        self.tstatrelativehumidity = data.get('tstatrelativehumidity')

        # temps (degrees F)
        self.leavingairtemp = data.get('leavingairtemp')
        self.tstatroomtemp = data.get('tstatroomtemp')
        self.enteringwatertemp = data.get('enteringwatertemp')

        # setpoints (degrees F)
        self.tstatheatingsetpoint = data.get('tstatheatingsetpoint')
        self.tstatcoolingsetpoint = data.get('tstatcoolingsetpoint')
        self.tstatactivesetpoint = data.get('tstatactivesetpoint')

    @property
    def mode(self):
        return FURNACE_MODE[self.modeofoperation]

    def __str__(self):
        return ("<FurnaceReading power=%d, mode=%s, looptemp=%.1f, "
                "airtemp=%.1f, roomtemp=%.1f, setpoint=%d>" % (
                    self.totalunitpower,
                    self.mode,
                    self.enteringwatertemp,
                    self.leavingairtemp,
                    self.tstatroomtemp,
                    self.tstatactivesetpoint))
