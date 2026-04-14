# Get Item Definition — Design Spec

Date: 2026-04-14

## Overview

Add a standalone script that retrieves the definition of a single Fabric item using the `Items - Get Item Definition` API, decoding base64 payloads and writing each file to disk preserving the path structure returned by the API.

---

## API

**Endpoint:**
```
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/items/{itemId}/getDefinition?format={format}
```

No request body. `format` is optional.

**Responses:**
- `200 OK` — immediate result with `ItemDefinitionResponse`
- `202 Accepted` — LRO in progress; headers: `Location`, `x-ms-operation-id`, `Retry-After`
- `429 Too Many Requests` — rate limited; header: `Retry-After`

**Response body (200 or LRO result):**
```json
{
  "definition": {
    "parts": [
      { "path": "report.json", "payload": "<base64>", "payloadType": "InlineBase64" },
      { "path": "definition.pbir", "payload": "<base64>", "payloadType": "InlineBase64" },
      { "path": ".platform", "payload": "<base64>", "payloadType": "InlineBase64" }
    ]
  }
}
```

Paths are relative to the item root with no leading `/`.

**Required scope:** `Item.ReadWrite.All` (or item-specific scope, e.g. `Notebook.ReadWrite.All`)

**Limitations:** Blocked for items with a protected sensitivity label.

---

## Changes

| File | Action | Responsibility |
|---|---|---|
| `services/bulkexportitemdefinitions.py` | Modify | Add `get_item_definition` method |
| `get_item_definition.py` | Create | Standalone script — orchestration, LRO polling, decode & write |

### Reused (unchanged)

- `get_operation_status` / `get_operation_result` — already on `BulkExportItemDefinitionsService`
- `services/aadservice.py` — access token
- `app.py` / `config.py` — `FABRIC_API_URL` config

---

## Service Layer

### New method on `BulkExportItemDefinitionsService`

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
```

Endpoint: `POST {FABRIC_API_URL}v1/workspaces/{workspace_id}/items/{item_id}/getDefinition`
Query param: `?format={format}` appended only when `format` is provided.
No request body.

---

## Script Orchestration — `get_item_definition.py`

### Signature

```python
def main(workspace_id, item_id, format=None):
```

`workspace_id` and `item_id` are required. `format` is optional.

### Flow

```
main(workspace_id, item_id, format=None)
│
├── Phase 1: Call get_item_definition
│   Loop:
│     200 → process immediately, break
│     202 → record location_url, op_id, retry_after; break
│     429 → sleep(Retry-After), continue (no cap)
│     other error → log and return
│
├── Phase 2: Poll LRO (only if 202)
│   Loop:
│     sleep(retry_after)
│     GET operation status
│       Succeeded → GET result, proceed to write
│       Failed    → log error (ws_id, item_id, op_id), return
│       Running   → update retry_after from Retry-After header, continue
│       status check error → log, retry after retry_after backoff
│
└── Phase 3: write_definition(ws_id, item_id, data)
    For each part in data["definition"]["parts"]:
      Decode InlineBase64 payload
      Write to data/item_definitions/{date}/{ws_id}/{item_id}/{path}
      Create intermediate directories as needed
      On file write error: log, skip that file, continue
```

---

## Output Structure

```
data/item_definitions/
  {YYYY-MM-DD}/
    {workspace_id}/
      {item_id}/
        .platform
        definition.pbir
        report.json
```

Shares the same root (`data/item_definitions/`) as the bulk export script. No `_index.json` — the folder name is the item identifier.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| 429 on POST | Retry loop with `Retry-After` backoff, no cap |
| LRO `"Failed"` | Log error (workspace ID, item ID, op ID), return |
| `OperationNotSupportedForItem` | Log warning, return |
| Protected sensitivity label | Log warning (from error response text/errorCode), return |
| LRO status check error | Log error, retry after `retry_after` backoff |
| File write error for a part | Log error, skip that file, continue writing others |

Single-item script — errors exit rather than continuing.

---

## Not in Scope

- Bulk or multi-item processing — use `get_item_definitions.py` for that
- `format` enumeration — passed through as-is from caller
