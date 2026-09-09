#!/usr/bin/env python3
"""Check whether WaterFurnace/GeoStar's websocket backend still requires
legacy TLS renegotiation.

waterfurnace.waterfurnace._login_ws() sets OP_LEGACY_SERVER_CONNECT on the
SSL context because their websocket server has an outdated TLS stack that
fails a standard handshake with UNSAFE_LEGACY_RENEGOTIATION_DISABLED. This
script attempts a plain, non-legacy TLS connection to check whether that
workaround is still necessary. Run it standalone (no project deps needed)
whenever we want to check if we can drop the workaround.
"""

import socket
import ssl
import sys

HOSTS = {
    "waterfurnace": "awlclientproxy.mywaterfurnace.com",
    "geostar": "awlclientproxy.mygeostar.com",
}


def check_host(host):
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    try:
        with socket.create_connection((host, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host):
                return True, None
    except (ssl.SSLError, OSError) as e:
        return False, str(e)


def main():
    any_legacy_required = False
    for name, host in HOSTS.items():
        ok, error = check_host(host)
        if ok:
            print(f"{name} ({host}): OK - standard TLS handshake succeeded")
            print("  -> legacy renegotiation workaround may no longer be needed")
        else:
            any_legacy_required = True
            print(f"{name} ({host}): FAILED - {error}")
            print("  -> legacy renegotiation workaround is still required")

    return 1 if any_legacy_required else 0


if __name__ == "__main__":
    sys.exit(main())
