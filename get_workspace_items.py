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
