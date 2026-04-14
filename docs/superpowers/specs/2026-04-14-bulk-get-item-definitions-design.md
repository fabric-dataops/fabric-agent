# Bulk Get Item Definitions — Design Spec

Date: 2026-04-14

## Overview

Add a standalone script that bulk-exports Fabric item definitions across all workspaces in a tenant using the Fabric REST API `bulkExportDefinitions` (beta) endpoint. Each item's definition files are decoded from base64 and written to disk, preserving the folder/file path structure returned by the API.

---

## API

**Endpoint:**
```
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/items/bulkExportDefinitions?beta=true
```

**Request body:**
```json
{ "mode": "All" }
```
`mode: "All"` exports all supported item types in the workspace in a single call — no prior item enumeration required.

**Responses:**
- `200 OK` — immediate result with `BulkExportItemDefinitionsResponse`
- `202 Accepted` — LRO in progress; headers: `Location`, `x-ms-operation-id`, `Retry-After`
- `429 Too Many Requests` — rate limited; header: `Retry-After`

**Response body (200 or LRO result):**
```json
{
  "itemDefinitionsIndex": [
    { "id": "<uuid>", "rootPath": "/Folder/MyReport.Report" }
  ],
  "definitionParts": [
    { "path": "/Folder/MyReport.Report/definition.pbir", "payload": "<base64>", "payloadType": "InlineBase64" }
  ]
}
```

**Required scope:** `Item.ReadWrite.All`

**Permissions:** Caller must have contributor or higher on each workspace. Only items for which the caller has both read and write permissions are exported.

---

## New Files

| File | Purpose |
|---|---|
| `services/bulkexportitemdefinitions.py` | Service class wrapping the Fabric API calls |
| `get_item_definitions.py` | Standalone script with two-phase orchestration |

### Reused

- `services/listworkspaces.py` — workspace enumeration with continuation URI pagination
- `services/aadservice.py` — access token
- `app.py` / `config.py` — `FABRIC_API_URL` config

---

## Service Layer — `services/bulkexportitemdefinitions.py`

```python
class BulkExportItemDefinitionsService:

    def bulk_export_definitions(self, access_token, workspace_id):
        """POST /v1/workspaces/{workspaceId}/items/bulkExportDefinitions?beta=true
        Body: {"mode": "All"}
        Returns raw Response — caller inspects status code (200 / 202 / 429 / error).
        """

    def get_operation_status(self, access_token, operation_id):
        """GET /v1/operations/{operation_id}
        Returns response with JSON: {"status": "Running"|"Succeeded"|"Failed", ...}
        """

    def get_operation_result(self, access_token, location_url):
        """GET {location_url}/result
        Returns raw Response containing BulkExportItemDefinitionsResponse JSON.
        """
```

Status and result calls are separate (not combined into a blocking loop) so the script can drive polling across all pending workspaces simultaneously.

---

## Script Orchestration — `get_item_definitions.py`

### Signature

```python
def main(workspace_id=None):
    """
    workspace_id: optional — scope to one workspace; omit to process all active workspaces.
    """
```

Consistent with `get_workspace_items.py`.

### Phase 0: Resolve workspaces

If `workspace_id` is provided, use `[{"id": workspace_id}]`. Otherwise, enumerate all active workspaces using `ListWorkspacesService` with continuation URI pagination (same loop as `get_workspace_items.py`).

### Phase 1: Fire all export requests

For each workspace, call `bulk_export_definitions` in a retry loop:

```
while True:
    POST bulkExportDefinitions
    200 → add to immediate_results [(ws_id, data)], break
    202 → add to pending_ops [(ws_id, location_url, op_id, retry_after)], break
    429 → sleep(Retry-After), continue   # retry indefinitely
    other error → log error, skip workspace, break
```

### Phase 2: Poll all pending LROs

Each pending op tracks a `next_check_at` timestamp (set to `now + retry_after` when added).

```
while pending_ops is not empty:
    sleep until the earliest next_check_at among pending ops
    for each op where now >= next_check_at:
        GET /v1/operations/{op_id}
        Succeeded → GET result, add to results, remove from pending
        Failed    → log error (ws_id, op_id), remove from pending
        Running   → set next_check_at = now + retry_after from response
```

### Phase 3: Process results

For each (ws_id, data) in immediate_results + polled_results:
1. Write `_index.json` (the raw `itemDefinitionsIndex` array) to the workspace output folder
2. For each entry in `definitionParts`:
   - Decode `payload` from base64
   - Strip leading `/` from `path`
   - Write decoded bytes to `data/item_definitions/{date}/{ws_id}/{path}`
   - Create intermediate directories as needed
3. Log file write errors per-part (skip that file, continue)

---

## Output Structure

```
data/item_definitions/
  {YYYY-MM-DD}/
    {workspace_id}/
      _index.json                              ← itemDefinitionsIndex for traceability
      Folder1/
        MyReport.Report/
          .platform
          definition.pbir
        MyDataset.SemanticModel/
          .platform
          model.bim
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| 429 on POST | Retry loop with `Retry-After` backoff, no cap |
| LRO status `"Failed"` | Log error (workspace ID + op ID), skip workspace, continue |
| `ItemsHaveProtectedLabels` | Log warning (workspace ID), skip workspace, continue |
| File write error for a part | Log error (workspace ID + path), skip that file, continue |
| Workspace list fetch error | Log error, abort (can't proceed without workspace list) |

Per-workspace errors never stop the overall run.

---

## Not in Scope

- Selective mode (`mode: "Selective"`) — not needed; `All` covers the use case
- Bulk import — separate feature
- Incremental / modified-since filtering — not supported by this API
