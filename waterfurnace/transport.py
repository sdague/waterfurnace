"""HTTP-auth and websocket transport collaborators used by SymphonyGeothermal."""

import contextlib
import copy
import json
import logging
import re
import ssl
import threading

import requests
import websocket

from .const import (
    DATA_REQUEST,
    FAILED_LOGIN,
    TIMEOUT,
    USER_AGENT,
    WS_ABORT_TIMEOUT,
    WFCredentialError,
    WFError,
    WFWebsocketClosedError,
)
from .models import WFLocation, WFReading

_LOGGER = logging.getLogger(__name__)


class _AuthSession:
    """Owns the HTTP session-id: obtaining, validating, and holding it.

    Pure HTTP concern, with no knowledge of the websocket connection that
    the session id is later used to authenticate.
    """

    def __init__(self, base_url, login_url, user, passwd, sessionid=None):
        self.base_url = base_url
        self.login_url = login_url
        self.user = user
        self.passwd = passwd
        self.sessionid = sessionid

    def get_session_id(self):
        """Ensure self.sessionid is set to a valid session, refreshing if needed."""
        if self.sessionid:
            try:
                self._check_session_id()
            except WFCredentialError:
                self._get_session_id()
        else:
            self._get_session_id()

    def _check_session_id(self):
        """Verify self.sessionid is still valid.

        Raises WFCredentialError if the session has expired or the server's
        response can't be parsed as the expected user payload, so callers
        can fall back to a fresh login.
        """
        _LOGGER.debug("Checking existing session.")
        headers = {
            "user-agent": USER_AGENT,
        }
        res = requests.get(
            f"{self.base_url}/user",
            headers=headers,
            cookies={
                "legal-acknowledge": "yes",
                "sessionid": self.sessionid,
            },
            timeout=TIMEOUT,
            allow_redirects=False,
        )
        try:
            res.json()["emailaddress"]
        except (KeyError, ValueError) as e:
            # ValueError covers requests' JSONDecodeError, raised when the
            # server returns a non-JSON body (e.g. an HTML 404 page) instead
            # of the expected user payload. Session expiry is routine and
            # the caller recovers via a fresh login, so this isn't logged
            # at ERROR level.
            _LOGGER.debug("Existing session is not valid A lot of debug info coming...")
            _LOGGER.debug("Response: %s", res)
            _LOGGER.debug("Response Cookies: %s", res.cookies)
            _LOGGER.debug("Response Content: %s", res.content)
            raise WFCredentialError() from e

    def _get_session_id(self):
        headers = {
            "user-agent": USER_AGENT,
        }
        cookies = {
            "legal-acknowledge": "yes",
            "energy-base-price": "0.15",
            "temp_unit": "f",
        }

        # The login form is now protected by a Laravel CSRF token, so we
        # have to load the login page first to obtain it.
        login_page = requests.get(
            self.login_url,
            headers=headers,
            cookies=cookies,
            timeout=TIMEOUT,
        )
        login_page.raise_for_status()
        match = re.search(
            r'<input[^>]*name="_token"[^>]*value="([^"]+)"', login_page.text
        ) or re.search(r'<input[^>]*value="([^"]+)"[^>]*name="_token"', login_page.text)
        if not match:
            _LOGGER.debug("Login page content: %s", login_page.text)
            raise WFError("Unable to find CSRF token on login page")
        token = match.group(1)
        cookies.update(dict(login_page.cookies))

        data = dict(
            emailaddress=self.user,
            password=self.passwd,
            op="login",
            redirect="/",
            _token=token,
        )

        res = requests.post(
            self.login_url,
            data=data,
            headers=headers,
            cookies=cookies,
            timeout=TIMEOUT,
            allow_redirects=False,
        )
        try:
            self.sessionid = res.cookies["sessionid"]
        except KeyError as e:
            _LOGGER.exception(
                "Did not find expected session cookie, login failed."
                " A lot of debug info coming..."
            )
            _LOGGER.debug("Response: %s", res)
            _LOGGER.debug("Response Cookies: %s", res.cookies)
            _LOGGER.debug("Response Content: %s", res.content)
            if FAILED_LOGIN.encode() in res.content:
                _LOGGER.error(
                    "Failed to log in, are you sure your user / password are correct"
                )
                raise WFCredentialError() from e
            else:
                raise WFError() from e


class _WsTransport:
    """Owns the websocket connection: login handshake, read, and write.

    Holds tid, ws, gwid, account_id, and the resolved location data, all of
    which only make sense in the context of an established websocket
    session.
    """

    def __init__(self, ws_url, device=0, location=0):
        self.ws_url = ws_url
        self.device = device
        self.location = location
        self.ws = None
        self.gwid = None
        self.tid = 0
        self.locations = None
        self.devices = None
        # Unique ID for the account, regardless of email changes.
        self.account_id = None

    def next_tid(self):
        self.tid = (self.tid + 1) % 100

    @staticmethod
    def _resolve_by_index(selector, items, kind):
        """Resolve an item from a list by integer index.

        Args:
            selector: An int index into items.
            items: The list to resolve from.
            kind: Human-readable name of what's being resolved, for errors.
        """
        try:
            return items[selector]
        except IndexError as e:
            raise WFError(
                f"{kind} index out of range. Max index is {len(items) - 1}"
            ) from e

    def _connect_ws(self):
        # The following is needed to allow legacy negotiation because
        # WF is kind of slow in updating infrastructure
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        sslopt = {"context": ctx}

        self.ws = websocket.create_connection(
            self.ws_url, timeout=TIMEOUT, sslopt=sslopt
        )

    def _send_login_request(self, sessionid):
        login = {
            "cmd": "login",
            "tid": self.tid,
            "source": "consumer dashboard",
            "sessionid": sessionid,
        }
        return self.send(login)

    def _parse_login_response(self, data):
        """Pull account_id/locations out of a decoded login response."""
        _LOGGER.debug("Login response: %s", data)
        try:
            if data["err"]:
                raise WFError(data["err"])
            account_id = data["key"]
            locations = data["locations"]
        except KeyError as e:
            _LOGGER.exception("Login response missing expected field: %s", data)
            raise WFWebsocketClosedError() from e

        self.account_id = account_id
        return locations

    def _resolve_gwid(self, locations):
        """Resolve self.location/self.device against locations and set gwid.

        Args:
            locations: Raw location dicts straight from the login response
                (see _parse_login_response), not WFLocation objects.
        """
        location = self._resolve_by_index(self.location, locations, "Location")

        try:
            gateways = location["gateways"]
        except KeyError as e:
            _LOGGER.exception(
                "Location missing expected 'gateways' field: %s", location
            )
            raise WFWebsocketClosedError() from e

        device = self._resolve_by_index(self.device, gateways, "Device")

        self.gwid = device["gwid"]

    def _resolve_devices(self, locations):
        """Resolve self.location against locations and return its WFGateways.

        Args:
            locations: A list of WFLocation objects (see self.locations),
                not the raw dicts _resolve_gwid expects.
        """
        target_location = self._resolve_by_index(self.location, locations, "Location")
        return target_location.gateways

    def login(self, sessionid):
        """Establish the websocket connection and log in with sessionid."""
        # reset the transaction id if we start over
        self.tid = 1
        self._connect_ws()
        data = self._send_login_request(sessionid)
        raw_locations = self._parse_login_response(data)
        self._resolve_gwid(raw_locations)
        self.locations = [WFLocation(loc) for loc in raw_locations]
        self.devices = self._resolve_devices(self.locations)

    def _abort(self, *args, **kwargs):
        _LOGGER.warning("Timeout on websocket request. Aborting websocket")
        try:
            self.ws.abort()
        except Exception:
            _LOGGER.exception("Can't abort, this might be interesting....")

    @contextlib.contextmanager
    def _ws_abort_timer(self):
        """Abort the websocket if the enclosed block doesn't finish in time."""
        timer = threading.Timer(WS_ABORT_TIMEOUT, self._abort, [self])
        timer.start()
        try:
            yield
        finally:
            timer.cancel()

    def send(self, req):
        """Send a request and return its decoded response.

        Bumps tid and translates websocket/JSON failures into
        WFWebsocketClosedError.
        """
        _LOGGER.debug("Req: %s", req)
        try:
            with self._ws_abort_timer():
                self.ws.send(json.dumps(req))
                _LOGGER.debug("Successful send")
                data = self.ws.recv()
                _LOGGER.debug("Successful recv")
            datadecoded = json.loads(data)
            self.next_tid()
            return datadecoded
        except websocket.WebSocketConnectionClosedException as e:
            # Routine: the server closes idle connections, and the caller
            # (_with_retry) reconnects and retries. Not worth an ERROR-level
            # traceback.
            _LOGGER.debug("Websocket closed, probably from a timeout", exc_info=True)
            raise WFWebsocketClosedError() from e
        except ValueError as e:
            _LOGGER.exception("Unable to decode data as json: %s", data)
            raise WFWebsocketClosedError() from e
        except Exception as e:
            _LOGGER.exception("Unknown exception, socket probably failed")
            raise WFWebsocketClosedError() from e

    def write(self, **kwargs):
        req = {
            "cmd": "write",
            "tid": self.tid,
            "awlid": self.gwid,
            "source": "tstat",
        }
        req.update(kwargs)

        _LOGGER.debug("Write req: %s", req)
        datadecoded = self.send(req)
        _LOGGER.debug("Write resp: %s", datadecoded)
        if datadecoded["err"]:
            raise WFError(datadecoded["err"])
        return datadecoded

    def read(self):
        req = copy.deepcopy(DATA_REQUEST)
        req["tid"] = self.tid
        req["awlid"] = self.gwid

        datadecoded = self.send(req)
        _LOGGER.debug("Resp: %s", datadecoded)
        if datadecoded["err"]:
            raise WFError(datadecoded["err"])
        return WFReading(datadecoded)
