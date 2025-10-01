# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from app import App as app


class SemanticModelService:
    headers = None
    body = None

    def get_semantic_models(self, access_token):
        """Returns a list of semantic models of the tenant.

        Args:
            None

        Returns:
            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        # Construct the endpoint URL
        endpoint_url = f"{app.config.POWER_BI_API_URL}v1.0/myorg/admin/datasets"

        api_response = requests.get(endpoint_url, headers=self.headers, verify=True)

        return api_response

    def refresh_semantic_model(
        self,
        access_token: str,
        model_id: str,
        workspace_id: str,
        max_parallelism: int,
        commit_mode: str,
        refresh_type: str,
    ):
        """Initiates a refresh for a given dataset.

        Args:
        access_token: Access token
        model_id: Semantic model Id
        workspace_id: Workspace Id
        max_parallelism: The maximum number of threads on which to run parallel processing commands.
        commit_mode: Determines if objects will be committed in batches or only when complete. Accepted values: partialBatch or transactional.
        refresh_type: The type of processing to perform. Accepted values: Automatic, Calculate, ClearValues, DataOnly, Defragment, Full.

        Returns:
            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        self.body = {
            "maxParallelism": max_parallelism,
            "commitMode": commit_mode,
            "type": refresh_type,
        }

        # Construct the endpoint URL
        endpoint_url = f"{app.config.POWER_BI_API_URL}v1.0/myorg/groups/{workspace_id}/datasets/{model_id}/refreshes"

        api_response = requests.post(
            endpoint_url, headers=self.headers, json=self.body, verify=True, timeout=180
        )

        return api_response
