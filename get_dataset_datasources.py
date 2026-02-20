import json
import os
from datetime import date

from app import App
from config import BaseConfig
from services.aadservice import AadService
from services.powerbi.getdatasetdatasources import GetDatasetDatasourcesService
from services.powerbi.semanticmodels import SemanticModelService

# Initialize App configuration for standalone execution
App.setup(BaseConfig)

# Get today's date in YYYY-MM-DD format
current_date = date.today().strftime("%Y-%m-%d")

# Folder path for saving dataset datasource data
output_path = "./data/dataset_datasources/"


def save_output(path, data, dataset_id, filename):
    """Save JSON data to a file organised by date and dataset.

    Args:
        path (str): Base output directory.
        data (dict | list): JSON-serialisable data to write.
        dataset_id (str): The dataset ID used as a sub-folder.
        filename (str): Name of the output file.
    """

    folder_path = os.path.join(path, current_date, dataset_id)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path, filename)
    with open(file_path, "w", encoding="utf-8") as outfile:
        json.dump(data, outfile, indent=2)

    print(f"Saved: {file_path}")


def main(workspace_id=None):
    """Retrieve datasets and their datasources via the Power BI REST API.

    Args:
        workspace_id (str | None): Optional workspace (group) ID. When provided,
            only datasets in that workspace are returned. When omitted, all
            datasets across the tenant are returned via the Admin API.
    """

    # Obtain an access token
    # access_token = AadService.get_access_token()
    access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6InNNMV95QXhWOEdWNHlOLUI2ajJ4em1pazVBbyIsImtpZCI6InNNMV95QXhWOEdWNHlOLUI2ajJ4em1pazVBbyJ9.eyJhdWQiOiJodHRwczovL2FuYWx5c2lzLndpbmRvd3MubmV0L3Bvd2VyYmkvYXBpIiwiaXNzIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvOTQ3Y2I1NTktYTM4MC00MTUyLTllYjUtYzdhYWY0MWIxOTRmLyIsImlhdCI6MTc3MTQ3NjA5OSwibmJmIjoxNzcxNDc2MDk5LCJleHAiOjE3NzE0ODA0NzUsImFjY3QiOjAsImFjciI6IjEiLCJhaW8iOiJBWFFBaS84YkFBQUErN3c3ait5LzFHMzNxWjk1eE0vOEVJYWlWS0FoS28rMDdXa3BtbzY0M0tFdDEvb0NqTlREM3lkYWxuaXRiL2xzOUg0M25NbWk2ekIwSlltbEN2Si9QdlZWTzZUL0d0WnZKa3RpUVN3NmF0WjFPT25wbzgvdUh2RVJHN0VuUFpNRTBtcktmbEhNalBkVVZGMml6M3VCRFE9PSIsImFtciI6WyJwd2QiLCJtZmEiXSwiYXBwaWQiOiIxOGZiY2ExNi0yMjI0LTQ1ZjYtODViMC1mN2JmMmIzOWIzZjMiLCJhcHBpZGFjciI6IjAiLCJmYW1pbHlfbmFtZSI6IkZlcm5hbmRvIiwiZ2l2ZW5fbmFtZSI6IkFudG9uIiwiaWR0eXAiOiJ1c2VyIiwiaXBhZGRyIjoiNDkuMC4xNC4yMDYiLCJuYW1lIjoiQW50b24gRmVybmFuZG9fU0EiLCJvaWQiOiJlM2U1MmFmOC1mZGMzLTRiNjktYjA4Zi0zNjdmZDBkYzM1NWQiLCJvbnByZW1fc2lkIjoiUy0xLTUtMjEtMTQ2MTkzMzI5LTQyNTM3MDEzNTctMjIzODgyOTcwNi02NTk1OTUiLCJwdWlkIjoiMTAwMzIwMDUwNDgwN0M0RCIsInJoIjoiMS5BVUlBV2JWOGxJQ2pVa0dldGNlcTlCc1pUd2tBQUFBQUFBQUF3QUFBQUFBQUFBQUFBQzVDQUEuIiwic2NwIjoiQXBwLlJlYWQuQWxsIENhcGFjaXR5LlJlYWQuQWxsIENhcGFjaXR5LlJlYWRXcml0ZS5BbGwgQ29ubmVjdGlvbi5SZWFkLkFsbCBDb25uZWN0aW9uLlJlYWRXcml0ZS5BbGwgQ29udGVudC5DcmVhdGUgRGFzaGJvYXJkLlJlYWQuQWxsIERhc2hib2FyZC5SZWFkV3JpdGUuQWxsIERhdGFmbG93LlJlYWQuQWxsIERhdGFmbG93LlJlYWRXcml0ZS5BbGwgRGF0YXNldC5SZWFkLkFsbCBEYXRhc2V0LlJlYWRXcml0ZS5BbGwgR2F0ZXdheS5SZWFkLkFsbCBHYXRld2F5LlJlYWRXcml0ZS5BbGwgSXRlbS5FeGVjdXRlLkFsbCBJdGVtLkV4dGVybmFsRGF0YVNoYXJlLkFsbCBJdGVtLlJlYWRXcml0ZS5BbGwgSXRlbS5SZXNoYXJlLkFsbCBPbmVMYWtlLlJlYWQuQWxsIE9uZUxha2UuUmVhZFdyaXRlLkFsbCBQaXBlbGluZS5EZXBsb3kgUGlwZWxpbmUuUmVhZC5BbGwgUGlwZWxpbmUuUmVhZFdyaXRlLkFsbCBSZXBvcnQuUmVhZFdyaXRlLkFsbCBSZXBydC5SZWFkLkFsbCBTdG9yYWdlQWNjb3VudC5SZWFkLkFsbCBTdG9yYWdlQWNjb3VudC5SZWFkV3JpdGUuQWxsIFRhZy5SZWFkLkFsbCBUZW5hbnQuUmVhZC5BbGwgVGVuYW50LlJlYWRXcml0ZS5BbGwgVXNlclN0YXRlLlJlYWRXcml0ZS5BbGwgV29ya3NwYWNlLkdpdENvbW1pdC5BbGwgV29ya3NwYWNlLkdpdFVwZGF0ZS5BbGwgV29ya3NwYWNlLlJlYWQuQWxsIFdvcmtzcGFjZS5SZWFkV3JpdGUuQWxsIiwic2lkIjoiMDAyMTcyOWEtM2VjYS1lY2E5LWY3Y2ItOTIzYzhlMmZlNmQzIiwic2lnbmluX3N0YXRlIjpbImlua25vd25udHdrIl0sInN1YiI6IlVoZXFiYTRaQ29uLXZfTlc4OWZ5aVpfT2kyUldjNW5SUjhmR1ZXRGhfWjAiLCJ0aWQiOiI5NDdjYjU1OS1hMzgwLTQxNTItOWViNS1jN2FhZjQxYjE5NGYiLCJ1bmlxdWVfbmFtZSI6ImFudG9uZmVybmFuZG8xX3NhQG5ibmNvLmNvbS5hdSIsInVwbiI6ImFudG9uZmVybmFuZG8xX3NhQG5ibmNvLmNvbS5hdSIsInV0aSI6InlydE5VeU8zV1VhVTVQY2Y2azR3QUEiLCJ2ZXIiOiIxLjAiLCJ3aWRzIjpbImE5ZWE4OTk2LTEyMmYtNGM3NC05NTIwLThlZGNkMTkyODI2YyIsImI3OWZiZjRkLTNlZjktNDY4OS04MTQzLTc2YjE5NGU4NTUwOSJdLCJ4bXNfYWN0X2ZjdCI6IjUgMyIsInhtc19mdGQiOiI3aUR1Z2c0TlJ1anJJOWFTX0dQQ0RTdllZT3E1V1BPWkZaTWRNTDVSUDNJQllYVnpkSEpoYkdsaFpXRnpkQzFrYzIxeiIsInhtc19pZHJlbCI6IjYgMSIsInhtc19zdWJfZmN0IjoiMyAxMiJ9.Hq2fOQALFeDiz7brGDAoqQkrAHtCApoXJBxG6HbagE0-IO8FmkzyLv-7Lmmdh9zpHOi2V9G0gSr91UdLRT8uHhatFL3ryDAMWYFsS-xGr30zgrpvFJfDxuRHz61i0QnV_r0J2lWSFcbAwB1qW2I0lZT5NLviydLbHbUZNfygpZKIx3pkczx39uJuhK8CX8JN0HyCeDkW0XAExLdDSW0OnRcLdV1VqWqwc7XDQx0mbcVXuMjg_q0yCMYUEM1SBKsHGM_7XbmAWL1CAahGLJyQt76BqbGM2NfyTwhmNKEi318PhCU74FmVKq-tv083onDKy0lNOYJmEdpXqUjXYj3XRg'
    semantic_model_service = SemanticModelService()
    dataset_datasources_service = GetDatasetDatasourcesService()

    # ----- Step 1: Get datasets -----
    if workspace_id:
        print(f"Fetching datasets for workspace: {workspace_id}")
        datasets_response = semantic_model_service.get_semantic_models_in_group(
            access_token, workspace_id
        )
    else:
        print("Fetching all datasets (Admin API)")
        datasets_response = semantic_model_service.get_semantic_models(access_token)

    if not datasets_response.ok:
        print(
            f"Error fetching datasets: {datasets_response.status_code} "
            f"{datasets_response.reason}"
        )
        print(datasets_response.content)
        return

    datasets_data = datasets_response.json()
    datasets = datasets_data.get("value", [])

    print(f"Found {len(datasets)} dataset(s)")

    # Save the full datasets response
    folder_path = os.path.join(output_path, current_date)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    with open(
        os.path.join(folder_path, "datasets.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(datasets, f, indent=2)

    # ----- Step 2: For each dataset, get its datasources -----
    for dataset in datasets:
        dataset_id = dataset.get("id")
        dataset_name = dataset.get("name", "unknown")

        print(f"\nProcessing dataset: {dataset_name} ({dataset_id})")

        datasources_response = dataset_datasources_service.get_datasources(
            access_token, dataset_id
        )

        if not datasources_response.ok:
            print(
                f"  Error fetching datasources for dataset {dataset_id}: "
                f"{datasources_response.status_code} {datasources_response.reason}"
            )
            continue

        datasources_data = datasources_response.json()
        datasources = datasources_data.get("value", [])

        # Inject the semantic model (dataset) ID into each datasource record
        for datasource in datasources:
            datasource["datasetId"] = dataset_id

        print(f"  Found {len(datasources)} datasource(s)")

        # Save datasources for this dataset
        save_output(
            output_path,
            datasources,
            workspace_id if workspace_id else "all_workspaces",
            f"{dataset_id}_datasources.json",
        )

    print("\nDone.")


if __name__ == "__main__":
    # Pass a workspace ID to scope the request, or leave as None for all datasets
    workspace_id = None
    main(workspace_id="85360A12-4CC4-4776-8635-57CB9AB80955")
