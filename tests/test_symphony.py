#!/usr/bin/env python

"""Tests for `waterfurnace` package."""

import json
import mock
import unittest

import pytest

from waterfurnace import waterfurnace as wf

FAKE_RESPONSE = {
    "err": "",
    "locations": [
        {"gateways": [
            {"gwid": "123456"}
        ]
        }
    ]
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

    @mock.patch('requests.post')
    def test_unknown_failure(self, mock_req):
        mock_req.return_value = FakeRequest(
            content="Error")
        w = wf.WaterFurnace(
            mock.sentinel.email, mock.sentinel.passwd)
        with pytest.raises(wf.WFError):
            w.login()

    @mock.patch('requests.post')
    def test_failled_login(self, mock_req):
        LOGIN_MSG = (
            "Something went wrong. Your login failed. "
            "Please check your email address / password and try again."
            " <br/>")

        mock_req.return_value = FakeRequest(
            content=LOGIN_MSG)
        w = wf.WaterFurnace(
            mock.sentinel.email, mock.sentinel.passwd)
        with pytest.raises(wf.WFCredentialError):
            w.login()

    @mock.patch('requests.post')
    def test_success_get_session_id(self, mock_req):
        mock_req.return_value = FakeRequest(
            cookies={"sessionid": mock.sentinel.sessionid}
        )
        w = wf.WaterFurnace(
            mock.sentinel.email, mock.sentinel.passwd)
        w._get_session_id()
        assert w.sessionid == mock.sentinel.sessionid

    @mock.patch('websocket.create_connection')
    @mock.patch('websocket.recv')
    @mock.patch('requests.post')
    def test_success_login(self, mock_req, m_recv, mock_ws_create):
        mock_req.return_value = FakeRequest(
            cookies={"sessionid": str(mock.sentinel.sessionid)},
        )
        m_ws = mock.MagicMock()
        m_ws.recv.return_value = FAKE_CONTENT
        mock_ws_create.return_value = m_ws

        w = wf.WaterFurnace(
            str(mock.sentinel.email), str(mock.sentinel.passwd))
        w.login()
        assert m_ws.method_calls[0] == mock.call.send(
            json.dumps({"cmd": "login", "tid": 1,
                        "source": "consumer dashboard",
                        "sessionid": "sentinel.sessionid"}))
        assert m_ws.method_calls[1] == mock.call.recv()

    @mock.patch('websocket.create_connection')
    @mock.patch('requests.post')
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

        w = wf.WaterFurnace(
            mock.sentinel.email, mock.sentinel.passwd)
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

    @mock.patch('websocket.create_connection')
    @mock.patch('requests.post')
    def test_increment_read_data(self, mock_req, mock_ws_create):
        mock_req.return_value = FakeRequest(
            cookies={"sessionid": str(mock.sentinel.sessionid)}
        )

        fake_data = json.dumps(
            {"rsp": "read",
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
             "lockoutstatus": {"lockoutstatuscode": 0,
                               "lockedout": 0},
             "lastfault": 15,
             "lastlockout": {"lockoutstatuslast": 0},
             "homeautomationalarm1": 0,
             "homeautomationalarm2": 3,
             "roomtemp": 69,
             "activesettings": {"temporaryoverride": 0,
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
                                "intertimeoff_read": 5},
             "tstatactivesetpoint": 69,
             "tstatmode": 0,
             "tstatheatingsetpoint": 69,
             "tstatcoolingsetpoint": 75,
             "awltstattype": 103})

        m_ws = mock.MagicMock()
        # we need to give the json return something non magic
        # otherwise it can't deserialize
        m_ws.recv.return_value = FAKE_CONTENT
        mock_ws_create.return_value = m_ws

        w = wf.WaterFurnace(
            mock.sentinel.email, mock.sentinel.passwd)
        w.login()

        # Replace the data packet once we get to read
        m_ws.recv.return_value = fake_data

        data = w.read()

        assert data.airflowcurrentspeed == 2
        assert data.mode == "Fan Only"
        assert data.tstathumidsetpoint == 40
        assert data.tstatrelativehumidity == 45
        assert data.enteringwatertemp == 41.4
        assert data.leavingairtemp == 67.7
        assert data.tstatactivesetpoint == 69

    @mock.patch('websocket.create_connection')
    @mock.patch('requests.post')
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
            mock.sentinel.email, mock.sentinel.passwd, str(mock.sentinel.unit))
        w.login()

        # Replace the data content once we get to read
        m_ws.recv.return_value = json.dumps(
            {"rsp": "read",
             "tid": 20,
             "err": "something went wrong"})

        mock_ws_create.return_value = m_ws
        with pytest.raises(wf.WFWebsocketClosedError):
            w.read()
