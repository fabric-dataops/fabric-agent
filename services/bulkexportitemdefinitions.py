# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from app import App as app


class BulkExportItemDefinitionsService:
    headers = None
    # Status and result calls are intentionally kept separate (not wrapped in a
    # blocking poll loop) so callers can drive polling across multiple workspaces
    # concurrently using per-operation next_check_at timestamps.

    def bulk_export_definitions(self, access_token, workspace_id):
        """Initiates a bulk export of all supported item definitions in a workspace.

        Args:
            access_token (str): Access token to call API.
            workspace_id (str): The workspace ID to export definitions from.

        Returns:
            Response: 200 (immediate result), 202 (LRO started), 429 (rate limited),
                      or other error status.
        """
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        endpoint_url = (
            f"{app.config.FABRIC_API_URL}v1/workspaces/{workspace_id}"
            f"/items/bulkExportDefinitions?beta=true"
        )

        return requests.post(
            endpoint_url,
            headers=self.headers,
            json={"mode": "All"},
            verify=True,
            timeout=180,
        )

    def get_operation_status(self, access_token, operation_id):
        """Returns the status of a long-running export operation.

        Args:
            access_token (str): Access token to call API.
            operation_id (str): The operation ID from the x-ms-operation-id response header.

        Returns:
            Response: JSON body contains {"status": "Running"|"Succeeded"|"Failed"}.
        """
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        endpoint_url = f"{app.config.FABRIC_API_URL}v1/operations/{operation_id}"

        return requests.get(endpoint_url, headers=self.headers, verify=True, timeout=180)

    def get_operation_result(self, access_token, location_url):
        """Returns the result of a completed long-running export operation.

        Args:
            access_token (str): Access token to call API.
            location_url (str): The Location header value from the 202 response.

        Returns:
            Response: JSON body is BulkExportItemDefinitionsResponse containing
                      itemDefinitionsIndex and definitionParts.
        """
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        return requests.get(
            f"{location_url}/result", headers=self.headers, verify=True, timeout=180
        )
