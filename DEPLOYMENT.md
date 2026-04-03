# Deployment Guide

This document explains how the project is automatically deployed to PyPI.

## Automatic Deployment Setup

### 1. Create PyPI API Token

1. Go to [PyPI.org](https://pypi.org/)
2. Sign in to your account
3. Go to Account Settings → API Tokens
4. Create a new token with **Entire account** scope
5. Copy the token (you'll only see it once)

### 2. Add Secret to GitHub

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `PYPI_API_TOKEN`
5. Value: Paste the PyPI API token
6. Save

### 3. Configure Branch Protection (Optional but Recommended)

To prevent accidental releases:

1. Go to Settings → Branches
2. Add rule for `main` branch
3. Enable:
   - "Require pull request reviews before merging"
   - "Require status checks to pass before merging"
   - "Require branches to be up to date before merging"

## Release Process

### Manual Release

1. Update version in `pyproject.toml`:
   ```toml
   version = "0.2.0"  # Update this
   ```

2. Commit and push:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.2.0"
   git push
   ```

3. Create a GitHub Release:
   - Go to Releases → Draft a new release
   - Tag version: `v0.2.0` (must start with 'v')
   - Title: `Release v0.2.0`
   - Description: List of changes
   - Publish release

4. The CI/CD pipeline will automatically:
   - Run tests on all Python versions
   - Build the distribution
   - Publish to PyPI

### CI/CD Workflows

**tests.yml**: Runs on every push and PR
- Tests on Python 3.8, 3.9, 3.10, 3.11, 3.12
- Tests on Ubuntu, Windows, macOS
- Linting with flake8
- Coverage reporting

**lint.yml**: Checks code style
- Black formatting
- isort import sorting
- flake8 linting

**publish.yml**: Runs only on release creation
- Builds distribution
- Checks with twine
- Publishes to PyPI

## Installing Development Version

To install the latest development version:

```bash
pip install git+https://github.com/cumic06/unity-cli.git@main
```

## Troubleshooting

### PyPI token not working
- Make sure the token is correctly added to GitHub Secrets
- Check that you copied the entire token (including `pypi-` prefix)

### Build fails
- Check the Actions tab in GitHub for detailed error messages
- Ensure `pyproject.toml` is valid

### Release tag naming
- Must follow format `v*.*.*` (e.g., `v0.1.0`, `v1.0.0`)
- Otherwise the publish workflow won't trigger

## Manual PyPI Upload (if needed)

```bash
pip install build twine

# Build distribution
python -m build

# Upload to PyPI (requires credentials)
twine upload dist/*
```

## Version Numbering

This project uses Semantic Versioning (MAJOR.MINOR.PATCH):
- MAJOR: Breaking changes
- MINOR: New features
- PATCH: Bug fixes

Example versions:
- `0.1.0` - Initial alpha release
- `0.2.0` - Added new features
- `0.2.1` - Bug fix
- `1.0.0` - First stable release
