import json
import os
from datetime import date

from azure.core.exceptions import HttpResponseError
from microsoft_fabric_api import FabricClient

from app import App
from config import BaseConfig
from services.cloudlogger import get_logger
from services.fabriccredential import build_credential
from services.listworkspaces import ListWorkspacesService

App.setup(BaseConfig)

logger = get_logger(__name__)

current_date = date.today().strftime("%Y-%m-%d")
OUTPUT_BASE = "./data/workspaces/fabric"


def save_workspaces(workspaces):
    """Write the workspace list as JSON under data/workspaces/fabric/{date}/.

    Args:
        workspaces (list): Serialised workspace dicts.

    Returns:
        str: Path of the file written.
    """
    output_dir = os.path.join(OUTPUT_BASE, current_date)
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, "workspaces.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(workspaces, f, indent=2)

    logger.info("Saved %s workspace(s) to %s", len(workspaces), file_path)
    return file_path


def main(type="Workspace", state="Active"):
    """Fetch all Fabric workspaces via the SDK and save to disk.

    Args:
        type (str): Workspace type filter. Default "Workspace".
        state (str): Workspace state filter. Default "Active".
    """
    credential = build_credential()
    client = FabricClient(credential)
    svc = ListWorkspacesService(client)

    logger.info("Fetching workspaces (type=%s, state=%s)", type, state)

    try:
        workspaces = list(svc.list_workspaces(type=type, state=state))
    except HttpResponseError as e:
        logger.error(
            "Error fetching workspaces: %s %s",
            e.status_code,
            e.reason,
        )
        return

    logger.info("Received %s workspace(s)", len(workspaces))

    if not workspaces:
        logger.warning("No workspaces returned.")
        return

    workspace_dicts = [ws.serialize() for ws in workspaces]
    save_workspaces(workspace_dicts)
    logger.info("Done.")


if __name__ == "__main__":
    main()
