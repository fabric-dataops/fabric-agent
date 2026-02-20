import json
import os
import re
from datetime import date

from app import App
from config import BaseConfig
from services.aadservice import AadService
from services.powerbi.getgateways import GetGatewaysService

# Initialize App configuration for standalone execution
App.setup(BaseConfig)

# Get today's date in YYYY-MM-DD format
current_date = date.today().strftime("%Y-%m-%d")

# Folder path for saving datasource user data
output_path = "./data/datasource_users/"


def save_output(path, data, gateway_id, filename):
    """Save JSON data to a file organised by date and gateway.

    Args:
        path (str): Base output directory.
        data (dict | list): JSON-serialisable data to write.
        gateway_id (str): The gateway ID used as a sub-folder.
        filename (str): Name of the output file.
    """

    folder_path = os.path.join(path, current_date, gateway_id)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Sanitise filename by replacing characters invalid in file paths
    safe_filename = re.sub(r'[\\/:*?"<>|]', '_', filename)

    file_path = os.path.join(folder_path, safe_filename)
    with open(file_path, "w", encoding="utf-8") as outfile:
        json.dump(data, outfile, indent=2)

    print(f"Saved: {file_path}")


def main():
    """Retrieve users for every datasource across all gateways via the Power BI REST API."""

    # Obtain an access token
    # access_token = AadService.get_access_token()
    access_token = ''

    gateway_service = GetGatewaysService()

    # ----- Step 1: Get all gateways -----
    gateways_response = gateway_service.get_gateways(access_token)

    if not gateways_response.ok:
        print(
            f"Error fetching gateways: {gateways_response.status_code} "
            f"{gateways_response.reason}"
        )
        print(gateways_response.content)
        return

    gateways_data = gateways_response.json()
    gateways = gateways_data.get("value", [])

    print(f"Found {len(gateways)} gateway(s)")

    # ----- Step 2: For each gateway, get its datasources -----
    for gateway in gateways:
        gateway_id = gateway.get("id")
        gateway_name = gateway.get("name", "unknown")

        print(f"\nProcessing gateway: {gateway_name} ({gateway_id})")

        datasources_response = gateway_service.get_gateway_datasources(
            access_token, gateway_id
        )

        if not datasources_response.ok:
            print(
                f"  Error fetching datasources for gateway {gateway_id}: "
                f"{datasources_response.status_code} {datasources_response.reason}"
            )
            continue

        datasources_data = datasources_response.json()
        datasources = datasources_data.get("value", [])

        print(f"  Found {len(datasources)} datasource(s)")

        # ----- Step 3: For each datasource, get its users -----
        for datasource in datasources:
            datasource_id = datasource.get("id")
            datasource_name = datasource.get("datasourceName", datasource_id)

            print(f"    Fetching users for datasource: {datasource_name} ({datasource_id})")

            users_response = gateway_service.get_datasource_users(
                access_token, gateway_id, datasource_id
            )

            if not users_response.ok:
                print(
                    f"      Error fetching users for datasource {datasource_id}: "
                    f"{users_response.status_code} {users_response.reason}"
                )
                continue

            users_data = users_response.json()
            users = users_data.get("value", [])

            # Inject datasource id and name into each user record
            for user in users:
                user["datasourceId"] = datasource_id
                user["datasourceName"] = datasource_name

            print(f"      Found {len(users)} user(s)")

            # Save users for this datasource
            save_output(
                output_path,
                users,
                gateway_id,
                f"{datasource_id}_users.json",
            )

    print("\nDone.")


if __name__ == "__main__":
    main()


