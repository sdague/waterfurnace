# Changelog

## [Unreleased]

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
