# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fabric DataOps Agent — a Python tool for automating Power BI and Microsoft Fabric REST API operations (metadata scanning, activity events, workspace management, gateway/datasource operations).

## Commands

### Setup & Dependencies

```bash
# Install dependencies (uses uv)
uv sync

# Run the Flask app
uv run python main.py
```

### Running Scripts

```bash
# Standalone scripts are run directly
uv run python get_activity_events.py
uv run python get_metadata_scan_results.py
uv run python get_dataset_datasources.py
```

### Tests

No formal test suite. Test files are standalone scripts:
```bash
uv run python test_fabric_lib.py        # Tests Fabric API client (requires browser auth)
uv run python test_python_version.py    # Verifies Python executable
```

## Architecture

### Authentication

All API calls require a Bearer token from `services/aadservice.py`:
- `AadService.get_access_token()` — supports both `ServicePrincipal` (CLIENT_SECRET) and `MasterUser` (username/password) modes
- Auth mode is set in `config.py` via `AUTHENTICATION_MODE`

### Configuration

`config.py` → `BaseConfig` class reads `TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET` from `.env`. Config is stored as a singleton via `app.py`:
```python
App.setup(BaseConfig)  # sets App.config, used by all services
```

### Service Pattern

Every service in `services/powerbi/` follows the same structure:
```python
class GetXxxService:
    def get_xxx(self, access_token):
        headers = {"Authorization": "Bearer " + access_token, ...}
        return requests.get(f"{app.config.POWER_BI_API_URL}v1.0/myorg/...", headers=headers)
```

Services return raw `requests.Response` objects. Callers handle `.json()` parsing and file I/O.

### Standalone Scripts vs Flask App

- **Standalone scripts** (root level, e.g. `get_activity_events.py`) — used for bulk data extraction; write results as JSON to `data/` subdirectories
- **Flask app** (`main.py` → `app.py`) — web interface at `http://localhost:5000`; currently minimal

### Data Storage

Scripts save API responses as JSON files under `data/`:
- `data/activity_events/json/{YYYY-MM-DD}/`
- `data/workspaces/modified/`
- `data/metadata_scanning/`
- etc.

The `data/` and `logs/` directories are gitignored.

### Encryption (models/ + helper/)

Credential updates to gateways require RSA-OAEP encryption via `helper/asymmetric1024keyencryptionhelper.py` or `asymmetrichigherkeyencryptionhelper.py`. The gateway's public key (fetched from API) is used to encrypt credentials before publishing.

## Environment Variables

Required in `.env`:
```
TENANT_ID=<Azure AD tenant ID>
CLIENT_ID=<App registration client ID>
CLIENT_SECRET=<App registration client secret>
```

## Key APIs Used

- Power BI REST API: `https://api.powerbi.com/v1.0/myorg/`
- Fabric API (via `microsoft-fabric-api` SDK): workspace/item management
- AAD token scope: `https://analysis.windows.net/powerbi/api/.default`