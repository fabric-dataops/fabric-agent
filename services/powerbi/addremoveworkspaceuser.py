# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from app import App as app


class WorkspacePermissionsService:
    headers = None
    body = None

    def add_user(self, access_token, workspace_id, email_address, access_level):
        """Grants user permissions to the specified workspace.
        This API call only supports adding a user, security group, M365 group and service principal.

                Args:
                    access_token (str): Access token to authenticate with the API.
                    access_level (str): The access right (permission level) that a user has on the workspace. Valid vaules are Admin, Member and Viewer etc.
                    workspace_id (str): Identifier of the workspace.
                    email_address (str): Email address of the user.

                Returns:
                    Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }
        self.body = {
            "emailAddress": email_address,
            "groupUserAccessRight": access_level,
        }

        # Construct the endpoint URL
        endpoint_url = (
            f"{app.config.POWER_BI_API_URL}v1.0/myorg/admin/groups/{workspace_id}/users"
        )

        api_response = requests.post(
            endpoint_url, headers=self.headers, json=self.body, verify=True, timeout=300
        )
        return api_response

    def add_service_principal(
        self, access_token, workspace_id, client_id, access_level
    ):
        """Grants a service principal permissions to the specified workspace.
        This API call only supports adding a user, security group, M365 group and service principal.

                Args:
                    access_token (str): Access token to authenticate with the API.
                    access_level (str): The access right (permission level) that a user has on the workspace. Valid vaules are Admin, Member and Viewer etc.
                    workspace_id (str): Identifier of the workspace.
                    client_id (str): Client Id of the principal.
                    principal_type (str): The principal type.

                Returns:
                    Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }
        self.body = {
            "identifier": client_id,
            "principalType": "App",
            "groupUserAccessRight": access_level,
        }

        # Construct the endpoint URL
        endpoint_url = (
            f"{app.config.POWER_BI_API_URL}v1.0/myorg/admin/groups/{workspace_id}/users"
        )

        api_response = requests.post(
            endpoint_url, headers=self.headers, json=self.body, verify=True, timeout=300
        )
        return api_response

    def add_group(self, access_token, workspace_id, group_id, access_level):
        """Grants a service principal permissions to the specified workspace.
        This API call only supports adding a user, security group, M365 group and service principal.

                Args:
                    access_token (str): Access token to authenticate with the API.
                    access_level (str): The access right (permission level) that a user has on the workspace. Valid vaules are Admin, Member and Viewer etc.
                    workspace_id (str): Identifier of the workspace.
                    group_id (str): Group Id from Azure Entra ID.
                    principal_type (str): The principal type.

                Returns:
                    Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }
        self.body = {
            "identifier": group_id,
            "principalType": "Group",
            "groupUserAccessRight": access_level,
        }

        # Construct the endpoint URL
        endpoint_url = (
            f"{app.config.POWER_BI_API_URL}v1.0/myorg/admin/groups/{workspace_id}/users"
        )

        api_response = requests.post(
            endpoint_url, headers=self.headers, json=self.body, verify=True, timeout=300
        )
        return api_response

    def remove_user(self, access_token, workspace_id, identifier):
        """Removes a user form a specified workspace.
        This API call only supports adding a user, security group, M365 group and service principal.

                Args:
                    access_token (str): Access token to authenticate with the API.
                    workspace_id (str): Identifier of the workspace.
                    identifier (str): Id of the principal to remove.

                Returns:
                    Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        # Using myorg instead of admin api due to error when using admin
        endpoint_url = f"{app.config.POWER_BI_API_URL}v1.0/myorg/groups/{workspace_id}/users/{identifier}"

        api_response = requests.delete(
            endpoint_url, headers=self.headers, verify=True, timeout=300
        )
        return api_response
