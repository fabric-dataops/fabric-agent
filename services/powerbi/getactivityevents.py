# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from app import App as app


class GetActivityEventsService:
    headers = None

    def get_activity_event(
        self, access_token, start_date_time, end_date_time, activity_type = "all"
    ):
        """Returns the initial list of audit activity events for a tenant

        Args:
            access_token (str): Access token to call API
            start_date (str): Start Date
            end_date (str): End Date

        Returns:
            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        # Construct the endpoint URL
        endpoint_url = f"{app.config.POWER_BI_API_URL}v1.0/myorg/admin/activityevents?startDateTime={start_date_time}&endDateTime={end_date_time}"
        
        if activity_type == "all":
            endpoint_url
        else:
            endpoint_url += f"&$filter=Activity eq '{activity_type}'"

        api_response = requests.get(endpoint_url, headers=self.headers, verify=True)

        return api_response

    def get_activity_event_cont(
        self, access_token, continuation_url
    ):
        """Calls the Power BI get activity events api to get the rest of activities

        Args:
            continuation_url (str): Continuation URL from the previous API call

        Returns:
            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        endpoint_url = continuation_url

        api_response = requests.get(endpoint_url, headers=self.headers, verify=True)

        return api_response