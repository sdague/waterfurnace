# Release Process

This project uses a simplified, automated release process with a single source of truth for versioning.

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

This interactive command will:
1. Show the current version
2. Prompt you for the new version number (must be in X.Y.Z format)
3. Update `pyproject.toml` with the new version
4. Prompt you to update [`CHANGELOG.md`](CHANGELOG.md)
5. Commit both files
6. Push to the main branch

### 2. Automatic Publishing

Once pushed to main, GitHub Actions automatically:
1. Validates the version format
2. Checks that the version tag doesn't already exist
3. Runs tests on Python 3.10, 3.11, 3.12, and 3.14
4. Builds the package
5. Publishes to PyPI
6. Creates a git tag (e.g., `v1.6.3`)
7. Creates a GitHub Release with changelog notes

**That's it!** The entire process is automated after you push to main.

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (1.x.x): Incompatible API changes
- **MINOR** version (x.1.x): New functionality, backwards compatible
- **PATCH** version (x.x.1): Bug fixes, backwards compatible

## Changelog Format

For the GitHub Release to include proper release notes, format your [`CHANGELOG.md`](CHANGELOG.md) like this:

```markdown
## 1.6.3 (2024-03-14)

* New feature description
* Bug fix description
```

The release workflow will automatically extract the section for your version.

## Manual Steps (if needed)

### Update Version Only

Edit the version in `pyproject.toml`:

```toml
[project]
version = "1.6.3"
```

Then commit and push to main:

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Release version 1.6.3"
git push origin main
```

### Build Package Locally

```bash
make dist
```

This creates distribution files in the `dist/` directory.

### Run Tests Locally

```bash
make test
```

This runs the full test suite via `tox` on all supported Python versions.

## GitHub Actions Workflow

The release workflow ([`.github/workflows/release.yml`](.github/workflows/release.yml)) is triggered by:
- Push to `main` branch
- Changes to `pyproject.toml` file

The workflow includes these jobs:
1. **validate** - Extracts and validates version, checks for existing tags
2. **test** - Runs tests on all Python versions (3.10, 3.11, 3.12, 3.14)
3. **build** - Builds distribution packages
4. **publish-to-pypi** - Publishes to PyPI using trusted publishing
5. **create-release** - Creates git tag and GitHub Release with changelog

## Monitoring Releases

Monitor the release progress at:
https://github.com/sdague/waterfurnace/actions

## Troubleshooting

### Tests Fail During Release

If tests fail in the GitHub Actions workflow:
1. Check the workflow logs to identify the issue
2. Fix the issue locally
3. Run `make test` to verify the fix
4. Commit and push the fix
5. The workflow will run again automatically

### Version Already Exists

If you accidentally try to release a version that already exists:
1. The workflow will fail at the validation step
2. Increment the version number
3. Update `pyproject.toml` with the new version
4. Commit and push again

### Need to Update Changelog After Push

If you forgot to update the changelog:
1. Update [`CHANGELOG.md`](CHANGELOG.md)
2. Commit with message: `Update changelog for v1.6.3`
3. Push to main
4. The release will use the updated changelog

### Manual Tag Creation (Emergency Only)

If you need to create a release manually:

```bash
# Update version in pyproject.toml
# Update CHANGELOG.md
git add pyproject.toml CHANGELOG.md
git commit -m "Release version 1.6.3"
git push origin main

# Wait for workflow to complete, or create tag manually:
git tag -a v1.6.3 -m "Release version 1.6.3"
git push origin v1.6.3
```

## PyPI Publishing

The workflow uses [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) to securely publish to PyPI without API tokens. This is configured in the PyPI project settings and requires:
- GitHub Actions workflow with `id-token: write` permission
- PyPI project configured with GitHub as a trusted publisher