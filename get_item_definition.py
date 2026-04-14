import base64
import os
import time
from datetime import date  # used for current_date only

from app import App
from config import BaseConfig
from services.aadservice import AadService
from services.bulkexportitemdefinitions import BulkExportItemDefinitionsService


def _parse_retry_after(value, default):
    """Parse a Retry-After header value as seconds, falling back to default."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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
        path = part.get("path", "").lstrip("/")
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
            full_path = os.path.realpath(os.path.join(output_dir, path))
            safe_root = os.path.realpath(output_dir)
            if not full_path.startswith(safe_root + os.sep):
                print(f"  Skipping unsafe path '{path}' for item {item_id}")
                continue
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
            retry_after = _parse_retry_after(response.headers.get("Retry-After"), 5)
            if not op_id or not location_url:
                print(f"Error: 202 response missing Location or x-ms-operation-id header")
                return
            print(f"LRO started for item {item_id}, op_id={op_id}")
            break

        elif response.status_code == 429:
            retry_after = _parse_retry_after(response.headers.get("Retry-After"), 10)
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
                        f"Error fetching result for item {item_id}, op_id={op_id}: "
                        f"{result_response.status_code} {result_response.text}"
                    )
                    return
                break

            elif status == "Failed":
                print(f"LRO failed for item {item_id}, op_id={op_id}: {status_data}")
                return

            else:  # Running or unrecognised
                retry_after = _parse_retry_after(
                    status_response.headers.get("Retry-After"), retry_after
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
