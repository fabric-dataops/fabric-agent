# get_workspace_items SDK Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace direct HTTP calls in `get_workspace_items.py`, `ListWorkspacesService`, and `ListItemsService` with the `microsoft-fabric-api` Python SDK (`FabricClient`), eliminating manual token handling and pagination loops.

**Architecture:** A new credential factory (`services/fabriccredential.py`) bridges the existing `App.config` auth config to an Azure `TokenCredential` object. Both service classes are refactored in-place to accept a `FabricClient` at construction and delegate to the SDK — returning lazy `Iterable` objects instead of `requests.Response`. `get_workspace_items.py` is updated to wire these together and serialize SDK model objects with `.as_dict()`.

**Tech Stack:** `microsoft-fabric-api` (`FabricClient`), `azure-identity` (`ClientSecretCredential`, `UsernamePasswordCredential`), `azure-core` (`HttpResponseError`), `pytest`, `unittest.mock`

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `services/fabriccredential.py` | Build Azure `TokenCredential` from `App.config` |
| Create | `tests/test_fabriccredential.py` | Unit tests for credential factory |
| Modify | `services/listworkspaces.py` | SDK-backed workspace listing |
| Create | `tests/test_listworkspaces.py` | Unit tests for `ListWorkspacesService` |
| Modify | `services/listitems.py` | SDK-backed item listing |
| Create | `tests/test_listitems.py` | Unit tests for `ListItemsService` |
| Modify | `get_workspace_items.py` | Wire credential factory + services, serialize SDK models |
| Create | `tests/test_get_workspace_items.py` | Unit tests for `main()` |

---

## Task 1: Credential Factory

**Files:**
- Create: `services/fabriccredential.py`
- Create: `tests/test_fabriccredential.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_fabriccredential.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from azure.identity import ClientSecretCredential, UsernamePasswordCredential


def _make_config(mode, tenant="t1", client_id="c1", secret="s1", user="u1", pw="p1"):
    cfg = MagicMock()
    cfg.AUTHENTICATION_MODE = mode
    cfg.TENANT_ID = tenant
    cfg.CLIENT_ID = client_id
    cfg.CLIENT_SECRET = secret
    cfg.POWER_BI_USER = user
    cfg.POWER_BI_PASS = pw
    return cfg


def test_service_principal_returns_client_secret_credential():
    cfg = _make_config("ServicePrincipal")
    with patch("services.fabriccredential.App") as mock_app:
        mock_app.config = cfg
        from services.fabriccredential import build_credential
        cred = build_credential()
    assert isinstance(cred, ClientSecretCredential)


def test_master_user_returns_username_password_credential():
    cfg = _make_config("MasterUser")
    with patch("services.fabriccredential.App") as mock_app:
        mock_app.config = cfg
        from services.fabriccredential import build_credential
        cred = build_credential()
    assert isinstance(cred, UsernamePasswordCredential)


def test_unknown_mode_raises_value_error():
    cfg = _make_config("Unknown")
    with patch("services.fabriccredential.App") as mock_app:
        mock_app.config = cfg
        from services.fabriccredential import build_credential
        with pytest.raises(ValueError, match="Unsupported AUTHENTICATION_MODE"):
            build_credential()


def test_service_principal_case_insensitive():
    cfg = _make_config("serviceprincipal")
    with patch("services.fabriccredential.App") as mock_app:
        mock_app.config = cfg
        from services.fabriccredential import build_credential
        cred = build_credential()
    assert isinstance(cred, ClientSecretCredential)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_fabriccredential.py -v
```

Expected: `ModuleNotFoundError: No module named 'services.fabriccredential'`

- [ ] **Step 3: Create `services/fabriccredential.py`**

```python
from azure.identity import ClientSecretCredential, UsernamePasswordCredential
from app import App


def build_credential():
    config = App.config
    mode = config.AUTHENTICATION_MODE.lower()

    if mode == "serviceprincipal":
        return ClientSecretCredential(
            tenant_id=config.TENANT_ID,
            client_id=config.CLIENT_ID,
            client_secret=config.CLIENT_SECRET,
        )
    if mode == "masteruser":
        return UsernamePasswordCredential(
            client_id=config.CLIENT_ID,
            username=config.POWER_BI_USER,
            password=config.POWER_BI_PASS,
        )
    raise ValueError(f"Unsupported AUTHENTICATION_MODE: {config.AUTHENTICATION_MODE}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_fabriccredential.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add services/fabriccredential.py tests/test_fabriccredential.py
git commit -m "feat: add fabriccredential factory for SDK auth"
```

---

## Task 2: Refactor `ListWorkspacesService`

**Files:**
- Modify: `services/listworkspaces.py`
- Create: `tests/test_listworkspaces.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_listworkspaces.py`:

```python
from unittest.mock import MagicMock
from services.listworkspaces import ListWorkspacesService


def _make_client(workspaces):
    ws = MagicMock()
    ws.id = "ws1"
    ws.display_name = "My Workspace"

    client = MagicMock()
    client.admin.workspaces.list_workspaces.return_value = iter(workspaces)
    return client


def test_list_workspaces_delegates_to_sdk():
    mock_ws = MagicMock(id="ws1", display_name="Test WS")
    client = _make_client([mock_ws])

    service = ListWorkspacesService(client)
    result = list(service.list_workspaces())

    client.admin.workspaces.list_workspaces.assert_called_once_with(
        type="Workspace", state="Active"
    )
    assert result == [mock_ws]


def test_list_workspaces_passes_type_and_state():
    client = _make_client([])

    service = ListWorkspacesService(client)
    list(service.list_workspaces(type="Personal", state="Deleted"))

    client.admin.workspaces.list_workspaces.assert_called_once_with(
        type="Personal", state="Deleted"
    )


def test_list_workspaces_returns_empty_iterable():
    client = _make_client([])
    service = ListWorkspacesService(client)
    assert list(service.list_workspaces()) == []


def test_no_list_workspaces_cont_method():
    client = MagicMock()
    service = ListWorkspacesService(client)
    assert not hasattr(service, "list_workspaces_cont")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_listworkspaces.py -v
```

Expected: FAIL — `ListWorkspacesService.__init__` does not accept a `client` argument.

- [ ] **Step 3: Replace `services/listworkspaces.py`**

```python
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from microsoft_fabric_api import FabricClient


class ListWorkspacesService:

    def __init__(self, client: FabricClient):
        self._client = client

    def list_workspaces(self, type="Workspace", state="Active"):
        """Returns all workspaces for a tenant as an iterable of Workspace objects.

        Args:
            type (str): Workspace type filter. Default "Workspace".
            state (str): Workspace state filter. Default "Active".

        Returns:
            Iterable[Workspace]: SDK workspace model objects. Pagination is handled
                automatically by the SDK.
        """
        return self._client.admin.workspaces.list_workspaces(type=type, state=state)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_listworkspaces.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add services/listworkspaces.py tests/test_listworkspaces.py
git commit -m "refactor: replace ListWorkspacesService HTTP calls with FabricClient SDK"
```

---

## Task 3: Refactor `ListItemsService`

**Files:**
- Modify: `services/listitems.py`
- Create: `tests/test_listitems.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_listitems.py`:

```python
from unittest.mock import MagicMock
from services.listitems import ListItemsService


def _make_client(items):
    client = MagicMock()
    client.core.items.list_items.return_value = iter(items)
    return client


def test_list_items_delegates_to_sdk():
    mock_item = MagicMock(id="item1", display_name="My Notebook", type="Notebook")
    client = _make_client([mock_item])

    service = ListItemsService(client)
    result = list(service.list_items("ws1"))

    client.core.items.list_items.assert_called_once_with("ws1", type=None)
    assert result == [mock_item]


def test_list_items_passes_item_type_filter():
    client = _make_client([])

    service = ListItemsService(client)
    list(service.list_items("ws1", item_type="Report"))

    client.core.items.list_items.assert_called_once_with("ws1", type="Report")


def test_list_items_returns_empty_iterable():
    client = _make_client([])
    service = ListItemsService(client)
    assert list(service.list_items("ws1")) == []


def test_no_list_items_cont_method():
    client = MagicMock()
    service = ListItemsService(client)
    assert not hasattr(service, "list_items_cont")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_listitems.py -v
```

Expected: FAIL — `ListItemsService.__init__` does not accept a `client` argument.

- [ ] **Step 3: Replace `services/listitems.py`**

```python
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from microsoft_fabric_api import FabricClient


class ListItemsService:

    def __init__(self, client: FabricClient):
        self._client = client

    def list_items(self, workspace_id: str, item_type: str = None):
        """Returns all items in a workspace as an iterable of Item objects.

        Args:
            workspace_id (str): The workspace ID to list items from.
            item_type (str | None): Optional item type filter (e.g. "Report",
                "SemanticModel", "Lakehouse", "Notebook"). None returns all types.

        Returns:
            Iterable[Item]: SDK item model objects. Pagination is handled
                automatically by the SDK.
        """
        return self._client.core.items.list_items(workspace_id, type=item_type)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_listitems.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add services/listitems.py tests/test_listitems.py
git commit -m "refactor: replace ListItemsService HTTP calls with FabricClient SDK"
```

---

## Task 4: Update `get_workspace_items.py`

**Files:**
- Modify: `get_workspace_items.py`
- Create: `tests/test_get_workspace_items.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_get_workspace_items.py`:

```python
import json
import os
import pytest
from unittest.mock import MagicMock, patch, call


def _make_workspace(ws_id, display_name):
    ws = MagicMock()
    ws.id = ws_id
    ws.display_name = display_name
    ws.as_dict.return_value = {"id": ws_id, "displayName": display_name}
    return ws


def _make_item(item_id, item_type, ws_id):
    item = MagicMock()
    item.id = item_id
    item.type = item_type
    item.as_dict.return_value = {"id": item_id, "type": item_type}
    return item


@patch("get_workspace_items.save_output")
@patch("get_workspace_items.ListItemsService")
@patch("get_workspace_items.ListWorkspacesService")
@patch("get_workspace_items.FabricClient")
@patch("get_workspace_items.build_credential")
def test_main_fetches_all_workspaces_and_items(
    mock_cred, mock_client_cls, mock_ws_svc_cls, mock_items_svc_cls, mock_save, tmp_path
):
    ws1 = _make_workspace("ws-1", "Alpha")
    ws2 = _make_workspace("ws-2", "Beta")
    item1 = _make_item("item-1", "Notebook", "ws-1")
    item2 = _make_item("item-2", "Report", "ws-2")

    mock_ws_svc = MagicMock()
    mock_ws_svc.list_workspaces.return_value = iter([ws1, ws2])
    mock_ws_svc_cls.return_value = mock_ws_svc

    mock_items_svc = MagicMock()
    mock_items_svc.list_items.side_effect = [iter([item1]), iter([item2])]
    mock_items_svc_cls.return_value = mock_items_svc

    import get_workspace_items
    get_workspace_items.output_path = str(tmp_path)

    get_workspace_items.main()

    mock_cred.assert_called_once()
    mock_client_cls.assert_called_once_with(mock_cred.return_value)
    mock_ws_svc_cls.assert_called_once_with(mock_client_cls.return_value)
    mock_items_svc_cls.assert_called_once_with(mock_client_cls.return_value)

    assert mock_items_svc.list_items.call_count == 2
    mock_items_svc.list_items.assert_any_call("ws-1", None)
    mock_items_svc.list_items.assert_any_call("ws-2", None)

    assert mock_save.call_count == 2


@patch("get_workspace_items.save_output")
@patch("get_workspace_items.ListItemsService")
@patch("get_workspace_items.ListWorkspacesService")
@patch("get_workspace_items.FabricClient")
@patch("get_workspace_items.build_credential")
def test_main_single_workspace_skips_workspace_fetch(
    mock_cred, mock_client_cls, mock_ws_svc_cls, mock_items_svc_cls, mock_save, tmp_path
):
    item1 = _make_item("item-1", "Notebook", "ws-42")

    mock_items_svc = MagicMock()
    mock_items_svc.list_items.return_value = iter([item1])
    mock_items_svc_cls.return_value = mock_items_svc

    import get_workspace_items
    get_workspace_items.output_path = str(tmp_path)

    get_workspace_items.main(workspace_id="ws-42")

    mock_ws_svc_cls.return_value.list_workspaces.assert_not_called()
    mock_items_svc.list_items.assert_called_once_with("ws-42", None)
    mock_save.assert_called_once()


@patch("get_workspace_items.save_output")
@patch("get_workspace_items.ListItemsService")
@patch("get_workspace_items.ListWorkspacesService")
@patch("get_workspace_items.FabricClient")
@patch("get_workspace_items.build_credential")
def test_main_passes_item_type_filter(
    mock_cred, mock_client_cls, mock_ws_svc_cls, mock_items_svc_cls, mock_save, tmp_path
):
    ws1 = _make_workspace("ws-1", "Alpha")
    item1 = _make_item("item-1", "Report", "ws-1")

    mock_ws_svc = MagicMock()
    mock_ws_svc.list_workspaces.return_value = iter([ws1])
    mock_ws_svc_cls.return_value = mock_ws_svc

    mock_items_svc = MagicMock()
    mock_items_svc.list_items.return_value = iter([item1])
    mock_items_svc_cls.return_value = mock_items_svc

    import get_workspace_items
    get_workspace_items.output_path = str(tmp_path)

    get_workspace_items.main(item_type="Report")

    mock_items_svc.list_items.assert_called_once_with("ws-1", "Report")


@patch("get_workspace_items.save_output")
@patch("get_workspace_items.ListItemsService")
@patch("get_workspace_items.ListWorkspacesService")
@patch("get_workspace_items.FabricClient")
@patch("get_workspace_items.build_credential")
def test_main_injects_workspace_id_into_items(
    mock_cred, mock_client_cls, mock_ws_svc_cls, mock_items_svc_cls, mock_save, tmp_path
):
    ws1 = _make_workspace("ws-99", "Alpha")
    item1 = _make_item("item-1", "Notebook", "ws-99")

    mock_ws_svc = MagicMock()
    mock_ws_svc.list_workspaces.return_value = iter([ws1])
    mock_ws_svc_cls.return_value = mock_ws_svc

    mock_items_svc = MagicMock()
    mock_items_svc.list_items.return_value = iter([item1])
    mock_items_svc_cls.return_value = mock_items_svc

    import get_workspace_items
    get_workspace_items.output_path = str(tmp_path)

    get_workspace_items.main()

    saved_items = mock_save.call_args[0][1]
    assert saved_items[0]["workspaceId"] == "ws-99"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_get_workspace_items.py -v
```

Expected: FAIL — `cannot import name 'build_credential'` or `cannot import name 'FabricClient'` from `get_workspace_items`.

- [ ] **Step 3: Replace `get_workspace_items.py`**

```python
import json
import os
from datetime import date

from azure.core.exceptions import HttpResponseError
from microsoft_fabric_api import FabricClient

from app import App
from config import BaseConfig
from services.fabriccredential import build_credential
from services.listitems import ListItemsService
from services.listworkspaces import ListWorkspacesService

# Initialize App configuration for standalone execution
App.setup(BaseConfig)

# Get today's date in YYYY-MM-DD format
current_date = date.today().strftime("%Y-%m-%d")

# Folder path for saving workspace items data
output_path = "./data/workspace_items/"


def save_output(path, data, workspace_id, filename):
    folder_path = os.path.join(path, current_date, workspace_id)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path, filename)
    with open(file_path, "w", encoding="utf-8") as outfile:
        json.dump(data, outfile, indent=2)

    print(f"Saved: {file_path}")


def main(workspace_id=None, item_type=None):
    """Retrieve Fabric workspaces and their items via the Fabric REST API.

    Args:
        workspace_id (str | None): Optional workspace ID. When provided, only
            items in that workspace are returned. When omitted, all active
            workspaces are fetched first and items are retrieved for each.
        item_type (str | None): Optional item type filter (e.g. "Report",
            "SemanticModel", "Lakehouse", "Notebook"). When omitted, all item
            types are returned.
    """
    credential = build_credential()
    client = FabricClient(credential)
    list_workspaces_service = ListWorkspacesService(client)
    list_items_service = ListItemsService(client)

    # ----- Step 1: Determine workspaces to process -----
    if workspace_id:
        workspaces_to_process = [(workspace_id, "unknown")]
        print(f"Processing workspace: {workspace_id}")
    else:
        print("Fetching all active workspaces")
        try:
            workspaces = list(list_workspaces_service.list_workspaces())
        except HttpResponseError as e:
            print(f"Error fetching workspaces: {e.status_code} {e.reason}")
            return

        print(f"Found {len(workspaces)} workspace(s)")

        folder_path = os.path.join(output_path, current_date)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        with open(
            os.path.join(folder_path, "workspaces.json"), "w", encoding="utf-8"
        ) as f:
            json.dump([ws.as_dict() for ws in workspaces], f, indent=2)

        workspaces_to_process = [(ws.id, ws.display_name) for ws in workspaces]

    # ----- Step 2: For each workspace, get its items -----
    for ws_id, ws_name in workspaces_to_process:
        print(f"\nProcessing workspace: {ws_name} ({ws_id})")

        try:
            items = list(list_items_service.list_items(ws_id, item_type))
        except HttpResponseError as e:
            print(
                f"  Error fetching items for workspace {ws_id}: "
                f"{e.status_code} {e.reason}"
            )
            continue

        items_dicts = [item.as_dict() for item in items]
        for item_dict in items_dicts:
            item_dict["workspaceId"] = ws_id

        print(f"  Found {len(items_dicts)} item(s)")

        filename = f"{ws_id}_items.json"
        if item_type:
            filename = f"{ws_id}_{item_type.lower()}_items.json"

        save_output(output_path, items_dicts, ws_id, filename)

    print("\nDone.")


if __name__ == "__main__":
    # Pass a workspace_id to scope to one workspace, or leave as None for all workspaces.
    # Pass an item_type to filter (e.g. "Report", "SemanticModel", "Lakehouse", "Notebook"),
    # or leave as None to return all item types.
    main(workspace_id=None, item_type=None)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_get_workspace_items.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Run the full test suite**

```bash
uv run pytest tests/ -v
```

Expected: All 12 tests PASSED

- [ ] **Step 6: Commit**

```bash
git add get_workspace_items.py tests/test_get_workspace_items.py
git commit -m "refactor: migrate get_workspace_items to FabricClient SDK"
```
