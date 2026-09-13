#!/usr/bin/env python

"""Tests for `waterfurnace` package."""

import json
import logging
import time
import unittest
from unittest import mock

import pytest
import websocket

from waterfurnace import waterfurnace as wf

_LOGGER = logging.getLogger(__name__)


FAKE_RESPONSE = {
    "err": "",
    "key": 1234,
    "locations": [{"gateways": [{"gwid": "123456"}]}],
}


FAKE_CONTENT = json.dumps(FAKE_RESPONSE)


class FakeWebsocket:
    stopped = False
    logged_in = False

    def send(self, *args, **kwargs):
        pass

    def recv(self, *args, **kwargs):
        if not self.logged_in:
            self.logged_in = True
            return FAKE_CONTENT

        for _ in range(10):
            if self.stopped:
                raise websocket.WebSocketConnectionClosedException()
            time.sleep(1)

    def abort(self, *args, **kwargs):
        self.stopped = True


LOGIN_PAGE = '<input name="_token" value="fake-csrf-token" />'


class FakeRequest:
    def __init__(self, status_code=200, content="", cookies=None, text=LOGIN_PAGE):
        self.status_code = status_code
        self.content = content
        self.text = text
        if cookies is None:
            self.cookies = {}
        else:
            self.cookies = cookies

    def raise_for_status(self):
        pass


class TestTimeout(unittest.TestCase):
    @mock.patch("time.sleep")
    @mock.patch("websocket.create_connection")
    @mock.patch("requests.get")
    @mock.patch("requests.post")
    def test_increment_read_data(self, mock_req, mock_get, mock_ws_create, mock_sleep):
        mock_get.return_value = FakeRequest()
        mock_req.return_value = FakeRequest(
            cookies={"sessionid": str(mock.sentinel.sessionid)}
        )
        m_ws = FakeWebsocket()

        mock_ws_create.return_value = m_ws

        # max_fails=0 keeps this test focused on a single read's abort-timer
        # behavior, without also exercising the retry loop.
        w = wf.WaterFurnace(mock.sentinel.email, mock.sentinel.passwd, max_fails=0)
        w.login()

        with pytest.raises(wf.WFWebsocketClosedError):
            w.read()
