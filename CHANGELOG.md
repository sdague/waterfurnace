# Changelog

## [Unreleased]

### Changed
- Split `SymphonyGeothermal`'s HTTP-login and websocket-transport concerns
  into two internal collaborator classes: `_AuthSession` (session-id
  acquisition/validation) and `_WsTransport` (websocket connect, login
  handshake, tid, and read/write framing). `SymphonyGeothermal` now composes
  these via `self._auth`/`self._transport` instead of holding all of their
  state and methods directly. This is an internal structural change with no
  behavior change to the public API (`login()`, `read()`, `locations`,
  `devices`, `gwid`, `account_id`, the `set_*` write methods, and
  `get_energy_data()` all work the same as before, including for existing
  consumers like Home Assistant's `waterfurnace` integration). Some
  lower-level internals that were never part of the documented API (e.g.
  `symphony.tid`, `symphony.sessionid`, `symphony.ws`) are no longer exposed
  directly on `SymphonyGeothermal` and now live on `symphony._transport`/
  `symphony._auth` instead.
- `locations`, `devices`, `gwid`, and `account_id` are now resolved eagerly
  during `login()` and stored as plain attributes, instead of
  `locations`/`devices` being recomputed from raw response data on every
  access. One behavior change: logging into a location that has no gateways
  (and defaults to device index 0) now raises `WFError` from `login()`
  itself, instead of `login()` succeeding and `devices` later evaluating to
  an empty list.
- `_with_retry`'s failure count is now a local variable inside the retry
  loop instead of `self.fails`. It was never read outside that loop, so
  keeping it as instance state served no purpose beyond making it look
  like meaningful object state.
- `set_fan_mode()`'s `intertimeon`/`intertimeoff` type/range checks are now
  driven by `WRITE_FIELD_SPECS`/`_validate()`, the same schema-driven
  mechanism the other write methods already use, instead of their own
  inline `isinstance`/range checks. The "required together when
  `mode=2`"/"forbidden otherwise" relationship between the two arguments
  remains explicit inline logic, since that's a cross-field rule the
  per-field schema doesn't model. One wording change: the `ValueError` for
  an out-of-range or wrong-type `intertimeon`/`intertimeoff` now matches
  the standardized message format used by the other write methods (e.g.
  "intertimeon must be an integer between 1-60, got: X") instead of its
  previous bespoke wording. Valid range is 1-60 minutes; no documented
  hardware limit exists, so this is a sanity ceiling rather than a real
  device constraint.

## [1.9.4] - 2026-09-13

### Fixed
- Restored `read_with_retry()` as an alias for `read()`. It was removed in
  1.9.3 when the retry loop it used to implement became the default
  behavior of `read()` itself, but existing callers (e.g. Home Assistant's
  `waterfurnace` integration) still call it by the old name.

## [1.9.3] - 2026-09-13

### Changed
- Refactored the duplicated location/device selector logic in `_login_ws()`
  into a shared `_resolve_by_index_or_match()` helper, making it easier to
  reason about and test the int-index vs. string-match resolution paths.
- Split `_login_ws()` into `_connect_ws()`, `_send_login_request()`,
  `_parse_login_response()`, and `_resolve_gwid()`, each with a single
  responsibility, so the overall login flow reads as a short linear
  sequence instead of one long method.
- The websocket login response's `key` field (used as `account_id`) is now
  treated as required, the same as `locations`. Real server responses
  always include it, and treating it as optional only meant a missing
  `key` would surface later as a broken request from `get_energy_data()`
  instead of failing clearly at login time.
- Extracted the duplicated timer/send/recv/exception-translation logic
  shared by `_ws_write()` and `read()` into a single `_ws_send()` method,
  with the 10s abort-timer setup/teardown pulled out into a
  `_ws_abort_timer()` context manager so it no longer clutters the main
  send/recv flow. As part of this, `read()` now raises `WFError` (instead
  of `WFWebsocketClosedError`) for a server-reported error, the same as
  `_ws_write()` already did — the two had been inconsistent since
  `read()`'s own `WFError` was accidentally caught and rewrapped by its
  bare `except Exception`. Also fixed: `read()`'s abort timer is now
  reliably cancelled even if `send()`/`recv()` raises (previously only
  `_ws_write()` guaranteed this).
- The websocket login request now also goes through `_ws_send()`, instead
  of `_send_login_request()` doing its own raw send/recv/decode. As a
  result, the login response's `err` field is now actually checked
  (previously never inspected), raising `WFError` with the server's
  message on a login-level error instead of silently proceeding or
  failing later with an opaque `WFWebsocketClosedError` from a missing
  field. One consequence: `read_with_retry()`'s relogin step can now
  raise `WFError` for a server-reported login error (e.g. a revoked
  session); this is intentionally not retried like a transient websocket
  failure, and propagates out of `read_with_retry()` to the caller.
- Extracted the near-identical range-validation logic duplicated across
  `set_mode()`, `set_cooling_setpoint()`, `set_heating_setpoint()`,
  `set_fan_mode()`, and `set_humidity()` into a single `_validate()`
  helper driven by a `WRITE_FIELD_SPECS` table (min/max/accepted-types per
  field). Each field's accepted types are checked by exact type rather than
  `isinstance()`, since `bool` is a subclass of `int` in Python and would
  otherwise let `True`/`False` slip through an int-only check as if they
  were `1`/`0`. The `ValueError` wording for these five is now uniform
  (e.g. "cooling setpoint must be numeric between 60-90, got: X") instead
  of each method having its own slightly different phrasing. One small
  behavior change: `set_cooling_setpoint()`/`set_heating_setpoint()` now
  reject `bool` at the type-check stage, same as the other three methods;
  previously a `bool` was let through the type check (since `isinstance`
  treats it as an `int`) and only rejected later by the range check.
- Grouped `ActiveSettings`'s attributes into labeled sections (mode,
  setpoints, fan, hold/override flags) and normalized `WFEnergyReading`'s
  existing grouping comments to a terser style, matching the
  grouping-comment convention `WFReading` already uses. No behavior
  change.
- Collapsed `read()` and `read_with_retry()` into a single `read()` method.
  The relogin/backoff/retry loop that `read_with_retry()` used to implement
  is now a `_with_retry` decorator applied to `read()`, so the retry
  mechanics live outside `read()`'s main flow instead of duplicating it in
  a second method. `read_with_retry()` is removed. One consequence: every
  caller of `read()` now gets retry/relogin behavior by default, including
  `sensors_cmd`'s continuous-polling loop in the CLI (previously a bare,
  non-retrying `read()` call — likely an oversight, since retrying is
  exactly what that use case wants) and `set_humidity()`'s internal read of
  current state before writing (previously fast-failing; now it can retry
  for up to several minutes on a transient failure before giving up, same
  as any other read). Also fixed: the retry loop no longer sleeps before
  its final, doomed attempt — previously it always slept
  `self.fails * ERROR_INTERVAL` after every failure, including the last
  one right before giving up and raising.
- Documented `_check_session_id()`'s raise-on-invalid-session contract in
  its docstring (raises `WFCredentialError`, which `login()` relies on to
  know when to fall back to a fresh login). No behavior change.

## [1.9.2] - 2026-09-12

### Fixed
- `_login_ws()` no longer crashes uncaught if the websocket login response
  is malformed (non-JSON) or missing the expected `locations`/`gateways`
  fields (e.g. an error response in place of the normal login payload).
  These now raise `WFWebsocketClosedError`, consistent with how `read()`
  and `_ws_write()` already handle bad websocket data, so
  `read_with_retry()`'s existing retry logic picks them up cleanly.

## [1.9.1] - 2026-09-12

### Fixed
- Reusing a stored `sessionid` (session reuse across reconnects, as done by
  long-running consumers like Home Assistant) no longer crashes with an
  uncaught `requests.exceptions.JSONDecodeError`. `_check_session_id()` now
  uses the current `/user` endpoint (the old `/api.php/user` route now
  404s with an HTML page) and also treats any non-JSON or malformed
  response the same as an invalid session, falling back to a fresh login as
  it already did for other failure shapes.

### Added
- `scripts/check_legacy_ssl.py` (and `make check-legacy-ssl`): a standalone,
  dependency-free script to check whether WaterFurnace/GeoStar's websocket
  backend still requires the legacy TLS renegotiation workaround in
  `_login_ws()`, so we can tell when it's safe to remove.

## [1.9.0] - 2026-09-09

### Fixed
- Login now handles the CSRF token required by the Symphony login form. The
  server added this protection, which caused every login attempt (and thus
  `wf sensors`, `wf read`, etc.) to fail with a session cookie error even
  with correct credentials.
- `wf energy` now uses the current `/api/v2/gateway/{gwid}/energy` endpoint
  with the `awluserkey`/`periods` parameters the server now expects, instead
  of the removed `/api.php/v2/...` route with `end`, which always 404'd.
  The public `get_energy_data()` signature and return type are unchanged.

### Changed
- Replaced `black` with `ruff` for formatting and linting (rules: B, UP, I, E, W, F, PERF)
- Replaced `pip`/`tox` with `uv` for local development workflow
- Removed `tox.ini`, `requirements_dev.txt`, `setup.cfg`
- Updated GitHub Actions CI to use `astral-sh/setup-uv`

## [1.8.0] - 2026-04-25

* **Breaking:** `wf read` is replaced by two top-level commands: `wf sensors`
  (live sensor readings) and `wf energy` (historical energy data). The `-e/--energy`
  flag is removed. Use `wf sensors` for what was previously `wf read` and
  `wf energy --start ... --end ...` for what was previously `wf read -e`.

## [1.7.1] - 2026-04-19

* Fix one miss on click behavior tests

## [1.7.0] - 2026-04-19

This release adds experimental write controls to the waterfurnace system. As with everything, use at your own risk.

* Add write control commands: `set_mode`, `set_cooling_setpoint`,
  `set_heating_setpoint`, `set_fan_mode`, and `set_humidity`
* Add `FAN_MODE` constant for fan mode labels (Auto, Continuous, Intermittent)
* `set_humidity` reads current sensor state before writing to preserve
  existing `humidity_offset_settings` and dehumidification setpoint
* **Breaking:** CLI restructured from a single command to subcommands.
  Existing read usage changes from `waterfurnace -u ...` to
  `waterfurnace read -u ...`. New write subcommands: `set-mode`,
  `set-cooling-temp`, `set-heating-temp`.

## [1.6.5] - 2026-04-15

* Add support for `activesettings`, and `activemode` (thanks @masterkoppa)

## [1.6.4] - 2026-03-16

* Allow the username to be an environment variable.
* Allow session reuse.

## [1.6.3] - 2026-03-16

* Update log formatting.

## [1.6.2] - 2026-03-11

* pypi build fixes

## [1.6.0] - 2026-03-11

* Add WFNoDataError error when energy data is not available (thanks @masterkoppa)
* Update GitHub Actions: checkout from v4 to v6, setup-python from v5 to v6, codecov-action from v4 to v5
* Add Python 3.14 to GitHub Actions test matrix
* Update black target versions to include Python 3.13 and 3.14

## [1.5.1] - 2026-01-31

* pypi build fixes

## [1.5.0] - 2026-01-31

* expose detailed location data for waterfurnace (thanks @masterkoppa)
* project main branch transition from `master` to `main`
* convert .rst to .md docs
* cleanup of obsolete files

## [1.4.0] - 2026-01-09

* Add get_energy_data, useful for homeassistant (thanks @masterkoppa)

## [1.3.1] - 2026-01-07

* Automate pypi build process

## [1.3.0] - 2026-01-07

* CLI enhanced to allow prompt for password (thanks @masterkoppa)
* Allow selecting device if multiple exist in your account (thanks @sam-kleiner)

## [1.2.0] - 2025-09-13

* Add SSL legacy compatibility to connect with modern SSL. Addresses
  `UNSAFE_LEGACY_RENEGOTIATION_DISABLED` error.
* Add LeavingWaterTemp and WaterFlowRate sensors (Series 7 WF)
* Added features to CLI (for details see --help)
  * Added debug flag
  * Added option sensor list specification
  * Added continous reporting
  * Added ability to specify furnace in a multi unit system

## [1.1.0] - 2019-01-07

* Fix retry logic

## [1.0.0] - 2018-12-05

* Detect unit automatically
* Add series 7 sensors

## [0.7.0] - 2018-07-13

* Add workaround timer to handle socket failures

## [0.6.0] - 2018-02-21

* Add timeout on socket

## [0.5.0] - 2018-02-16

* Update exception handling to be more Home Assistant friendly

## [0.4.0] - 2018-02-05

* More exceptions to distinguish errors we are expecting

## [0.3.0] - 2018-01-23

* Handle tid rollover

## [0.2.0] - 2018-01-19

* Library specific exceptions for login failures.

## [0.1.0] - 2018-01-17

* First release on PyPI.
