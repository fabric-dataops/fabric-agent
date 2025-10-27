# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from app import App as app


class GetRefreshablesService:
    headers = None

    def get_refreshables(self, access_token, top=60):
        """Returns a list of refreshables for the organization within a capacity.
        Power BI retains a seven-day refresh history for each dataset, up to a maximum of sixty refreshes.

                Args:
                    top (str): number of results to return. Maximum 60.

                Returns:
                    Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        # Construct the endpoint URL
        endpoint_url = f"{app.config.POWER_BI_API_URL}v1.0/myorg/admin/capacities/refreshables?top={top}&$expand=capacity,group"

        api_response = requests.get(endpoint_url, headers=self.headers, verify=True)

        return api_response
