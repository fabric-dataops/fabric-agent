# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from app import App as app


class GetModifiedWorkspacesService:
    headers = None

    def get_modified_workspaces(
        self,
        access_token: str,
        modified_since: str = None,
        exclude_personal_workspaces: bool = True,
        exclude_inactive_workspaces: bool = True,
    ):
        """Gets a list of workspace IDs in the organization.

        If the optional modifiedSince parameter is set to a date-time, only the IDs of workspaces that changed after that date-time are returned.
        If the modifiedSince parameter isn't used, the IDs of all workspaces in the organization are returned.
        The date-time specified by the modifiedSince parameter must be in the range of 30 minutes (to allow workspace changes to take effect) to 30 days prior to the current time.

                        Args:
                            exclude_inactive_workspaces (bool): Whether to exclude inactive workspaces.
                            exclude_personal_workspaces (bool): Whether to exclude personal workspaces
                            modified_since (str): Last modified date (must be in ISO 8601 compliant UTC format) ie: 2020-10-02T05:51:30.0000000Z

                        Returns:
                            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        # Construct the endpoint URL
        endpoint_url = f"{app.config.POWER_BI_API_URL}v1.0/myorg/admin/workspaces/modified?excludePersonalWorkspaces={exclude_personal_workspaces}&excludeInActiveWorkspaces={exclude_inactive_workspaces}"

        if modified_since is not None:
            endpoint_url += f"&modifiedSince={modified_since}"

        api_response = requests.get(
            endpoint_url, headers=self.headers, verify=True, timeout=180
        )
        return api_response
