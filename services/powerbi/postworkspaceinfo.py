# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from app import App as app


class PostWorkspacesInfoService:
    headers = None
    body = None

    def post_workspace_info(
        self,
        access_token: str,
        workspaces: list,
        dataset_expressions: bool = True,
        dataset_schema: bool = True,
        datasource_details: bool = True,
        get_artifact_users: bool = True,
        lineage: bool = True,
    ):
        """Initiates a call to receive metadata for the requested list of workspaces.
        Call this api to initiate a metadata scan.

                        Args:
                            lineage (bool): Whether to return lineage info (upstream dataflows, tiles, data source IDs).
                            datasource_details (bool): Whether to return user details for a Power BI item (such as a report or a dashboard).
                            dataset_schema (bool): Whether to return dataset schema (tables, columns and measures).
                            dataset_expressions (bool): Whether to return dataset expressions (DAX and Mashup queries).
                            get_artifact_users (bool): Whether to return data source details
                            workspaces (list): List of workspaces to scan.


                        Returns:
                            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        self.body = {"workspaces": workspaces}

        # Construct the endpoint URL
        endpoint_url = f"{app.config.POWER_BI_API_URL}v1.0/myorg/admin/workspaces/getInfo?lineage={lineage}&datasourceDetails={datasource_details}&datasetSchema={dataset_schema}&datasetExpressions={dataset_expressions}&getArtifactUsers={get_artifact_users}"

        api_response = requests.post(
            endpoint_url, headers=self.headers, json=self.body, verify=True, timeout=180
        )
        return api_response
