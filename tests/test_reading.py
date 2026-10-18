"""Tests for WFReading field parsing and hardware-dependent read requests."""

import copy
import json
from unittest import mock

import pytest

from waterfurnace import waterfurnace as wf
from waterfurnace.transport import _WsTransport

# A read response captured from a Dual Capacity unit (awlabctype 2).
READ_RESPONSE = {
    "rsp": "read",
    "tid": 2,
    "err": "",
    "zone": 0,
    "awlid": "ABC123456",
    "compressorpower": 0,
    "fanpower": 0,
    "auxpower": 0,
    "looppumppower": 0,
    "totalunitpower": 0,
    "awlabctype": 2,
    "modeofoperation": 0,
    "actualcompressorspeed": 0,
    "airflowcurrentspeed": 0,
    "auroraoutputeh1": 0,
    "auroraoutputeh2": 0,
    "auroraoutputcc": 0,
    "auroraoutputcc2": 0,
    "tstatdehumidsetpoint": 45,
    "tstathumidsetpoint": 48,
    "tstatrelativehumidity": 63,
    "leavingairtemp": 67.4,
    "tstatroomtemp": 68.7,
    "enteringwatertemp": 49.6,
    "aocenteringwatertemp": -999.9,
    "leavingwatertemp": 49.8,
    "waterflowrate": 0,
    "lockoutstatus": {"lockoutstatuscode": 0, "lockedout": 0},
    "lastfault": 15,
    "lastlockout": {"lockoutstatuslast": 0},
    "humidity_offset_settings": {
        "humidity_offset": 0,
        "humdity_control_option": 1,
        "dehumidification_mode": 0,
        "humidification_mode": 0,
    },
    "humidity": 63,
    "outdoorair": 55.2,
    "homeautomationalarm1": 0,
    "homeautomationalarm2": 3,
    "roomtemp": 68,
    "activesettings": {"activemode": 3, "heatingsp_read": 68},
    "tstatactivesetpoint": 68,
    "tstatmode": 0,
    "tstatheatingsetpoint": 68,
    "tstatcoolingsetpoint": 71,
    "awltstattype": 103,
}


def reading(**overrides):
    data = copy.deepcopy(READ_RESPONSE)
    data.update(overrides)
    return wf.WFReading(data)


class TestFurnaceMode:
    def test_existing_labels_unchanged(self):
        # Home Assistant maps these exact strings to HVAC actions.
        assert wf.FURNACE_MODE[:10] == (
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

    @pytest.mark.parametrize(
        ("value", "label"),
        [
            (10, "Unknown"),
            (11, "Defrost"),
            (12, "Hydronic"),
            (13, "Hydronic with Air Heating"),
            (14, "EH Hydronic Transition"),
        ],
    )
    def test_hydronic_and_defrost_modes(self, value, label):
        assert reading(modeofoperation=value).mode == label

    @pytest.mark.parametrize("value", [15, -1, None, True])
    def test_unknown_mode_is_none(self, value):
        assert reading(modeofoperation=value).mode is None

    def test_mode_none_when_not_reported(self):
        assert wf.WFReading({}).mode is None

    @pytest.mark.parametrize("value", [5, -1, None])
    def test_unknown_active_mode_is_none(self, value):
        r = reading(activesettings={"activemode": value})
        assert r.activesettings.mode is None
        assert "mode" not in r.as_dict()["activesettings"]


class TestNoSensorValue:
    @pytest.mark.parametrize(
        "name",
        [
            "leavingairtemp",
            "enteringwatertemp",
            "aocenteringwatertemp",
            "leavingwatertemp",
            "outdoorair",
            "load_tank_temp",
            "hotwatertemp",
        ],
    )
    def test_no_sensor_temps_become_none(self, name):
        # Reported but not present: the attribute exists, as None.
        r = reading(**{name: -999.9})
        assert getattr(r, name) is None
        assert r.as_dict()[name] is None

    def test_real_temps_pass_through(self):
        r = reading()
        assert r.leavingairtemp == 67.4
        assert r.enteringwatertemp == 49.6

    def test_raw_keeps_original_value(self):
        assert reading().raw["aocenteringwatertemp"] == -999.9


class TestExposedFields:
    def test_hardware_types(self):
        r = reading()
        assert r.awlabctype == 2
        assert r.awltstattype == 103

    def test_outputs(self):
        r = reading(auroraoutputcc=1, auroraoutputeh2=1)
        assert r.auroraoutputcc == 1
        assert r.auroraoutputcc2 == 0
        assert r.auroraoutputeh1 == 0
        assert r.auroraoutputeh2 == 1

    def test_misc_readings(self):
        r = reading()
        assert r.outdoorair == 55.2
        assert r.humidity == 63
        assert r.roomtemp == 68
        assert r.tstatmode == 0

    def test_lockout_and_fault_fields_flattened(self):
        r = reading(
            lockoutstatus={"lockoutstatuscode": 23, "lockedout": 1},
            lastlockout={"lockoutstatuslast": 7},
        )
        assert r.lockoutstatuscode == 23
        assert r.lockedout == 1
        assert r.lastlockout == 7
        assert r.lastfault == 15

    def test_home_automation_alarms(self):
        r = reading()
        assert r.homeautomationalarm1 == 0
        assert r.homeautomationalarm2 == 3

    def test_unreported_fields_are_not_attributes(self):
        r = wf.WFReading({"modeofoperation": 0})
        for attr in (
            "awlabctype",
            "outdoorair",
            "lockoutstatuscode",
            "lockedout",
            "lastlockout",
            "lastfault",
            "load_tank_temp",
            "tstatroomtemp",
        ):
            assert not hasattr(r, attr), attr
            assert attr not in r.as_dict(), attr
        assert r.modeofoperation == 0

    def test_unreported_active_settings_are_not_attributes(self):
        r = reading(activesettings={"activemode": 3})
        assert r.activesettings.activemode == 3
        assert not hasattr(r.activesettings, "heatingsp_read")
        assert r.as_dict()["activesettings"] == {"activemode": 3, "mode": "Heat"}

    def test_lockout_values_absent_from_nested_dicts(self):
        r = reading(lockoutstatus={"lockedout": 1}, lastlockout={})
        assert r.lockedout == 1
        assert not hasattr(r, "lockoutstatuscode")
        assert not hasattr(r, "lastlockout")

    def test_load_tank_temp(self):
        assert reading(load_tank_temp=101.5).load_tank_temp == 101.5
        assert reading(load_tank_temp=-999.9).load_tank_temp is None

    def test_dhw(self):
        r = reading(hotwatertemp=76.6, dhwsetpoint=140)
        assert r.hotwatertemp == 76.6
        assert r.dhwsetpoint == 140
        assert not hasattr(reading(), "hotwatertemp")
        assert not hasattr(reading(), "dhwsetpoint")


class TestAsDict:
    def test_contains_fields_and_derived_modes(self):
        d = reading().as_dict()
        assert d["outdoorair"] == 55.2
        assert d["mode"] == "Standby"
        assert d["activesettings"]["mode"] == "Heat"
        assert d["activesettings"]["heatingsp_read"] == 68

    def test_excludes_raw(self):
        d = reading().as_dict()
        assert "raw" not in d
        assert "raw_humidity_offset_settings" not in d

    def test_is_json_serializable(self):
        assert json.loads(json.dumps(reading().as_dict()))["mode"] == "Standby"

    def test_empty_response(self):
        d = wf.WFReading({}).as_dict()
        assert d == {"zone": 0, "err": "", "awlid": "", "tid": 0}

    def test_repr_tolerates_missing_values(self):
        # An error payload has none of the numeric fields.
        assert "FurnaceReading" in repr(wf.WFReading({"err": "boom"}))
        assert "ActiveSettings" in repr(wf.WFReading({}).activesettings)


# Attributes Home Assistant's waterfurnace integration reads (climate.py
# directly, sensor.py via getattr); a rename here would break it.
HA_ATTRIBUTES = [
    "mode",
    "totalunitpower",
    "tstatactivesetpoint",
    "leavingairtemp",
    "tstatroomtemp",
    "enteringwatertemp",
    "tstathumidsetpoint",
    "tstatdehumidsetpoint",
    "tstatrelativehumidity",
    "compressorpower",
    "fanpower",
    "auxpower",
    "looppumppower",
    "actualcompressorspeed",
    "airflowcurrentspeed",
    "tstatheatingsetpoint",
    "tstatcoolingsetpoint",
    "leavingwatertemp",
    "waterflowrate",
]


@pytest.mark.parametrize("name", HA_ATTRIBUTES)
def test_home_assistant_attributes_present(name):
    assert hasattr(reading(leavingwatertemp=49.8, waterflowrate=0), name)


def test_home_assistant_active_settings_mode():
    assert reading().activesettings.mode == "Heat"


class TestReadRequestFields:
    def _transport(self, awlabctype):
        t = _WsTransport("wss://example")
        t.awlabctype = awlabctype
        t.gwid = "ABC123456"
        t.send = mock.MagicMock(return_value={"err": ""})
        return t

    def _sent_rlist(self, t):
        t.read()
        return t.send.call_args[0][0]["rlist"]

    def test_default_rlist_for_other_types(self):
        for abctype in (None, 1, 3, 4, 5, 18):
            rlist = self._sent_rlist(self._transport(abctype))
            assert rlist == wf.DATA_REQUEST["rlist"], abctype

    def test_dual_capacity_adds_dhw(self):
        rlist = self._sent_rlist(self._transport(2))
        assert rlist == wf.DATA_REQUEST["rlist"] + ["hotwatertemp", "dhwsetpoint"]

    def test_5_series_3d_adds_load_tank_and_dhw(self):
        rlist = self._sent_rlist(self._transport(24))
        assert rlist == wf.DATA_REQUEST["rlist"] + [
            "load_tank_temp",
            "hotwatertemp",
            "dhwsetpoint",
        ]

    def test_data_request_not_mutated(self):
        before = list(wf.DATA_REQUEST["rlist"])
        self._sent_rlist(self._transport(24))
        assert wf.DATA_REQUEST["rlist"] == before
