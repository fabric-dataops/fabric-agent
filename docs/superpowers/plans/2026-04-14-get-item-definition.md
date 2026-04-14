# Get Item Definition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a standalone script that fetches a single Fabric item's definition via the `getDefinition` API, decodes base64 payloads, and writes the files to disk.

**Architecture:** Add one method (`get_item_definition`) to the existing `BulkExportItemDefinitionsService`, reusing its `get_operation_status` and `get_operation_result` for LRO polling. A new standalone script (`get_item_definition.py`) handles the call, polling loop, and file writing — following the same pattern as `get_item_definitions.py`.

**Tech Stack:** Python 3.13, `requests`, `base64` (stdlib), `time`/`datetime` (stdlib), existing `AadService` + `App`/`BaseConfig`.

---

### Task 1: Add `get_item_definition` method to service

**Files:**
- Modify: `services/bulkexportitemdefinitions.py`

The current file has three methods: `bulk_export_definitions`, `get_operation_status`, `get_operation_result`. Add `get_item_definition` as a fourth method at the end of the class.

- [ ] **Step 1: Add the method to `services/bulkexportitemdefinitions.py`**

Append the following method inside the `BulkExportItemDefinitionsService` class (after the closing of `get_operation_result`, before the end of the file):

```python
    def get_item_definition(self, access_token, workspace_id, item_id, format=None):
        """Returns the definition of a single Fabric item.

        Args:
            access_token (str): Access token to call API.
            workspace_id (str): The workspace ID.
            item_id (str): The item ID.
            format (str | None): Optional format of the item definition.

        Returns:
            Response: 200 (immediate result), 202 (LRO started), 429 (rate limited),
                      or other error status.
        """
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        endpoint_url = (
            f"{app.config.FABRIC_API_URL}v1/workspaces/{workspace_id}"
            f"/items/{item_id}/getDefinition"
        )
        if format:
            endpoint_url += f"?format={format}"

        return requests.post(
            endpoint_url,
            headers=self.headers,
            verify=True,
            timeout=180,
        )
```

- [ ] **Step 2: Verify the method is importable**

Run: `uv run python -c "from services.bulkexportitemdefinitions import BulkExportItemDefinitionsService; s = BulkExportItemDefinitionsService(); print(hasattr(s, 'get_item_definition'))"`

Expected output: `True`

- [ ] **Step 3: Commit**

```bash
git add services/bulkexportitemdefinitions.py
git commit -m "add get_item_definition method to BulkExportItemDefinitionsService"
```

---

### Task 2: Standalone script

**Files:**
- Create: `get_item_definition.py`

- [ ] **Step 1: Create the script**

```python
import base64
import os
import time
from datetime import date  # used for current_date only

from app import App
from config import BaseConfig
from services.aadservice import AadService
from services.bulkexportitemdefinitions import BulkExportItemDefinitionsService

App.setup(BaseConfig)

current_date = date.today().strftime("%Y-%m-%d")
OUTPUT_BASE = "./data/item_definitions"


def write_definition(ws_id, item_id, data):
    """Decode base64 payloads and write definition files to disk.

    Output path: data/item_definitions/{date}/{ws_id}/{item_id}/{path from API}

    Args:
        ws_id (str): Workspace ID (used as subfolder).
        item_id (str): Item ID (used as subfolder).
        data (dict): ItemDefinitionResponse JSON.
    """
    output_dir = os.path.join(OUTPUT_BASE, current_date, ws_id, item_id)
    os.makedirs(output_dir, exist_ok=True)

    parts = data.get("definition", {}).get("parts", [])
    written = 0

    for part in parts:
        path = part.get("path", "")
        payload = part.get("payload", "")
        payload_type = part.get("payloadType", "")

        if not path:
            print(f"  Skipping part with empty path for item {item_id}")
            continue

        if payload_type != "InlineBase64":
            print(f"  Unsupported payloadType '{payload_type}' for {path}, skipping")
            continue

        try:
            decoded = base64.b64decode(payload)
            full_path = os.path.join(output_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(decoded)
            written += 1
        except Exception as e:
            print(f"  Error writing {path} for item {item_id}: {e}")

    print(f"  Wrote {written}/{len(parts)} definition parts for item {item_id}")


def main(workspace_id, item_id, format=None):
    """Get the definition of a single Fabric item and write it to disk.

    Args:
        workspace_id (str): The workspace ID containing the item.
        item_id (str): The item ID.
        format (str | None): Optional format of the item definition.
    """
    access_token = AadService.get_access_token()
    # access_token = ''  # swap in for manual testing without live auth

    svc = BulkExportItemDefinitionsService()

    # Phase 1: request the item definition
    location_url = None
    op_id = None
    retry_after = 5
    data = None

    while True:
        response = svc.get_item_definition(access_token, workspace_id, item_id, format)

        if response.status_code == 200:
            data = response.json()
            print(f"Immediate result received for item {item_id}")
            break

        elif response.status_code == 202:
            location_url = response.headers.get("Location", "")
            op_id = response.headers.get("x-ms-operation-id", "")
            retry_after = int(response.headers.get("Retry-After", 5))
            print(f"LRO started for item {item_id}, op_id={op_id}")
            break

        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 10))
            print(f"Rate limited, retrying in {retry_after}s")
            time.sleep(retry_after)

        else:
            try:
                err_code = response.json().get("errorCode", "")
            except Exception:
                err_code = ""
            if err_code == "OperationNotSupportedForItem":
                print(f"Warning: item {item_id} does not support definition export")
            else:
                print(
                    f"Error {response.status_code} {response.reason} "
                    f"({err_code}): {response.text}"
                )
            return

    # Phase 2: poll LRO if needed
    if data is None:
        while True:
            print(f"Waiting {retry_after}s for LRO...")
            time.sleep(retry_after)

            status_response = svc.get_operation_status(access_token, op_id)

            if not status_response.ok:
                print(
                    f"Error checking status for op {op_id}: "
                    f"{status_response.status_code} {status_response.text}"
                )
                continue  # retry with same retry_after

            status_data = status_response.json()
            status = status_data.get("status", "")

            if status == "Succeeded":
                print(f"LRO succeeded, fetching result...")
                result_response = svc.get_operation_result(access_token, location_url)
                if result_response.ok:
                    data = result_response.json()
                else:
                    print(
                        f"Error fetching result: "
                        f"{result_response.status_code} {result_response.text}"
                    )
                    return
                break

            elif status == "Failed":
                print(f"LRO failed for item {item_id}, op_id={op_id}: {status_data}")
                return

            else:  # Running or unrecognised
                retry_after = int(
                    status_response.headers.get("Retry-After", retry_after)
                )

    # Phase 3: decode and write files
    print(f"\nWriting definition for item {item_id}...")
    write_definition(workspace_id, item_id, data)
    print("\nDone.")


if __name__ == "__main__":
    # Required: set workspace_id and item_id before running.
    main(
        workspace_id="<your-workspace-id>",
        item_id="<your-item-id>",
        format=None,
    )
```

- [ ] **Step 2: Verify the script is importable (syntax check)**

Run: `uv run python -c "import get_item_definition; print('OK')"`

Expected output: `OK`

- [ ] **Step 3: Run against a known item**

Edit the `if __name__ == "__main__":` block to set real IDs:

```python
if __name__ == "__main__":
    main(
        workspace_id="<your-workspace-id>",
        item_id="<your-item-id>",
        format=None,
    )
```

Run: `uv run python get_item_definition.py`

Expected output (shape):
```
LRO started for item <item-id>, op_id=<op-id>    ← or "Immediate result received"
Waiting 5s for LRO...
LRO succeeded, fetching result...

Writing definition for item <item-id>...
  Wrote N/N definition parts for item <item-id>

Done.
```

Verify files on disk:
```bash
find data/item_definitions -type f | head -20
```

- [ ] **Step 4: Commit**

```bash
git add get_item_definition.py
git commit -m "add get item definition script"
```
