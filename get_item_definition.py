import base64
import os
import time
from datetime import date  # used for current_date only

from app import App
from config import BaseConfig
from services.aadservice import AadService
from services.bulkexportitemdefinitions import BulkExportItemDefinitionsService
from services.cloudlogger import get_logger


def _parse_retry_after(value, default):
    """Parse a Retry-After header value as seconds, falling back to default."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


App.setup(BaseConfig)

logger = get_logger(__name__)

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
            logger.warning("Skipping part with empty path for item %s", item_id)
            continue

        if payload_type != "InlineBase64":
            logger.warning("Unsupported payloadType '%s' for %s, skipping", payload_type, path)
            continue

        try:
            decoded = base64.b64decode(payload)
            full_path = os.path.realpath(os.path.join(output_dir, path))
            safe_root = os.path.realpath(output_dir)
            if not full_path.startswith(safe_root + os.sep):
                logger.warning("Skipping unsafe path '%s' for item %s", path, item_id)
                continue
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(decoded)
            written += 1
        except Exception as e:
            logger.error("Error writing %s for item %s: %s", path, item_id, e)

    logger.info("Wrote %s/%s definition parts for item %s", written, len(parts), item_id)


def main(workspace_id, item_id, format=None):
    """Get the definition of a single Fabric item and write it to disk.

    Args:
        workspace_id (str): The workspace ID containing the item.
        item_id (str): The item ID.
        format (str | None): Optional format of the item definition.
    """
    # access_token = AadService.get_access_token()
    access_token = ''  # swap in for manual testing without live auth

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
            logger.debug("Immediate result received for item %s", item_id)
            break

        elif response.status_code == 202:
            location_url = response.headers.get("Location", "")
            op_id = response.headers.get("x-ms-operation-id", "")
            retry_after = _parse_retry_after(response.headers.get("Retry-After"), 5)
            if not op_id or not location_url:
                logger.error("202 response missing Location or x-ms-operation-id header for item %s", item_id)
                return
            logger.info("LRO started for item %s, op_id=%s", item_id, op_id)
            break

        elif response.status_code == 429:
            retry_after = _parse_retry_after(response.headers.get("Retry-After"), 10)
            logger.warning("Rate limited, retrying in %ss", retry_after)
            time.sleep(retry_after)

        else:
            try:
                err_code = response.json().get("errorCode", "")
            except Exception:
                err_code = ""
            if err_code == "OperationNotSupportedForItem":
                logger.warning("Item %s does not support definition export", item_id)
            else:
                logger.error(
                    "%s %s (%s): %s RequestId: %s",
                    response.status_code,
                    response.reason,
                    err_code,
                    response.text,
                    response.headers.get("RequestId"),
                )
            return

    # Phase 2: poll LRO if needed
    if data is None:
        while True:
            logger.debug("Waiting %ss for LRO op_id=%s", retry_after, op_id)
            time.sleep(retry_after)

            status_response = svc.get_operation_status(access_token, op_id)

            if not status_response.ok:
                logger.error(
                    "Error checking status for op %s: %s %s",
                    op_id,
                    status_response.status_code,
                    status_response.text,
                )
                continue  # retry with same retry_after

            status_data = status_response.json()
            status = status_data.get("status", "")

            if status == "Succeeded":
                logger.debug("LRO succeeded for op_id=%s, fetching result", op_id)
                result_response = svc.get_operation_result(access_token, location_url)
                if result_response.ok:
                    data = result_response.json()
                else:
                    logger.error(
                        "Error fetching result for item %s, op_id=%s: %s %s",
                        item_id,
                        op_id,
                        result_response.status_code,
                        result_response.text,
                    )
                    return
                break

            elif status == "Failed":
                logger.error("LRO failed for item %s, op_id=%s: %s", item_id, op_id, status_data)
                return

            else:  # Running or unrecognised
                retry_after = _parse_retry_after(
                    status_response.headers.get("Retry-After"), retry_after
                )

    # Phase 3: decode and write files
    logger.info("Writing definition for item %s", item_id)
    write_definition(workspace_id, item_id, data)
    logger.info("Done.")


if __name__ == "__main__":
    # Required: set workspace_id and item_id before running.
    main(
        workspace_id="<your-workspace-id>",
        item_id="<your-item-id>",
        format=None,
    )
