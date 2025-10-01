# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from app import App as app


class GetScanResultService:
    headers = None

    def get_scan_result(self, access_token: str, scan_id: str):
        """Gets the scan result for the specified scan.

        Args:
            scan_id (str): Required. The scan ID, which is included in the response from the postworkspaceinfo service.

        Returns:
            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        # Construct the endpoint URL
        endpoint_url = f"{app.config.POWER_BI_API_URL}v1.0/myorg/admin/workspaces/scanResult/{scan_id}"

        api_response = requests.get(
            endpoint_url, headers=self.headers, verify=True, timeout=180
        )
        return api_response
