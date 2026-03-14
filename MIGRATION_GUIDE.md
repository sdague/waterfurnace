# Migration Guide: Modern Python Packaging

This guide explains the changes made to modernize the waterfurnace package and how to use the new setup.

## What Changed?

The project has been migrated from the legacy `setup.py` approach to modern `pyproject.toml` configuration, following [PEP 517](https://peps.python.org/pep-0517/) and [PEP 621](https://peps.python.org/pep-0621/) standards.

### Key Changes

1. **New `pyproject.toml`**: All package metadata and configuration now lives in a single file
2. **Updated dependencies**: Modernized dependency versions with security patches
3. **Improved CI/CD**: GitHub Actions now tests multiple Python versions (3.10-3.13)
4. **Better tooling configuration**: Black, pytest, and coverage settings in pyproject.toml

## For End Users

### Installation (No Changes Required)

Installation remains the same:

```bash
pip install waterfurnace
```

### Usage (No Changes Required)

The API and CLI remain unchanged. Your existing code will continue to work:

```python
from waterfurnace.waterfurnace import WaterFurnace

wf = WaterFurnace(user, password)
wf.login()
data = wf.read()
```

## For Developers

### Setting Up Development Environment

**Old way (still works):**
```bash
pip install -r requirements_dev.txt
python setup.py develop
```

**New way (recommended):**
```bash
# Install package in editable mode with all dev dependencies
pip install -e ".[dev]"
```

### Running Tests

**Old way:**
```bash
pytest
```

**New way (same, but with more options):**
```bash
# Run tests with coverage
pytest --cov=waterfurnace --cov-report=term-missing

# Or use tox for multiple Python versions
tox
```

### Code Formatting

**Old way:**
```bash
black waterfurnace tests
```

**New way (same):**
```bash
black waterfurnace tests

# Or check without modifying
tox -e lint
```

### Building the Package

**Old way:**
```bash
python setup.py sdist bdist_wheel
```

**New way:**
```bash
# Using modern build tool
python -m build

# Or use tox
tox -e build
```

### Version Bumping

**Old way:**
```bash
bumpversion patch  # or minor, major
```

**New way:**
```bash
bump-my-version bump patch  # or minor, major
```

## Configuration Files

### What's New

- **`pyproject.toml`**: Main configuration file (NEW)
  - Package metadata
  - Dependencies
  - Tool configurations (black, pytest, coverage)
  - Build system configuration

### What's Updated

- **`requirements_dev.txt`**: Updated with modern versions
- **`tox.ini`**: Simplified and modernized
- **`.github/workflows/python-app.yml`**: Tests multiple Python versions

### What's Deprecated (but still present)

- **`setup.py`**: Still present for backward compatibility, but pyproject.toml is now the source of truth
- **`setup.cfg`**: Minimal configuration, most moved to pyproject.toml

## Benefits of the New Setup

1. **Standards Compliant**: Follows modern Python packaging standards (PEP 517, 621)
2. **Single Source of Truth**: All configuration in one place (pyproject.toml)
3. **Better Tooling**: Modern tools like `build` instead of `setup.py`
4. **Improved CI/CD**: Tests run on Python 3.10-3.13
5. **Easier Development**: Simple `pip install -e ".[dev]"` for setup
6. **Better Dependency Management**: Clear separation of runtime vs dev dependencies

## Troubleshooting

### Issue: `pip install -e ".[dev]"` fails

**Solution**: Upgrade pip first:
```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

### Issue: tox fails with "isolated_build" error

**Solution**: Upgrade tox:
```bash
pip install --upgrade tox
```

### Issue: Build fails

**Solution**: Install build tool:
```bash
pip install build
python -m build
```

## Optional: Removing Legacy Files

Once you're comfortable with the new setup, you can optionally remove:

- `setup.py` (keep for now for backward compatibility)
- `setup.cfg` (keep minimal version)
- Old backup files (`*.txt~`, `*~`)

**Note**: Don't remove these files yet if you need to support older pip versions (<21.3).

## Questions?

If you encounter issues with the new packaging setup, please:

1. Check this migration guide
2. Review the [pyproject.toml](pyproject.toml) file
3. Open an issue on GitHub with details about your environment

## Timeline

- **v1.5.1**: Migration to modern packaging (current)
- **v1.6.0**: May remove setup.py if no issues reported
- **v2.0.0**: Full modernization with type hints and async support (planned)