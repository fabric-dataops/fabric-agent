# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from app import App as app


class GetRefreshHistoryGroupService:
    headers = None

    def get_refresh_history_in_group(self, access_token, workspace_id, dataset_id):
        """Returns the refresh history for the specified dataset from the specified workspace.

        Args:
            workspace_id (str): Id of the workspace where the dataset is stored
            dataset_id (str): dataset Id

        Returns:
            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        # Construct the endpoint URL
        endpoint_url = f"{app.config.POWER_BI_API_URL}v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/refreshes"

        api_response = requests.get(endpoint_url, headers=self.headers, verify=True)

        return api_response
