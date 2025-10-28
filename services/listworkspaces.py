# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from app import App as app


class ListWorkspacesService:
    headers = None

    def list_workspaces(
        self, access_token, workspaces_type="Workspace", state="Active"
    ):
        """Returns the initial list of workspaces for a tenant

        Args:
            access_token (str): Access token to call API
            state (str): The workspace state. Supported states are Active and Deleted.
            workspace_type (str): The workspace type. Supported types are Personal, Workspace, adminworkspace.

        Returns:
            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        # Construct the endpoint URL
        endpoint_url = f"{app.config.FABRIC_API_URL}v1/admin/workspaces?type={workspaces_type}&state={state}"

        api_response = requests.get(endpoint_url, headers=self.headers, verify=True)

        return api_response

    def list_workspaces_cont(self, access_token, continuation_uri):
        """Calls the Fabric list workspaces api to get the rest of workspaces

        Args:
            continuation_uri (str): Continuation URL from the previous API call

        Returns:
            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        endpoint_url = continuation_uri

        api_response = requests.get(endpoint_url, headers=self.headers, verify=True)

        return api_response
