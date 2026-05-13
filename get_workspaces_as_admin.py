import json
import os
import time
from datetime import date
from dotenv import load_dotenv

from app import App
from config import BaseConfig
from services.aadservice import AadService
from services.cloudlogger import get_logger
from services.powerbi.getworkspacesasadmin import GetWorkspacesService

App.setup(BaseConfig)

logger = get_logger(__name__)

current_date = date.today().strftime("%Y-%m-%d")
OUTPUT_BASE = "./data/workspaces/admin"
PAGE_SIZE = 5000


def fetch_all_workspaces(access_token, workspace_filter="", expand=None):
    """Page through admin/groups until all workspaces are retrieved.

    Args:
        access_token (str): AAD access token.
        workspace_filter (str): Optional OData $filter expression.
        expand (str | None): Optional comma-separated $expand list
            (users, reports, dashboards, datasets, dataflows, workbooks).

    Returns:
        list[dict]: All workspaces returned by the API.
    """
    svc = GetWorkspacesService()
    all_workspaces = []
    skip = 0

    while True:
        logger.debug("Fetching workspaces: skip=%s top=%s", skip, PAGE_SIZE)
        response = svc.get_workspaces_as_admin(
            access_token,
            workspace_filter,
            expand=expand,
            top=PAGE_SIZE,
            skip=skip,
        )

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 10))
            logger.warning("Rate limited, retrying in %ss", retry_after)
            time.sleep(retry_after)
            continue

        if not response.ok:
            logger.error(
                "%s %s %s RequestId: %s",
                response.status_code,
                response.reason,
                response.text,
                response.headers.get("RequestId"),
            )
            break

        page = response.json().get("value", [])
        all_workspaces.extend(page)
        logger.info("Received %s workspace(s) (total: %s)", len(page), len(all_workspaces))

        if len(page) < PAGE_SIZE:
            break

        skip += PAGE_SIZE

    return all_workspaces


def save_workspaces(workspaces):
    """Write the workspace list as JSON under data/workspaces/admin/{date}/.

    Args:
        workspaces (list[dict]): Workspace dicts returned by the admin API.

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


def main(workspace_filter="", expand=None):
    """Fetch all workspaces via the Power BI admin API and save to disk.

    Args:
        workspace_filter (str): Optional OData $filter expression
            (e.g. "type eq 'Workspace'" or "contains(name, '[Dev]')").
        expand (str | None): Optional comma-separated $expand list.
    """
    access_token = AadService.get_access_token()
    # load_dotenv()
    # access_token = os.getenv('ACCESS_TOKEN')

    workspaces = fetch_all_workspaces(
        access_token, workspace_filter=workspace_filter, expand=expand
    )
    if not workspaces:
        logger.warning("No workspaces returned.")
        return

    save_workspaces(workspaces)
    logger.info("Done.")


if __name__ == "__main__":
    # Pass a filter / expand to scope the result, or leave as defaults for all workspaces.
    main(workspace_filter="", expand=None)
