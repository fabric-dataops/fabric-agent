# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from app import App as app


class GetWorkspacesService:
    headers = None

    def get_workspaces_as_admin(
        self, access_token, workspace_filter, expand=None, top=5000, skip=0
    ):
        """Returns a list of workspaces.

        Args:
            access_token (str): Access token to authenticate with the API.
            filter (str): Filters the results based on a boolean condition.
            expand (str): Accepts a comma-separated list of data types, which will be expanded inline in the response. Supports users, reports, dashboards, datasets, dataflows, and workbooks.
            top (int): Returns only the first n results. This parameter is mandatory and must be in the range of 1-5000.
            skip (int): Skips the first n results. Use with top to fetch results beyond the first 5000.

        Returns:
            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        # Construct the endpoint URL

        if expand:
            endpoint_url = f"{app.config.POWER_BI_API_URL}v1.0/myorg/admin/groups?$expand={expand}&$filter={workspace_filter}&$top={top}&$skip={skip}"
        else:
            endpoint_url = f"{app.config.POWER_BI_API_URL}v1.0/myorg/admin/groups?$filter={workspace_filter}&$top={top}&$skip={skip}"

        api_response = requests.get(
            endpoint_url, headers=self.headers, verify=True, timeout=300
        )

        return api_response
