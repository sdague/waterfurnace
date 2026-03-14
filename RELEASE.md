# Release Process

This project uses a simplified release process with a single source of truth for versioning.

## Version Management

**Single Source of Truth:** All version information is stored in [`pyproject.toml`](pyproject.toml) only.

- The package version is defined in `pyproject.toml` under `[project]` → `version`
- [`waterfurnace/__init__.py`](waterfurnace/__init__.py) automatically reads the version from the installed package metadata
- No other files need manual version updates

## How to Release

### 1. Run the Release Command

```bash
make release
```

This command will:
1. Clean build artifacts
2. Run all tests via `tox` (Python 3.10, 3.11, 3.12, 3.14)
3. Build distribution packages
4. Prompt you for the new version number
5. Update `pyproject.toml` with the new version
6. Commit the version change
7. Create a git tag (e.g., `v1.6.3`)

### 2. Push to GitHub

```bash
git push && git push --tags
```

### 3. Automatic Publishing

Once the tag is pushed, GitHub Actions automatically:
1. Builds the package
2. Publishes to TestPyPI (for verification)
3. Publishes to PyPI (production)
4. Creates a GitHub Release

## Manual Steps (if needed)

### Update Version Only

Edit the version in `pyproject.toml`:

```toml
[project]
version = "1.6.3"
```

### Build Package Locally

```bash
make dist
```

This creates distribution files in the `dist/` directory.

### Run Tests

```bash
make test
```

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (1.x.x): Incompatible API changes
- **MINOR** version (x.1.x): New functionality, backwards compatible
- **PATCH** version (x.x.1): Bug fixes, backwards compatible

## GitHub Actions Workflow

The release workflow (`.github/workflows/pypi-upload.yml`) is triggered by pushing tags matching `v*.*.*` pattern:

```bash
git tag v1.6.3
git push --tags
```

The workflow:
1. Builds the package
2. Publishes to TestPyPI
3. Publishes to PyPI (after TestPyPI succeeds)
4. Creates a GitHub Release (after PyPI succeeds)

## Troubleshooting

### Tests Fail During Release

The release process will abort if tests fail. Fix the issues and try again:

```bash
make test  # Run tests to identify issues
# Fix issues
make release  # Try release again
```

### Need to Update Changelog

Update [`CHANGELOG.md`](CHANGELOG.md) before running `make release`:

```bash
# Edit CHANGELOG.md
git add CHANGELOG.md
git commit -m "Update changelog for v1.6.3"
make release
```

### Version Already Exists

If you need to re-release the same version:

```bash
# Delete the local tag
git tag -d v1.6.3

# Delete the remote tag (if pushed)
git push origin :refs/tags/v1.6.3

# Create new tag
make release