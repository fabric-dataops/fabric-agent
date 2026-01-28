import json
import logging
import logging.handlers
import time
from datetime import date
import math
import os

from app import App
from config import BaseConfig
from services.aadservice import AadService

from services.cloudlogger import get_logger

from services.powerbi.getmodifiedworkspaces import GetModifiedWorkspacesService
from services.powerbi.getscanresult import GetScanResultService
from services.powerbi.getscanstatus import GetScanStatusService
from services.powerbi.postworkspaceinfo import PostWorkspacesInfoService
from services.powerbi.getworkspacesasadmin import GetWorkspacesService


# from jsonl_service import ConvertToJsonlService

# Get today's date in YYYY-MM-DD format
current_date = date.today().strftime("%Y_%m_%d")
current_date_path = date.today().strftime("%Y-%m-%d")

# Path to save files
FILE_PATH = "data/workspaces/modified"

# Create a logger
# CloudLogger.initiate_logger()

# Get a logger
logger = get_logger(__name__)

# Initialize app object and load config
app = App.setup(BaseConfig)


# Function to get a list of modified workspace ID's
def get_modified_workspaces(
    access_token: str,
    exclude_personal_workspaces: bool = True,
    exclude_inactive_workspaces: bool = True,
    modified_since: str = None,
) -> list[str]:
    """
    This function retrieves the Id's of workspaces modified since the date provided.
    """
    modified_workspace_service = GetModifiedWorkspacesService()
    workspace_api_response = modified_workspace_service.get_modified_workspaces(
        access_token=access_token,
        modified_since=modified_since,
        exclude_personal_workspaces=exclude_personal_workspaces,
        exclude_inactive_workspaces=exclude_inactive_workspaces,
    )

    if not workspace_api_response.ok:
        logger.error(
            "Error: %s %s %s %s",
            workspace_api_response.status_code,
            workspace_api_response.reason,
            workspace_api_response.text,
            {workspace_api_response.headers.get("RequestId")},
        )
    else:
        id_count = len(workspace_api_response.json())

        logger.debug(
            "Success: %s %s %s",
            workspace_api_response.status_code,
            workspace_api_response.reason,
            {workspace_api_response.headers.get("RequestId")},
        )
        logger.info(
            "Received %s workspace IDs",
            id_count,
        )

        if id_count > 500:
            logger.warning(
                "Number of workspace IDs %s exceeds the hourly limit of 500.",
                id_count,
            )
            if id_count > 1600:
                logger.warning(
                    "Received %s workspace IDs. Scanning all of them at once will reach the maximum limit of 16 simultaneous requests",
                    id_count,
                )

        api_response = workspace_api_response.json()

        # Save response as JSON
        with open(
            f"{FILE_PATH}/workspaces_{current_date}.json",
            "w",
            encoding="utf-8",
        ) as outfile:
            # Write the JSON data to the file
            json.dump(api_response, outfile)

        # Extract ID values
        workspaces = []

        for item in api_response:
            workspaces.append(item["id"])

        return workspaces


# Get a custom list of workspaces
def list_workspaces(top=1000, skip=0, filter=None, expand=None):
    """
    This function returns a list of workspaces that matches the name provided.

    Args:
            top (int): Returns only the first n results. This parameter is mandatory and must be in the range of 1-5000.
            skip (int): Skips the first n results. Use with top to fetch results beyond the first 5000.
            expand (str): Accepts a comma-separated list of data types, which will be expanded inline in the response. Supports users, reports, dashboards, datasets, dataflows, and workbooks.
            filter(str): OData filter for filtering workspsaces
        Returns:
            Response: Response from the API call
    """

    access_token = AadService.get_access_token()

    workspace_service = GetWorkspacesService()
    workspace_api_response = workspace_service.get_workspaces_as_admin(
        access_token, filter, expand=expand, top=top, skip=skip
    )

    if not workspace_api_response.ok:
        if not workspace_api_response.reason == "Not Found":
            logger.error(
                "%s %s Request Id: %s",
                workspace_api_response.status_code,
                workspace_api_response.reason,
                workspace_api_response.headers.get("RequestId"),
            )
            logger.error("Request failed. %s", workspace_api_response.reason)

    else:
        logger.debug("Workspace info received successfully.")
        workspaces = workspace_api_response.json()["value"]

        # Extract workspace IDs
        workspaces_ids = []

        for ws in workspaces:
            workspaces_ids.append(ws["id"])

        return workspaces_ids


# Function to start a metadata scan


def request_scan(access_token: str, worksapces: list) -> dict:
    """
    This function requests a metadata scan for the workspaces IDs provided.

    Limitations
    Maximum 500 requests per hour.
    Maximum 16 simultaneous requests.
    """

    workspace_info_service = PostWorkspacesInfoService()
    workspace_info_api_response = workspace_info_service.post_workspace_info(
        access_token=access_token, workspaces=worksapces
    )

    if not workspace_info_api_response.ok:
        logger.error(
            "Error: %s %s %s %s",
            workspace_info_api_response.status_code,
            workspace_info_api_response.reason,
            workspace_info_api_response.text,
            {workspace_info_api_response.headers.get("RequestId")},
        )
        return workspace_info_api_response
    else:
        logger.debug(
            "Success: %s %s. RequestId: %s",
            workspace_info_api_response.status_code,
            workspace_info_api_response.reason,
            {workspace_info_api_response.headers.get("RequestId")},
        )
        return workspace_info_api_response


def get_scan_status(access_token, scan_id, scan_no):

    scan_status_service = GetScanStatusService()
    scan_status_api_response = scan_status_service.get_scan_status(
        access_token=access_token, scan_id=scan_id
    )

    if not scan_status_api_response.ok:
        logger.error(
            "Error getting scan status for chunk %s: %s %s %s RequestId: %s",
            scan_no,
            scan_status_api_response.status_code,
            scan_status_api_response.reason,
            scan_status_api_response.text,
            {scan_status_api_response.headers.get("RequestId")},
        )
        return scan_status_api_response

    else:
        logger.debug(
            "Scan status for chunk %s received successfully. %s %s RequestId: %s",
            scan_no,
            scan_status_api_response.status_code,
            scan_status_api_response.reason,
            {scan_status_api_response.headers.get("RequestId")},
        )
        return scan_status_api_response


def get_scan_results(access_token, scan_id, scan_no, scan_count):

    scan_result_service = GetScanResultService()
    scan_result_api_response = scan_result_service.get_scan_result(
        access_token=access_token, scan_id=scan_id
    )
    if not scan_result_api_response.ok:
        logger.error(
            "Error getting scan results for chunk %s: %s %s %s RequestId: %s",
            scan_no,
            scan_result_api_response.status_code,
            scan_result_api_response.reason,
            scan_result_api_response.text,
            {scan_result_api_response.headers.get("RequestId")},
        )
    else:
        logger.info(
            "Scan results for chunk %s/%s received successfully. %s %s RequestId: %s",
            scan_no,
            scan_count,
            scan_result_api_response.status_code,
            scan_result_api_response.reason,
            {scan_result_api_response.headers.get("RequestId")},
        )

        api_response = scan_result_api_response.json()

        datasources = api_response["datasourceInstances"]
        workspaces = api_response["workspaces"]

        file_path = f"./data/metadata_scanning/{current_date_path}/json"

        # current_file_name = f"metadata_scan_{scan_no}"

        # Save api response as JSON

        # Create the directory if it doesn't exist
        os.makedirs(file_path, exist_ok=True)

        with open(
            f"{file_path}/{scan_id}_scan_results.json",
            "w",
            encoding="utf-8",
        ) as outfile:
            # Write the JSON data to the file
            json.dump(api_response, outfile)

        # Store wrokspace metadata as JSONL
        # jsonl_service = ConvertToJsonlService()

        dest_folder_ws = f"data/metadata_scanning/{current_date_path}/workspace_metadata"
        file_name_scan = f"workspaces_scan_{scan_no}"

        # jsonl_service.save_as_jsonl(workspaces, file_name_scan, dest_folder_ws)
        # for ws in workspaces:
        #     current_file_path = f'{dest_folder_ws}/{scan_no}/{ws["id"]}'
        #     os.makedirs(os.path.dirname(current_file_path), exist_ok=True)
        #     with open(
        #         f"{current_file_path}_scan_results.jsonl",
        #         "w",
        #         encoding="utf-8",
        #     ) as jsonl_file:
        #         # Write the JSON data to the file
        #         json.dump(ws, jsonl_file)
        #         jsonl_file.write("\n")

        # logger.info(
        #     "Worksace metadata for chunk %s/%s stored successfully.",
        #     scan_no,
        #     scan_count,
        # )

        # Store model datasources as JSONL
        dest_folder_ds = f"data/metadata_scanning/{current_date_path}/datasources"
        file_name_ds = f"sm_datasources_{scan_no}"
        # jsonl_service.save_as_jsonl(datasources, file_name_ds, dest_folder_ds)
        # logger.info(
        #     "Semantic model datasources for chunk %s/%s stored successfully.",
        #     scan_no,
        #     scan_count,
        # )

        # Create the directories if they don't exist
        os.makedirs(dest_folder_ws, exist_ok=True)
        os.makedirs(dest_folder_ds, exist_ok=True)

        # Save Workspaces as JSON
        with open(
            f"{dest_folder_ws}/{file_name_scan}.json",
            "w",
            encoding="utf-8",
        ) as outfile:
            # Write the JSON data to the file
            json.dump(workspaces, outfile)

        # Save Datasources as JSON
        if datasources:
            with open(
                f"{dest_folder_ds}/{file_name_ds}.json",
                "w",
                encoding="utf-8",
            ) as outfile:
                # Write the JSON data to the file
                json.dump(datasources, outfile)


def main(modified_since: str = None):
    """
    Retrieves a list of workspaces IDs and request a metadata scan for them. Then the scan result is stored as JSON files.

    Args:
      modified_since: Last modified date of workspaces to return from (must be in ISO 8601 compliant UTC format)
    """
    # Get access token
    access_token = '' #AadService.get_access_token()

    workspaces = get_modified_workspaces(
        access_token=access_token,
        modified_since=modified_since,
        exclude_personal_workspaces=True,
    )

    # workspaces = list_workspaces(
    #     # filter="contains(name, '[Dev]') or contains(name, '[Test]')"
    # )

    # workspaces = [
    #     "295acc40-8a9d-4ffa-bc6d-d84a56b8cdd2",
    #     "8ee60a41-35eb-481d-8559-a6cfa483e6e6",
    # ]

    # Create the FILE_PATH and any necessary parent directories if they don't exist
    os.makedirs(FILE_PATH, exist_ok=True)

    scan_ids = []
    # Calculate the total number of scans/chunks

    scan_count = 0 if not workspaces else math.ceil(len(workspaces) / 50)

    for i in range(0, len(workspaces), 50):
        chunk = workspaces[i : i + 50]  # Get a chunk of 50 IDs

        # Request Scan for the current chunk of workspace IDs
        scan_response = request_scan(access_token=access_token, worksapces=chunk)

        # Handle response
        if scan_response.status_code == 202:

            scan_id = scan_response.json()["id"]
            scan_ids.append(scan_id)

            logger.info(
                "Initiated a scan for chunk %s successfully. Scan ID: %s",
                {i // 50 + 1},
                scan_id,
            )
        else:
            logger.error(
                "Failed to initiate a scan for chunk %s. /n %s %s %s",
                {i // 50 + 1},
                scan_response.status_code,
                scan_response.reason,
                scan_response.text,
            )

    for scan_id in scan_ids:
        # r = get_scan_status(access_token, scan_id)
        # d = json.loads(r.content)
        # print(d["status"])

        scan_no = scan_ids.index(scan_id) + 1

        # Loop to check operation status
        while True:
            time.sleep(5)  # seconds to wait
            response = get_scan_status(access_token, scan_id, scan_no)

            if response.status_code != 200:
                logger.error("Failed to get the scan status for scan id %s", scan_id)
                raise Exception("Failed to get operation status")

            json_operation = response.text
            operation = json.loads(json_operation)

            if operation["status"] in ["Succeeded", "Failed"]:
                logger.debug("Scan %s %s", scan_id, operation["status"])
                break

        get_scan_results(access_token, scan_id, scan_no, scan_count)


main()