# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from app import App as app


class GetReportPagesService:
    headers = None

    def get_pages_in_group(self, access_token, group_id, report_id):
        """Returns the pages of a specified report within a workspace (group).

        Args:
            access_token (str): Bearer token for authentication.
            group_id (str): The workspace (group) ID.
            report_id (str): The report ID.

        Returns:
            Response: Response from the API call.
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        # Construct the endpoint URL
        endpoint_url = (
            f"{app.config.POWER_BI_API_URL}v1.0/myorg/groups/{group_id}"
            f"/reports/{report_id}/pages"
        )

        api_response = requests.get(endpoint_url, headers=self.headers, verify=True)

        return api_response
