#!/usr/bin/env python

"""Tests for `waterfurnace` package."""
import logging
import json
import mock
import unittest
import time

import pytest
import websocket

from waterfurnace import waterfurnace as wf

_LOGGER = logging.getLogger(__name__)


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


class FakeWebsocket(object):
    stopped = False
    logged_in = False

    def send(self, *args, **kwargs):
        pass

    def recv(self, *args, **kwargs):
        if not self.logged_in:
            self.logged_in = True
            return FAKE_CONTENT

        for i in range(10):
            if self.stopped:
                raise websocket.WebSocketConnectionClosedException()
            time.sleep(1)

    def abort(self, *args, **kwargs):
        self.stopped = True


class FakeRequest(object):
    def __init__(self, status_code=200, content="", cookies=None):
        self.status_code = status_code
        self.content = content
        if cookies is None:
            self.cookies = {}
        else:
            self.cookies = cookies


class TestTimeout(unittest.TestCase):

    @mock.patch('websocket.create_connection')
    @mock.patch('requests.post')
    def test_increment_read_data(self, mock_req, mock_ws_create):
        mock_req.return_value = FakeRequest(
            cookies={"sessionid": str(mock.sentinel.sessionid)}
        )
        m_ws = FakeWebsocket()

        mock_ws_create.return_value = m_ws

        w = wf.WaterFurnace(
            mock.sentinel.email, mock.sentinel.passwd, str(mock.sentinel.unit))
        w.login()

        with pytest.raises(wf.WFWebsocketClosedError):
            w.read()
