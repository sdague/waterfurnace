#!/usr/bin/env python

"""Tests for `waterfurnace` package."""

import json
import mock
import unittest

import pytest

from waterfurnace import waterfurnace as wf


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
            mock.sentinel.email, mock.sentinel.passwd, mock.sentinel.unit)
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
            mock.sentinel.email, mock.sentinel.passwd, mock.sentinel.unit)
        with pytest.raises(wf.WFCredentialError):
            w.login()

    @mock.patch('requests.post')
    def test_success_get_session_id(self, mock_req):
        mock_req.return_value = FakeRequest(
            cookies={"sessionid": mock.sentinel.sessionid}
        )
        w = wf.WaterFurnace(
            mock.sentinel.email, mock.sentinel.passwd, mock.sentinel.unit)
        w._get_session_id()
        assert w.sessionid == mock.sentinel.sessionid

    @mock.patch('websocket.create_connection')
    @mock.patch('requests.post')
    def test_success_login(self, mock_req, mock_ws_create):
        mock_req.return_value = FakeRequest(
            cookies={"sessionid": str(mock.sentinel.sessionid)}
        )
        m_ws = mock.MagicMock()
        mock_ws_create.return_value = m_ws

        w = wf.WaterFurnace(
            mock.sentinel.email, mock.sentinel.passwd, mock.sentinel.unit)
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
        m_ws = mock.MagicMock()
        # we need to give the json return something non magic
        # otherwise it can't deserialize
        m_ws.recv.return_value = '{"a": "b"}'
        mock_ws_create.return_value = m_ws

        w = wf.WaterFurnace(
            mock.sentinel.email, mock.sentinel.passwd, str(mock.sentinel.unit))
        w.login()
        w.read()
        w.read()
        w.read()
        assert w.tid == 5
