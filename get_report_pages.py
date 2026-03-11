import json
import os
from datetime import date

from app import App
from config import BaseConfig
from services.aadservice import AadService
from services.powerbi.getreportpages import GetReportPagesService

# Initialize App configuration for standalone execution
App.setup(BaseConfig)

# Get today's date in YYYY-MM-DD format
current_date = date.today().strftime("%Y-%m-%d")

# Folder path for saving report pages data
output_path = "./data/report_pages/"


def save_output(path, data, workspace_id, report_id, filename):
    """Save JSON data to a file organised by date, workspace, and report.

    Args:
        path (str): Base output directory.
        data (dict | list): JSON-serialisable data to write.
        workspace_id (str): The workspace (group) ID used as a sub-folder.
        report_id (str): The report ID used as a sub-folder.
        filename (str): Name of the output file.
    """

    folder_path = os.path.join(path, current_date, workspace_id, report_id)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path, filename)
    with open(file_path, "w", encoding="utf-8") as outfile:
        json.dump(data, outfile, indent=2)

    print(f"Saved: {file_path}")


def main(workspace_id, report_id):
    """Retrieve pages for a given report in a workspace via the Power BI REST API.

    Args:
        workspace_id (str): The workspace (group) ID.
        report_id (str): The report ID.
    """

    # Obtain an access token
    # access_token = AadService.get_access_token()
    access_token = ''
    report_pages_service = GetReportPagesService()

    print(
        f"Fetching pages for report: {report_id} "
        f"in workspace: {workspace_id}"
    )

    pages_response = report_pages_service.get_pages_in_group(
        access_token, workspace_id, report_id
    )

    if not pages_response.ok:
        print(
            f"Error fetching pages: {pages_response.status_code} "
            f"{pages_response.reason}"
        )
        print(pages_response.content)
        return

    pages_data = pages_response.json()
    pages = pages_data.get("value", [])

    print(f"Found {len(pages)} page(s)")

    # Save pages for this report
    save_output(
        output_path,
        pages,
        workspace_id,
        report_id,
        "pages.json",
    )

    print("\nDone.")


def main_batch(reports):
    """Retrieve pages for multiple reports across workspaces.

    Args:
        reports (list[dict]): A list of dicts, each with keys
            ``workspace_id`` and ``report_id``.

    Example::

        main_batch([
            {"workspace_id": "ws-1", "report_id": "rpt-1"},
            {"workspace_id": "ws-1", "report_id": "rpt-2"},
            {"workspace_id": "ws-2", "report_id": "rpt-3"},
        ])
    """

    for idx, entry in enumerate(reports, start=1):
        workspace_id = entry["workspace_id"]
        report_id = entry["report_id"]
        print(f"\n===== [{idx}/{len(reports)}] =====")
        main(workspace_id, report_id)


if __name__ == "__main__":
    # Single report
    # main(
    #     workspace_id="YOUR_WORKSPACE_ID",
    #     report_id="YOUR_REPORT_ID",
    # )

    # Batch – pass a list of workspace/report pairs
    main_batch([
        {"workspace_id": "", "report_id": ""}
    ])
