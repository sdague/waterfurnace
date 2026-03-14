# WaterFurnace Library - Robustness Improvement Plan

## Executive Summary

This document provides a comprehensive analysis of the waterfurnace Python library and recommendations for improving its robustness, maintainability, and production-readiness.

## Current State Assessment

The library provides a Python interface for WaterFurnace and GeoStar geothermal systems via websocket. It's functional but has several areas that could be enhanced for production robustness.

**Strengths:**
- Clean separation of concerns (CLI, core library, tests)
- Support for multiple vendors (WaterFurnace, GeoStar)
- Energy data API integration
- Retry logic for connection failures
- Active maintenance with recent Python version support

**Areas for Improvement:**
- Error handling and resilience
- Type safety and validation
- Testing coverage
- Documentation
- Security practices
- Modern Python packaging
- API design consistency

---

## Priority 1: Critical Issues (Security & Correctness)

### 1.1 Security Vulnerabilities

**Issue:** Password exposed in `__repr__` method
- **Location:** `waterfurnace/waterfurnace.py:138-139`
- **Risk:** Passwords logged in debug output, stack traces, or monitoring systems
- **Fix:** Remove password from string representation
```python
def __repr__(self):
    return f"<Symphony user={self.user}>"
```

**Issue:** No SSL certificate verification configuration
- **Location:** `waterfurnace/waterfurnace.py:186-188`
- **Risk:** Man-in-the-middle attacks
- **Fix:** Make SSL verification configurable but default to secure

### 1.2 Critical Bugs

**Issue:** CLI calls undefined methods
- **Location:** `waterfurnace/cli.py:141-142`
- **Problem:** Calls `wf.get_location()` and `wf.get_devices()` which don't exist
- **Fix:** Use correct API: `wf.locations[location]` and `wf.devices`

**Issue:** Mutable default argument
- **Location:** `waterfurnace/waterfurnace.py:458`
- **Problem:** `def __init__(self, data={})` creates shared mutable default
- **Fix:** Use `data=None` and initialize inside method

---

## Priority 2: Robustness & Reliability

### 2.1 Error Handling

**Current Issues:**
- Generic `except Exception` catches in multiple places
- Websocket errors not properly categorized
- No distinction between retryable and non-retryable errors

**Recommendations:**

1. **Create exception hierarchy:**
```python
class WFException(Exception):
    """Base exception for all WaterFurnace errors"""
    pass

class WFCredentialError(WFException):
    """Authentication/credential errors - not retryable"""
    pass

class WFConnectionError(WFException):
    """Network/connection errors - retryable"""
    pass

class WFTimeoutError(WFConnectionError):
    """Timeout errors - retryable"""
    pass

class WFWebsocketClosedError(WFConnectionError):
    """Websocket closed - retryable"""
    pass

class WFValidationError(WFException):
    """Input validation errors - not retryable"""
    pass
```

2. **Replace generic exception handling:**
   - In `waterfurnace.py:339-341`: Catch specific websocket exceptions
   - In `waterfurnace.py:213`: Catch specific exceptions for device/location lookup

3. **Add proper timeout handling:**
   - Replace threading.Timer with proper async/await or timeout context managers
   - Add configurable timeout values
   - Ensure timer cleanup in all code paths

### 2.2 Connection Management

**Issues:**
- No connection pooling
- Websocket not properly closed on errors
- No health check mechanism

**Recommendations:**

1. **Add context manager support:**
```python
class SymphonyGeothermal:
    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def close(self):
        """Properly close websocket connection"""
        if hasattr(self, 'ws') and self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
```

2. **Add connection health checks:**
```python
def is_connected(self):
    """Check if websocket is still connected"""
    return hasattr(self, 'ws') and self.ws and self.ws.connected
```

3. **Implement automatic reconnection:**
   - Add configurable reconnection strategy
   - Exponential backoff with jitter
   - Maximum retry limits

### 2.3 Input Validation

**Issues:**
- No validation of user inputs
- No validation of API responses
- Type coercion happens silently

**Recommendations:**

1. **Add input validation:**
```python
def __init__(self, user, passwd, max_fails=5, device=0, location=0):
    if not user or not isinstance(user, str):
        raise WFValidationError("User must be a non-empty string")
    if not passwd or not isinstance(passwd, str):
        raise WFValidationError("Password must be a non-empty string")
    if not isinstance(max_fails, int) or max_fails < 1:
        raise WFValidationError("max_fails must be a positive integer")
    # ... rest of initialization
```

2. **Validate API responses:**
   - Check for required fields in JSON responses
   - Validate data types match expectations
   - Handle missing or null values gracefully

---

## Priority 3: Code Quality & Maintainability

### 3.1 Type Hints

**Issue:** No type hints throughout the codebase

**Recommendations:**

1. **Add type hints to all functions and methods:**
```python
from typing import Optional, Dict, List, Any, Union

class SymphonyGeothermal:
    def __init__(
        self,
        base_url: str,
        login_url: str,
        ws_url: str,
        user: str,
        passwd: str,
        max_fails: int = 5,
        device: Union[int, str] = 0,
        location: Union[int, str] = 0,
    ) -> None:
        # ...

    def read(self) -> WFReading:
        # ...

    def get_energy_data(
        self,
        start_date: str,
        end_date: str,
        frequency: str = "1H",
        timezone_str: str = "America/New_York"
    ) -> WFEnergyData:
        # ...
```

2. **Add mypy to development dependencies and CI:**
```ini
# tox.ini
[testenv:typecheck]
basepython=python
deps=mypy
commands=mypy waterfurnace --strict
```

### 3.2 Documentation

**Issues:**
- Minimal docstrings
- No API documentation
- README lacks detailed usage examples

**Recommendations:**

1. **Add comprehensive docstrings:**
```python
def read(self) -> WFReading:
    """Read current sensor data from the geothermal system.

    Sends a data request via websocket and returns parsed sensor readings.
    The websocket must be connected (via login()) before calling this method.

    Returns:
        WFReading: Object containing all sensor readings including power,
                   temperatures, humidity, and operational mode.

    Raises:
        WFWebsocketClosedError: If websocket connection is closed or times out.
        WFError: If the API returns an error response.

    Example:
        >>> wf = WaterFurnace(user, password)
        >>> wf.login()
        >>> data = wf.read()
        >>> print(f"Power: {data.totalunitpower}W, Mode: {data.mode}")
    """
```

2. **Create comprehensive documentation:**
   - API reference documentation
   - Usage examples for common scenarios
   - Troubleshooting guide
   - Architecture overview

3. **Improve README:**
   - Add installation instructions
   - Add complete usage examples
   - Document all CLI options
   - Add FAQ section

### 3.3 Code Organization

**Issues:**
- Single large file (678 lines)
- Mixed concerns (websocket, HTTP, data models)
- Constants scattered throughout

**Recommendations:**

1. **Split into modules:**
```
waterfurnace/
├── __init__.py
├── client.py          # Main client classes
├── models.py          # Data models (WFReading, WFEnergyData, etc.)
├── exceptions.py      # Exception hierarchy
├── constants.py       # All constants
├── websocket.py       # Websocket handling
├── api.py            # HTTP API calls
└── cli.py            # CLI (existing)
```

2. **Extract constants:**
```python
# constants.py
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0"

class WaterFurnaceEndpoints:
    BASE_URL = "https://symphony.mywaterfurnace.com"
    LOGIN_URL = f"{BASE_URL}/account/login"
    WS_URL = "wss://awlclientproxy.mywaterfurnace.com/"

class GeoStarEndpoints:
    BASE_URL = "https://symphony.mygeostar.com"
    LOGIN_URL = f"{BASE_URL}/account/login"
    WS_URL = "wss://awlclientproxy.mygeostar.com/"

FURNACE_MODE = (
    "Standby", "Fan Only", "Cooling 1", "Cooling 2",
    "Reheat", "Heating 1", "Heating 2", "E-Heat",
    "Aux Heat", "Lockout",
)

DEFAULT_TIMEOUT = 30
ERROR_INTERVAL = 300
```

---

## Priority 4: Testing

### 4.1 Test Coverage

**Issues:**
- Minimal test coverage
- No unit tests for core functionality
- No integration tests
- No mocking of external services

**Recommendations:**

1. **Add comprehensive unit tests:**
```python
# tests/test_models.py
def test_wfreading_initialization():
    data = {
        "totalunitpower": 1500,
        "modeofoperation": 5,
        "tstatroomtemp": 72.5,
    }
    reading = WFReading(data)
    assert reading.totalunitpower == 1500
    assert reading.mode == "Heating 1"
    assert reading.tstatroomtemp == 72.5

def test_wfreading_with_missing_data():
    reading = WFReading({})
    assert reading.totalunitpower is None
    assert reading.tstatroomtemp is None
```

2. **Add integration tests with mocking:**
```python
# tests/test_client.py
import pytest
from unittest.mock import Mock, patch

@patch('waterfurnace.client.requests.post')
@patch('waterfurnace.client.websocket.create_connection')
def test_login_success(mock_ws, mock_post):
    mock_post.return_value.cookies = {'sessionid': 'test123'}
    mock_ws.return_value.recv.return_value = json.dumps({
        'locations': [{'gateways': [{'gwid': 'test'}]}]
    })

    wf = WaterFurnace('user', 'pass')
    wf.login()

    assert wf.sessionid == 'test123'
    assert wf.gwid == 'test'
```

3. **Add test fixtures:**
```python
# tests/conftest.py
@pytest.fixture
def sample_reading_data():
    return {
        "totalunitpower": 1500,
        "modeofoperation": 5,
        "tstatroomtemp": 72.5,
        "tstatactivesetpoint": 70,
        "enteringwatertemp": 45.0,
        "leavingairtemp": 95.0,
    }

@pytest.fixture
def mock_waterfurnace_client():
    with patch('waterfurnace.client.requests.post'), \
         patch('waterfurnace.client.websocket.create_connection'):
        yield WaterFurnace('test', 'test')
```

4. **Add coverage requirements:**
```ini
# tox.ini
[testenv]
commands =
    pytest --cov=waterfurnace --cov-report=html --cov-report=term-missing --cov-fail-under=80
```

### 4.2 Test Organization

**Recommendations:**

1. **Organize tests by module:**
```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── test_client.py        # Client tests
├── test_models.py        # Model tests
├── test_exceptions.py    # Exception tests
├── test_cli.py          # CLI tests
└── integration/
    └── test_integration.py
```

---

## Priority 5: Modern Python Practices

### 5.1 Packaging

**Issues:**
- Using deprecated `setup.py` approach
- No `pyproject.toml`
- Outdated dependency specifications

**Recommendations:**

1. **Migrate to `pyproject.toml`:**
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "waterfurnace"
version = "1.5.1"
description = "Python interface for waterfurnace geothermal systems"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "Apache Software License 2.0"}
authors = [
    {name = "Sean Dague", email = "sean@dague.net"}
]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
]
dependencies = [
    "Click>=8.0",
    "requests>=2.28",
    "websocket-client>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "mypy>=1.0",
    "tox>=4.0",
]

[project.scripts]
waterfurnace = "waterfurnace.cli:main"

[tool.black]
line-length = 88
target-version = ['py310']

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

2. **Update dependency versions:**
   - Use modern versions with security patches
   - Specify minimum versions with `>=`
   - Consider using `poetry` or `pip-tools` for lock files

### 5.2 Async Support

**Issue:** Synchronous blocking calls limit scalability

**Recommendations:**

1. **Add async variant:**
```python
# waterfurnace/async_client.py
import asyncio
import aiohttp
import websockets

class AsyncWaterFurnace:
    async def login(self) -> None:
        """Async login implementation"""
        async with aiohttp.ClientSession() as session:
            async with session.post(self.login_url, data=data) as resp:
                self.sessionid = resp.cookies['sessionid'].value

        async with websockets.connect(self.ws_url) as ws:
            await ws.send(json.dumps(login))
            response = await ws.recv()
            # ... process response

    async def read(self) -> WFReading:
        """Async read implementation"""
        # ... async websocket read
```

2. **Maintain backward compatibility:**
   - Keep synchronous API as default
   - Provide async as optional import
   - Document both APIs clearly

### 5.3 Configuration Management

**Issue:** Hardcoded configuration values

**Recommendations:**

1. **Add configuration class:**
```python
from dataclasses import dataclass

@dataclass
class WaterFurnaceConfig:
    timeout: int = 30
    max_retries: int = 5
    retry_interval: int = 300
    verify_ssl: bool = True
    user_agent: str = "Mozilla/5.0 ..."

    @classmethod
    def from_env(cls) -> 'WaterFurnaceConfig':
        """Load configuration from environment variables"""
        return cls(
            timeout=int(os.getenv('WF_TIMEOUT', 30)),
            max_retries=int(os.getenv('WF_MAX_RETRIES', 5)),
            # ...
        )
```

2. **Support configuration files:**
```python
def load_config(path: Optional[str] = None) -> WaterFurnaceConfig:
    """Load configuration from YAML/JSON file"""
    if path and os.path.exists(path):
        with open(path) as f:
            data = yaml.safe_load(f)
            return WaterFurnaceConfig(**data)
    return WaterFurnaceConfig()
```

---

## Priority 6: Developer Experience

### 6.1 Logging

**Issues:**
- Inconsistent logging levels
- Debug information mixed with errors
- No structured logging

**Recommendations:**

1. **Improve logging structure:**
```python
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def log_api_call(method: str, url: str, **kwargs: Any) -> None:
    """Log API calls with structured data"""
    logger.debug(
        "API call",
        extra={
            "method": method,
            "url": url,
            "params": kwargs,
        }
    )

def log_error(error: Exception, context: Dict[str, Any]) -> None:
    """Log errors with context"""
    logger.error(
        f"Error: {error}",
        extra={"error_type": type(error).__name__, **context},
        exc_info=True
    )
```

2. **Add log levels appropriately:**
   - DEBUG: Detailed diagnostic information
   - INFO: General informational messages
   - WARNING: Warning messages for recoverable issues
   - ERROR: Error messages for failures

### 6.2 CLI Improvements

**Issues:**
- Limited output formats
- No progress indicators
- Poor error messages

**Recommendations:**

1. **Add output format options:**
```python
@click.option(
    '--format',
    type=click.Choice(['text', 'json', 'csv']),
    default='text',
    help='Output format'
)
def main(..., format):
    if format == 'json':
        click.echo(json.dumps(data.to_dict()))
    elif format == 'csv':
        # CSV output
    else:
        # Human-readable text
```

2. **Add progress indicators:**
```python
with click.progressbar(length=100, label='Connecting') as bar:
    wf.login()
    bar.update(50)
    data = wf.read()
    bar.update(50)
```

3. **Improve error messages:**
```python
try:
    wf.login()
except WFCredentialError:
    click.echo("❌ Login failed: Invalid username or password", err=True)
    click.echo("Please check your credentials and try again.", err=True)
    sys.exit(1)
except WFConnectionError as e:
    click.echo(f"❌ Connection failed: {e}", err=True)
    click.echo("Please check your internet connection.", err=True)
    sys.exit(1)
```

### 6.3 Examples and Recipes

**Recommendations:**

1. **Create examples directory:**
```
examples/
├── basic_usage.py
├── continuous_monitoring.py
├── energy_analysis.py
├── multi_device.py
└── async_usage.py
```

2. **Add common use cases:**
```python
# examples/continuous_monitoring.py
"""
Example: Continuous monitoring with automatic reconnection
"""
from waterfurnace import WaterFurnace
import time

def monitor_system(user, password, interval=15):
    with WaterFurnace(user, password) as wf:
        while True:
            try:
                data = wf.read()
                print(f"Power: {data.totalunitpower}W, Mode: {data.mode}")
                time.sleep(interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}, retrying...")
                time.sleep(5)

if __name__ == "__main__":
    monitor_system("user@example.com", "password")
```

---

## Implementation Roadmap

### Phase 1: Critical Fixes (Week 1-2)
- [ ] Fix security issues (password in repr, SSL verification)
- [ ] Fix CLI bugs (undefined methods)
- [ ] Fix mutable default arguments
- [ ] Add basic input validation

### Phase 2: Error Handling (Week 3-4)
- [ ] Implement exception hierarchy
- [ ] Replace generic exception handling
- [ ] Add connection management (context managers)
- [ ] Improve retry logic

### Phase 3: Code Quality (Week 5-6)
- [ ] Add type hints throughout
- [ ] Add comprehensive docstrings
- [ ] Reorganize code into modules
- [ ] Set up mypy in CI

### Phase 4: Testing (Week 7-8)
- [ ] Write unit tests for all modules
- [ ] Add integration tests with mocking
- [ ] Set up coverage requirements
- [ ] Add test fixtures

### Phase 5: Modernization (Week 9-10)
- [ ] Migrate to pyproject.toml
- [ ] Update dependencies
- [ ] Add configuration management
- [ ] Improve logging

### Phase 6: Documentation & Polish (Week 11-12)
- [ ] Write comprehensive documentation
- [ ] Create examples
- [ ] Improve CLI UX
- [ ] Add async support (optional)

---

## Metrics for Success

1. **Code Quality:**
   - Type coverage: >90%
   - Test coverage: >80%
   - No critical security issues
   - Passes all linters (black, mypy, pylint)

2. **Reliability:**
   - Proper error handling for all failure modes
   - Automatic reconnection works reliably
   - No resource leaks (websockets, threads)

3. **Usability:**
   - Clear error messages
   - Comprehensive documentation
   - Working examples for common use cases
   - Intuitive API design

4. **Maintainability:**
   - Modular code structure
   - Clear separation of concerns
   - Well-documented code
   - Easy to extend

---

## Conclusion

The waterfurnace library is functional but needs significant improvements to be production-ready. The recommendations above prioritize security and correctness first, followed by robustness, code quality, and modern Python practices.

The most critical issues to address immediately are:
1. Password exposure in logging
2. CLI bugs with undefined methods
3. Mutable default arguments
4. Generic exception handling

Following this plan will result in a more robust, maintainable, and production-ready library that follows modern Python best practices.