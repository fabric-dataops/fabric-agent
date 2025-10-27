# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from app import App as app


class GetDataflowsService:
    headers = None

    def get_dataflows(self, access_token):
        """Returns a list of dataflows of the tenant.

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
        endpoint_url = f"{app.config.POWER_BI_API_URL}v1.0/myorg/admin/dataflows"

        api_response = requests.get(endpoint_url, headers=self.headers, verify=True)

        return api_response
