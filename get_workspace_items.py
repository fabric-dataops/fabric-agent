import json
import os
from datetime import date

from app import App
from config import BaseConfig
from services.aadservice import AadService
from services.listitems import ListItemsService
from services.listworkspaces import ListWorkspacesService

# Initialize App configuration for standalone execution
App.setup(BaseConfig)

# Get today's date in YYYY-MM-DD format
current_date = date.today().strftime("%Y-%m-%d")

# Folder path for saving workspace items data
output_path = "./data/workspace_items/"


def save_output(path, data, workspace_id, filename):
    """Save JSON data to a file organised by date and workspace.

    Args:
        path (str): Base output directory.
        data (dict | list): JSON-serialisable data to write.
        workspace_id (str): The workspace ID used as a sub-folder.
        filename (str): Name of the output file.
    """

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

    # Obtain an access token
    # access_token = AadService.get_access_token()
    access_token = ''
    list_workspaces_service = ListWorkspacesService()
    list_items_service = ListItemsService()

    # ----- Step 1: Determine workspaces to process -----
    if workspace_id:
        workspaces = [{"id": workspace_id}]
        print(f"Processing workspace: {workspace_id}")
    else:
        print("Fetching all active workspaces")
        workspaces_response = list_workspaces_service.list_workspaces(access_token)

        if not workspaces_response.ok:
            print(
                f"Error fetching workspaces: {workspaces_response.status_code} "
                f"{workspaces_response.reason}"
            )
            print(workspaces_response.content)
            return

        workspaces_data = workspaces_response.json()
        workspaces = workspaces_data.get("workspaces", [])

        # Handle pagination via continuationUri
        while workspaces_data.get("continuationUri"):
            continuation_response = list_workspaces_service.list_workspaces_cont(
                access_token, workspaces_data["continuationUri"]
            )
            if not continuation_response.ok:
                print(
                    f"Error fetching continuation workspaces: "
                    f"{continuation_response.status_code} {continuation_response.reason}"
                )
                break
            workspaces_data = continuation_response.json()
            workspaces.extend(workspaces_data.get("workspaces", []))

        print(f"Found {len(workspaces)} workspace(s)")

        # Save the full workspaces list
        folder_path = os.path.join(output_path, current_date)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        with open(
            os.path.join(folder_path, "workspaces.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(workspaces, f, indent=2)

    # ----- Step 2: For each workspace, get its items -----
    for workspace in workspaces:
        ws_id = workspace.get("id")
        ws_name = workspace.get("displayName", workspace.get("name", "unknown"))

        print(f"\nProcessing workspace: {ws_name} ({ws_id})")

        items_response = list_items_service.list_items(access_token, ws_id, item_type)

        if not items_response.ok:
            print(
                f"  Error fetching items for workspace {ws_id}: "
                f"{items_response.status_code} {items_response.reason}"
            )
            continue

        items_data = items_response.json()
        items = items_data.get("value", [])

        # Handle pagination via continuationUri
        while items_data.get("continuationUri"):
            continuation_response = list_items_service.list_items_cont(
                access_token, items_data["continuationUri"]
            )
            if not continuation_response.ok:
                print(
                    f"  Error fetching continuation items for workspace {ws_id}: "
                    f"{continuation_response.status_code} {continuation_response.reason}"
                )
                break
            items_data = continuation_response.json()
            items.extend(items_data.get("value", []))

        # Inject the workspace ID into each item record
        for item in items:
            item["workspaceId"] = ws_id

        print(f"  Found {len(items)} item(s)")

        # Save items for this workspace
        filename = f"{ws_id}_items.json"
        if item_type:
            filename = f"{ws_id}_{item_type.lower()}_items.json"

        save_output(output_path, items, ws_id, filename)

    print("\nDone.")


if __name__ == "__main__":
    # Pass a workspace_id to scope to one workspace, or leave as None for all workspaces.
    # Pass an item_type to filter (e.g. "Report", "SemanticModel", "Lakehouse", "Notebook"),
    # or leave as None to return all item types.
    main(workspace_id=None, item_type=None)
