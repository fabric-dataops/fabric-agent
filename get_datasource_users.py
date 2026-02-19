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
    access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6InNNMV95QXhWOEdWNHlOLUI2ajJ4em1pazVBbyIsImtpZCI6InNNMV95QXhWOEdWNHlOLUI2ajJ4em1pazVBbyJ9.eyJhdWQiOiJodHRwczovL2FuYWx5c2lzLndpbmRvd3MubmV0L3Bvd2VyYmkvYXBpIiwiaXNzIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvOTQ3Y2I1NTktYTM4MC00MTUyLTllYjUtYzdhYWY0MWIxOTRmLyIsImlhdCI6MTc3MTM5ODE5NywibmJmIjoxNzcxMzk4MTk3LCJleHAiOjE3NzE0MDI5MjgsImFjY3QiOjAsImFjciI6IjEiLCJhaW8iOiJBWFFBaS84YkFBQUFtZnRyWm5rOFMwSjF5RDRuakJKZVdXUXR4V29TM0VERURqWm9tWDZwdFFqTXUxcVh3SXhtQUd6UGpTT2E4TWpRbzZJNXlYNHVpaGZzL1NNTHlaM0ZDa1ZHM240RFNhdW9rUlFGMzAvQ1RtT0lSUzJhUElQd2RRODdWbDM3RHJlSUF2SWNpY1BJSy9lamFTSkxXNzZUQWc9PSIsImFtciI6WyJwd2QiLCJtZmEiXSwiYXBwaWQiOiIxOGZiY2ExNi0yMjI0LTQ1ZjYtODViMC1mN2JmMmIzOWIzZjMiLCJhcHBpZGFjciI6IjAiLCJmYW1pbHlfbmFtZSI6IkZlcm5hbmRvIiwiZ2l2ZW5fbmFtZSI6IkFudG9uIiwiaWR0eXAiOiJ1c2VyIiwiaXBhZGRyIjoiNDkuMC4xNC4yMDYiLCJuYW1lIjoiQW50b24gRmVybmFuZG9fU0EiLCJvaWQiOiJlM2U1MmFmOC1mZGMzLTRiNjktYjA4Zi0zNjdmZDBkYzM1NWQiLCJvbnByZW1fc2lkIjoiUy0xLTUtMjEtMTQ2MTkzMzI5LTQyNTM3MDEzNTctMjIzODgyOTcwNi02NTk1OTUiLCJwdWlkIjoiMTAwMzIwMDUwNDgwN0M0RCIsInJoIjoiMS5BVUlBV2JWOGxJQ2pVa0dldGNlcTlCc1pUd2tBQUFBQUFBQUF3QUFBQUFBQUFBQUFBQzVDQUEuIiwic2NwIjoiQXBwLlJlYWQuQWxsIENhcGFjaXR5LlJlYWQuQWxsIENhcGFjaXR5LlJlYWRXcml0ZS5BbGwgQ29ubmVjdGlvbi5SZWFkLkFsbCBDb25uZWN0aW9uLlJlYWRXcml0ZS5BbGwgQ29udGVudC5DcmVhdGUgRGFzaGJvYXJkLlJlYWQuQWxsIERhc2hib2FyZC5SZWFkV3JpdGUuQWxsIERhdGFmbG93LlJlYWQuQWxsIERhdGFmbG93LlJlYWRXcml0ZS5BbGwgRGF0YXNldC5SZWFkLkFsbCBEYXRhc2V0LlJlYWRXcml0ZS5BbGwgR2F0ZXdheS5SZWFkLkFsbCBHYXRld2F5LlJlYWRXcml0ZS5BbGwgSXRlbS5FeGVjdXRlLkFsbCBJdGVtLkV4dGVybmFsRGF0YVNoYXJlLkFsbCBJdGVtLlJlYWRXcml0ZS5BbGwgSXRlbS5SZXNoYXJlLkFsbCBPbmVMYWtlLlJlYWQuQWxsIE9uZUxha2UuUmVhZFdyaXRlLkFsbCBQaXBlbGluZS5EZXBsb3kgUGlwZWxpbmUuUmVhZC5BbGwgUGlwZWxpbmUuUmVhZFdyaXRlLkFsbCBSZXBvcnQuUmVhZFdyaXRlLkFsbCBSZXBydC5SZWFkLkFsbCBTdG9yYWdlQWNjb3VudC5SZWFkLkFsbCBTdG9yYWdlQWNjb3VudC5SZWFkV3JpdGUuQWxsIFRhZy5SZWFkLkFsbCBUZW5hbnQuUmVhZC5BbGwgVGVuYW50LlJlYWRXcml0ZS5BbGwgVXNlclN0YXRlLlJlYWRXcml0ZS5BbGwgV29ya3NwYWNlLkdpdENvbW1pdC5BbGwgV29ya3NwYWNlLkdpdFVwZGF0ZS5BbGwgV29ya3NwYWNlLlJlYWQuQWxsIFdvcmtzcGFjZS5SZWFkV3JpdGUuQWxsIiwic2lkIjoiMDAyMTRiOGEtYWNlOC0wZTU0LTgzYmQtN2E3NWYxNjllNWNkIiwic2lnbmluX3N0YXRlIjpbImlua25vd25udHdrIl0sInN1YiI6IlVoZXFiYTRaQ29uLXZfTlc4OWZ5aVpfT2kyUldjNW5SUjhmR1ZXRGhfWjAiLCJ0aWQiOiI5NDdjYjU1OS1hMzgwLTQxNTItOWViNS1jN2FhZjQxYjE5NGYiLCJ1bmlxdWVfbmFtZSI6ImFudG9uZmVybmFuZG8xX3NhQG5ibmNvLmNvbS5hdSIsInVwbiI6ImFudG9uZmVybmFuZG8xX3NhQG5ibmNvLmNvbS5hdSIsInV0aSI6Im41X3doMERxUzB1em1rNTJjRjhSQUEiLCJ2ZXIiOiIxLjAiLCJ3aWRzIjpbImI3OWZiZjRkLTNlZjktNDY4OS04MTQzLTc2YjE5NGU4NTUwOSJdLCJ4bXNfYWN0X2ZjdCI6IjUgMyIsInhtc19mdGQiOiJIYTA2VHE0aXR3NnNEb1hnREczNVhoei1oRHgtY21EeGo4Y09ZbmZGeFhJQllYVnpkSEpoYkdsaFl5MWtjMjF6IiwieG1zX2lkcmVsIjoiMSA4IiwieG1zX3N1Yl9mY3QiOiIzIDgifQ.HEi18zaLFBq1TQM6JDPgFXH58k859qqEJJ7dcrUXoNPTmHhlP5TFkqRYnM7s1vjFv-TkTrFMzwyjhGXBRANxEDnDGvI4v0UlTRrRalbGUxwrjzEWytqAQl23MxTrEZfEE85LE1k4BMGQ7ezxOR4P0e5aYLSvaxlZpSA2E4cqSKJQ0zrXol08AxwAaa2nohmBO3IE5bSKqcvD4yuHswd1yqWmtcW9PvV4dgDfUpiVOlL92nT4fyIzmRz6BKLdRLx0TSm6iG1BLk5xl78dt59AYiWM3SWzXtP5OHiyofdNNSozOvp__K4vdAodjZpR9kNXHKX9yAQKab_Lnb_uEa_w2Q'

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


