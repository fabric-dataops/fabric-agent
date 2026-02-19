import json
import os
from datetime import date

from app import App
from config import BaseConfig
from services.aadservice import AadService
from services.powerbi.getgateways import GetGatewaysService

# Initialize App configuration for standalone execution
App.setup(BaseConfig)

# Get today's date in YYYY-MM-DD format
current_date = date.today().strftime("%Y-%m-%d")

# Folder path for saving gateway datasource data
output_path = "./data/gateway_datasources/"


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

    file_path = os.path.join(folder_path, filename)
    with open(file_path, "w", encoding="utf-8") as outfile:
        json.dump(data, outfile, indent=2)

    print(f"Saved: {file_path}")


def main():
    """Retrieve all gateways and their datasources via the Power BI REST API."""

    # Obtain an access token
    # access_token = AadService.get_access_token()
    access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6InNNMV95QXhWOEdWNHlOLUI2ajJ4em1pazVBbyIsImtpZCI6InNNMV95QXhWOEdWNHlOLUI2ajJ4em1pazVBbyJ9.eyJhdWQiOiJodHRwczovL2FuYWx5c2lzLndpbmRvd3MubmV0L3Bvd2VyYmkvYXBpIiwiaXNzIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvOTQ3Y2I1NTktYTM4MC00MTUyLTllYjUtYzdhYWY0MWIxOTRmLyIsImlhdCI6MTc3MTM4Nzc5MCwibmJmIjoxNzcxMzg3NzkwLCJleHAiOjE3NzEzOTMwNjQsImFjY3QiOjAsImFjciI6IjEiLCJhaW8iOiJBWFFBaS84YkFBQUFIalFQZkptNlNUNm1hLzAyWFRBR1JGaFVCektTZ3lSR2ROakVjbnNtWDdNZXVzNE8zeFBBeW02MnlxbVo0SDNhMVRCOFRxditvalMra2gxb2o2c1JhbzJLMVlaN1pwMVZYdWM2OW44WkV6S3NGUlRhMS9INkRDN2NCN1Q2S3lHS09TOWswa0VMK2RVTjZudkQ5MWFIV3c9PSIsImFtciI6WyJwd2QiLCJtZmEiXSwiYXBwaWQiOiIxOGZiY2ExNi0yMjI0LTQ1ZjYtODViMC1mN2JmMmIzOWIzZjMiLCJhcHBpZGFjciI6IjAiLCJmYW1pbHlfbmFtZSI6IkZlcm5hbmRvIiwiZ2l2ZW5fbmFtZSI6IkFudG9uIiwiaWR0eXAiOiJ1c2VyIiwiaXBhZGRyIjoiNDkuMC4xNC4yMTYiLCJuYW1lIjoiQW50b24gRmVybmFuZG9fU0EiLCJvaWQiOiJlM2U1MmFmOC1mZGMzLTRiNjktYjA4Zi0zNjdmZDBkYzM1NWQiLCJvbnByZW1fc2lkIjoiUy0xLTUtMjEtMTQ2MTkzMzI5LTQyNTM3MDEzNTctMjIzODgyOTcwNi02NTk1OTUiLCJwdWlkIjoiMTAwMzIwMDUwNDgwN0M0RCIsInJoIjoiMS5BVUlBV2JWOGxJQ2pVa0dldGNlcTlCc1pUd2tBQUFBQUFBQUF3QUFBQUFBQUFBQUFBQzVDQUEuIiwic2NwIjoiQXBwLlJlYWQuQWxsIENhcGFjaXR5LlJlYWQuQWxsIENhcGFjaXR5LlJlYWRXcml0ZS5BbGwgQ29ubmVjdGlvbi5SZWFkLkFsbCBDb25uZWN0aW9uLlJlYWRXcml0ZS5BbGwgQ29udGVudC5DcmVhdGUgRGFzaGJvYXJkLlJlYWQuQWxsIERhc2hib2FyZC5SZWFkV3JpdGUuQWxsIERhdGFmbG93LlJlYWQuQWxsIERhdGFmbG93LlJlYWRXcml0ZS5BbGwgRGF0YXNldC5SZWFkLkFsbCBEYXRhc2V0LlJlYWRXcml0ZS5BbGwgR2F0ZXdheS5SZWFkLkFsbCBHYXRld2F5LlJlYWRXcml0ZS5BbGwgSXRlbS5FeGVjdXRlLkFsbCBJdGVtLkV4dGVybmFsRGF0YVNoYXJlLkFsbCBJdGVtLlJlYWRXcml0ZS5BbGwgSXRlbS5SZXNoYXJlLkFsbCBPbmVMYWtlLlJlYWQuQWxsIE9uZUxha2UuUmVhZFdyaXRlLkFsbCBQaXBlbGluZS5EZXBsb3kgUGlwZWxpbmUuUmVhZC5BbGwgUGlwZWxpbmUuUmVhZFdyaXRlLkFsbCBSZXBvcnQuUmVhZFdyaXRlLkFsbCBSZXBydC5SZWFkLkFsbCBTdG9yYWdlQWNjb3VudC5SZWFkLkFsbCBTdG9yYWdlQWNjb3VudC5SZWFkV3JpdGUuQWxsIFRhZy5SZWFkLkFsbCBUZW5hbnQuUmVhZC5BbGwgVGVuYW50LlJlYWRXcml0ZS5BbGwgVXNlclN0YXRlLlJlYWRXcml0ZS5BbGwgV29ya3NwYWNlLkdpdENvbW1pdC5BbGwgV29ya3NwYWNlLkdpdFVwZGF0ZS5BbGwgV29ya3NwYWNlLlJlYWQuQWxsIFdvcmtzcGFjZS5SZWFkV3JpdGUuQWxsIiwic2lkIjoiMDAyMTRiOGEtYWNlOC0wZTU0LTgzYmQtN2E3NWYxNjllNWNkIiwic2lnbmluX3N0YXRlIjpbImlua25vd25udHdrIl0sInN1YiI6IlVoZXFiYTRaQ29uLXZfTlc4OWZ5aVpfT2kyUldjNW5SUjhmR1ZXRGhfWjAiLCJ0aWQiOiI5NDdjYjU1OS1hMzgwLTQxNTItOWViNS1jN2FhZjQxYjE5NGYiLCJ1bmlxdWVfbmFtZSI6ImFudG9uZmVybmFuZG8xX3NhQG5ibmNvLmNvbS5hdSIsInVwbiI6ImFudG9uZmVybmFuZG8xX3NhQG5ibmNvLmNvbS5hdSIsInV0aSI6IkVLU21LcWI4WjBDZm92SUV0ck1qQUEiLCJ2ZXIiOiIxLjAiLCJ3aWRzIjpbImI3OWZiZjRkLTNlZjktNDY4OS04MTQzLTc2YjE5NGU4NTUwOSJdLCJ4bXNfYWN0X2ZjdCI6IjUgMyIsInhtc19mdGQiOiJyZWFnMlpVLVg0UkFDcWhwQlQ5M211TW13c3hrdlBTcjJ4MDVhYWFVSTFJQllYVnpkSEpoYkdsaGMyOTFkR2hsWVhOMExXUnpiWE0iLCJ4bXNfaWRyZWwiOiIxIDI4IiwieG1zX3N1Yl9mY3QiOiIzIDIifQ.dovpfsiltGcSqTbTqUoJdJ6VRmTaZs2sjqb4Y-anihem39YUnmZb0KDBhjCRwVhXeT10CkYkKUrjp4bciBCNVleqt_MZUUOiILtovXWxj0aXfnh7EOXQ81eV9ZCJ7A7c4s3p4dYGQeCTHpchyrKl8Pa11WPIjpDcGG4sdaATKsIFoC0Wxd_t0u_9lMT7NRarfGQnpM9FQKZR6tK7zq_AdfqzDzz9VIYuVVQSoyYZBurzCwcY5R0vT1wR0qF8uBunJpWbnRrFi57Qkngf1JSwMIL_f_mzh8PWhwbrDswLy_0p4BWEjHo17J4M7bSGz4Pckj-3jAJKbM1jWkvNc5XgzQ'

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

    # Save the full gateways response
    folder_path = os.path.join(output_path, current_date)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    with open(
        os.path.join(folder_path, "gateways.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(gateways, f, indent=2)

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

        # Save datasources for this gateway
        save_output(
            output_path,
            datasources,
            gateway_id,
            f"{gateway_name}_datasources.json",
        )

    print("\nDone.")


if __name__ == "__main__":
    main()
