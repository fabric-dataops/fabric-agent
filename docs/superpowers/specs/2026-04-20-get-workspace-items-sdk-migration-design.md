# Design: Migrate get_workspace_items to microsoft-fabric-api SDK

**Date:** 2026-04-20
**Branch:** reengineer-get-workspace-items

## Overview

Replace direct HTTP calls in `get_workspace_items.py`, `ListWorkspacesService`, and `ListItemsService` with the `microsoft-fabric-api` Python SDK (`FabricClient`). The SDK handles authentication, pagination, and response parsing — eliminating manual Bearer token headers, `continuationUri` loops, and `requests.Response` parsing.

`AadService` and all other service classes are untouched.

## Files Changed

| File | Change |
|------|--------|
| `services/fabriccredential.py` | **New** — credential factory |
| `services/listworkspaces.py` | **Updated** — SDK internals, new interface |
| `services/listitems.py` | **Updated** — SDK internals, new interface |
| `get_workspace_items.py` | **Updated** — uses credential factory + new service interfaces |

## Component Details

### `services/fabriccredential.py` (new)

Single public function:

```python
def build_credential() -> TokenCredential
```

- Reads `App.config.AUTHENTICATION_MODE`
- `ServicePrincipal` → returns `ClientSecretCredential(tenant_id, client_id, client_secret)`
- `MasterUser` → returns `UsernamePasswordCredential(client_id, username, password, authority=...)`
- Unknown mode → raises `ValueError`

This is the only auth bridge between the existing config system and the SDK. `AadService` is not touched.

### `services/listworkspaces.py` (updated)

**Before:** stateless class, methods accept `access_token`, return `requests.Response`, caller paginates via `list_workspaces_cont()`.

**After:**

```python
class ListWorkspacesService:
    def __init__(self, client: FabricClient)
    def list_workspaces(self, type="Workspace", state="Active") -> Iterable[Workspace]
```

- Constructor stores `FabricClient` instance
- `list_workspaces()` delegates to `client.admin.workspaces.list_workspaces(type=type, state=state)`
- Returns a lazy `Iterable[Workspace]` — SDK handles all pagination internally
- `list_workspaces_cont()` removed — no longer needed

### `services/listitems.py` (updated)

**Before:** stateless class, methods accept `access_token` + `workspace_id`, return `requests.Response`, caller paginates via `list_items_cont()`.

**After:**

```python
class ListItemsService:
    def __init__(self, client: FabricClient)
    def list_items(self, workspace_id: str, item_type: str | None = None) -> Iterable[Item]
```

- Constructor stores `FabricClient` instance
- `list_items()` delegates to `client.core.items.list_items(workspace_id, type=item_type)`
- Returns a lazy `Iterable[Item]` — SDK handles all pagination internally
- `list_items_cont()` removed — no longer needed

### `get_workspace_items.py` (updated)

**`main()` changes:**

1. Replace `AadService.get_access_token()` call with `build_credential()` from `fabriccredential`
2. Construct a single `FabricClient(credential)` instance
3. Pass `client` into `ListWorkspacesService(client)` and `ListItemsService(client)` constructors
4. Replace manual pagination loops with direct `for item in service.list_workspaces()` iteration
5. Materialise workspace list with `list()` once before saving `workspaces.json`
6. Serialize SDK model objects with `.as_dict()` before passing to `save_output()`

`save_output()` is unchanged — still receives a list of dicts.

## Data Flow

```
build_credential()
    → FabricClient(credential)
        → ListWorkspacesService(client).list_workspaces()    # Iterable[Workspace]
            → list(workspaces) → save workspaces.json
            → for workspace in workspaces:
                workspace_id = workspace.id
                ListItemsService(client).list_items(ws_id)   # Iterable[Item]
                    → items = [item.as_dict() for item in iterable]
                    → inject workspaceId into each dict
                    → save_output(output_path, items, ws_id, filename)
```

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Unknown auth mode | `ValueError` raised immediately in `build_credential()` |
| API error (workspace list) | `HttpResponseError` caught in `main()`, print and return |
| API error (items for a workspace) | `HttpResponseError` caught per-workspace, print and continue |

SDK raises `azure.core.exceptions.HttpResponseError` on non-2xx responses. Error handling in `get_workspace_items.py` is updated to catch this instead of checking `.ok` on a `Response` object.

## What Does NOT Change

- `save_output()` function — identical
- `AadService` — untouched
- All other service classes in `services/powerbi/` — untouched
- All other standalone scripts — untouched
- Output file format and directory structure — identical
- `main()` signature: `main(workspace_id=None, item_type=None)` — unchanged
