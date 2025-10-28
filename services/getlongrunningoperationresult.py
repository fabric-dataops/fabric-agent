# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import json
import time

import requests

from app import App as app


class GetLongRunningOperationResultService:
    headers = None
    body = None

    def get_long_running_operation_result(
        self, access_token, location_url, operation_id, retry_after
    ):
        """Returns a list of the tenant settings.

        Args:
            None

        Returns:
            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        # Construct the endpoint URLs
        status_endpoint_url = f"{app.config.FABRIC_API_URL}v1/operations/{operation_id}"
        result_endpoint_url = f"{location_url}/result"

        # Loop to check operation status
        while True:
            time.sleep(
                retry_after
            )  # Sleep for the duration specified by Retry-After header
            response = requests.get(
                status_endpoint_url, headers=self.headers, verify=False, timeout=180
            )

            if response.status_code != 200:
                raise Exception("Failed to get operation status")

            json_operation = response.text
            operation = json.loads(json_operation)

            if operation["status"] in ["Succeeded", "Failed"]:
                break

        result_api_response = requests.get(
            result_endpoint_url, headers=self.headers, verify=False, timeout=180
        )

        return result_api_response
