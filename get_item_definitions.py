import base64
import json
import os
import time
from datetime import date, datetime

from app import App
from config import BaseConfig
from services.aadservice import AadService
from services.bulkexportitemdefinitions import BulkExportItemDefinitionsService
from services.listworkspaces import ListWorkspacesService

App.setup(BaseConfig)

current_date = date.today().strftime("%Y-%m-%d")
OUTPUT_BASE = "./data/item_definitions"


def get_workspaces(access_token, workspace_id=None):
    """Resolve the list of workspaces to process.

    Args:
        access_token (str): Access token.
        workspace_id (str | None): When provided, returns a single-item list.
            When None, fetches all active workspaces with pagination.

    Returns:
        list[dict]: List of workspace dicts with at least an "id" key.

    Raises:
        SystemExit: If the workspace list cannot be fetched.
    """
    if workspace_id:
        return [{"id": workspace_id}]

    svc = ListWorkspacesService()
    response = svc.list_workspaces(access_token)

    if not response.ok:
        print(
            f"Error fetching workspaces: {response.status_code} {response.reason}"
        )
        print(response.content)
        raise SystemExit(1)

    data = response.json()
    workspaces = data.get("workspaces", [])

    while data.get("continuationUri"):
        cont = svc.list_workspaces_cont(access_token, data["continuationUri"])
        if not cont.ok:
            print(
                f"Error fetching continuation workspaces: {cont.status_code} {cont.reason}"
            )
            break
        data = cont.json()
        workspaces.extend(data.get("workspaces", []))

    print(f"Found {len(workspaces)} workspace(s)")
    return workspaces


def fire_export_requests(access_token, workspaces):
    """Phase 1: POST bulkExportDefinitions for each workspace.

    Retries indefinitely on 429, skips workspace on any other error.

    Args:
        access_token (str): Access token.
        workspaces (list[dict]): Workspaces to process.

    Returns:
        tuple[list, list]: (immediate_results, pending_ops)
            immediate_results: list of (ws_id, data) for 200 responses.
            pending_ops: list of op dicts for 202 responses.
    """
    svc = BulkExportItemDefinitionsService()
    immediate_results = []
    pending_ops = []

    for ws in workspaces:
        ws_id = ws.get("id")
        ws_name = ws.get("displayName", ws.get("name", "unknown"))
        print(f"Requesting export for: {ws_name} ({ws_id})")

        while True:
            response = svc.bulk_export_definitions(access_token, ws_id)

            if response.status_code == 200:
                immediate_results.append((ws_id, response.json()))
                print(f"  Immediate result received")
                break

            elif response.status_code == 202:
                location = response.headers.get("Location", "")
                op_id = response.headers.get("x-ms-operation-id", "")
                retry_after = int(response.headers.get("Retry-After", 5))
                pending_ops.append({
                    "ws_id": ws_id,
                    "location_url": location,
                    "op_id": op_id,
                    "retry_after": retry_after,
                    "next_check_at": datetime.now().timestamp() + retry_after,
                })
                print(f"  LRO started, op_id={op_id}")
                break

            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 10))
                print(f"  Rate limited, retrying in {retry_after}s")
                time.sleep(retry_after)

            else:
                print(
                    f"  Error {response.status_code} {response.reason}: {response.text}"
                )
                break

    return immediate_results, pending_ops


def poll_pending_operations(access_token, pending_ops):
    """Phase 2: Poll all pending LROs until each succeeds or fails.

    Uses per-op next_check_at timestamps to avoid unnecessary sleeping.

    Args:
        access_token (str): Access token.
        pending_ops (list[dict]): Op dicts from fire_export_requests.

    Returns:
        list[tuple]: (ws_id, data) pairs for each succeeded operation.
    """
    svc = BulkExportItemDefinitionsService()
    results = []

    while pending_ops:
        now = datetime.now().timestamp()
        earliest = min(op["next_check_at"] for op in pending_ops)
        wait = max(0.0, earliest - now)

        if wait > 0:
            print(f"Waiting {wait:.1f}s for next LRO check...")
            time.sleep(wait)

        still_pending = []

        for op in pending_ops:
            if datetime.now().timestamp() < op["next_check_at"]:
                still_pending.append(op)
                continue

            status_response = svc.get_operation_status(access_token, op["op_id"])

            if not status_response.ok:
                print(
                    f"  Error checking status for op {op['op_id']}: "
                    f"{status_response.status_code} {status_response.text}"
                )
                op["next_check_at"] = datetime.now().timestamp() + op["retry_after"]
                still_pending.append(op)
                continue

            status = status_response.json().get("status", "")

            if status == "Succeeded":
                print(f"  LRO succeeded for workspace {op['ws_id']}, fetching result...")
                result_response = svc.get_operation_result(
                    access_token, op["location_url"]
                )
                if result_response.ok:
                    results.append((op["ws_id"], result_response.json()))
                else:
                    print(
                        f"  Error fetching result for workspace {op['ws_id']}: "
                        f"{result_response.status_code} {result_response.text}"
                    )

            elif status == "Failed":
                print(
                    f"  LRO failed for workspace {op['ws_id']}, op_id={op['op_id']}: "
                    f"{status_response.json()}"
                )

            else:  # Running or unrecognised — keep polling
                retry_after = int(
                    status_response.headers.get("Retry-After", op["retry_after"])
                )
                op["next_check_at"] = datetime.now().timestamp() + retry_after
                still_pending.append(op)

        pending_ops = still_pending

    return results


def write_definitions(ws_id, data):
    """Phase 3: Decode base64 payloads and write definition files to disk.

    Output path: data/item_definitions/{date}/{ws_id}/{path from API}
    Also writes _index.json for traceability.

    Args:
        ws_id (str): Workspace ID (used as output subfolder name).
        data (dict): BulkExportItemDefinitionsResponse JSON.
    """
    output_dir = os.path.join(OUTPUT_BASE, current_date, ws_id)
    os.makedirs(output_dir, exist_ok=True)

    index = data.get("itemDefinitionsIndex", [])
    with open(os.path.join(output_dir, "_index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    parts = data.get("definitionParts", [])
    written = 0

    for part in parts:
        path = part.get("path", "").lstrip("/")
        payload = part.get("payload", "")
        payload_type = part.get("payloadType", "")

        if not path:
            print(f"  Skipping part with empty path for workspace {ws_id}")
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
            print(f"  Error writing {path} for workspace {ws_id}: {e}")

    print(f"  Wrote {written}/{len(parts)} definition parts for workspace {ws_id}")


def main(workspace_id=None):
    """Bulk export Fabric item definitions across workspaces and write to disk.

    Args:
        workspace_id (str | None): Optional workspace ID to scope to one workspace.
            When omitted, all active workspaces are processed.
    """
    access_token = AadService.get_access_token()
    # access_token = ''  # swap in for manual testing without live auth

    # Phase 0: resolve workspaces
    workspaces = get_workspaces(access_token, workspace_id)

    # Phase 1: fire all export requests
    immediate_results, pending_ops = fire_export_requests(access_token, workspaces)
    print(
        f"\nPhase 1 complete: {len(immediate_results)} immediate, "
        f"{len(pending_ops)} pending LRO(s)"
    )

    # Phase 2: poll pending LROs
    polled_results = poll_pending_operations(access_token, pending_ops)
    print(f"Phase 2 complete: {len(polled_results)} LRO result(s) received")

    # Phase 3: decode and write files
    all_results = immediate_results + polled_results
    print(f"\nWriting definitions for {len(all_results)} workspace(s)...")
    for ws_id, data in all_results:
        write_definitions(ws_id, data)

    print("\nDone.")


if __name__ == "__main__":
    # Pass a workspace_id to scope to one workspace, or leave as None for all workspaces.
    main(workspace_id=None)
