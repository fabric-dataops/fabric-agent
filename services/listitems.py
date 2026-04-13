# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from app import App as app


class ListItemsService:
    headers = None

    def list_items(self, access_token, workspace_id, item_type=None):
        """Returns the list of items in a Fabric workspace.

        Args:
            access_token (str): Access token to call API.
            workspace_id (str): The workspace ID to list items from.
            item_type (str | None): Optional item type filter (e.g. "Report",
                "SemanticModel", "Lakehouse", "Notebook"). When omitted, all
                item types are returned.

        Returns:
            Response: Response from the API call.
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        endpoint_url = f"{app.config.FABRIC_API_URL}v1/workspaces/{workspace_id}/items"
        if item_type:
            endpoint_url += f"?type={item_type}"

        api_response = requests.get(endpoint_url, headers=self.headers, verify=True)

        return api_response

    def list_items_cont(self, access_token, continuation_uri):
        """Calls the Fabric list items API to retrieve the next page of results.

        Args:
            access_token (str): Access token to call API.
            continuation_uri (str): Continuation URL from the previous API call.

        Returns:
            Response: Response from the API call.
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        api_response = requests.get(continuation_uri, headers=self.headers, verify=True)

        return api_response
