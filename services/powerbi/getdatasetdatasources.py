# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from app import App as app


class GetDatasetDatasourcesService:
    headers = None

    def get_datasources(self, access_token, dataset_id):
        """Returns the datasources of a specified dataset.

        Args:
            dataset_id (str): dataset Id

        Returns:
            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        # Construct the endpoint URL
        endpoint_url = f"{app.config.POWER_BI_API_URL}v1.0/myorg/admin/datasets/{dataset_id}/datasources"

        api_response = requests.get(endpoint_url, headers=self.headers, verify=True)

        return api_response
