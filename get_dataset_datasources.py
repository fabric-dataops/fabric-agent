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
    access_token = ''
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
    main(workspace_id="")
