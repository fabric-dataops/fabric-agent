# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import requests
from app import App as app


class GetGatewaysService:
    headers = None

    def get_gateways(self, access_token):
        """Returns a list of gateways for which the user is an admin.

        Args:
            access_token (str): Access token to call API

        Returns:
            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        endpoint_url = f"{app.config.POWER_BI_API_URL}v1.0/myorg/gateways"

        api_response = requests.get(endpoint_url, headers=self.headers, verify=True)

        return api_response

    def get_gateway_datasources(self, access_token, gateway_id):
        """Returns a list of data sources from the specified gateway. The user must have gateway admin permissions.

        Args:
            access_token (str): Access token to call API
            gateway_id (str): The gateway ID. When using a gateway cluster, the gateway ID refers to the primary (first) gateway in the cluster. In such cases, gateway ID is similar to gateway cluster ID.

        Returns:
            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        endpoint_url = (
            f"{app.config.POWER_BI_API_URL}v1.0/myorg/gateways/{gateway_id}/datasources"
        )

        api_response = requests.get(endpoint_url, headers=self.headers, verify=True)

        return api_response

    def get_datasource_status(self, access_token, gateway_id, datasource_id):
        """Returns the status of a given datasource.

        Args:
            gateway_id (str): ID of the gateway.
            datasource_id (str): ID of the datasource.


        Returns:
            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        # Construct the endpoint URL
        endpoint_url = f"{app.config.POWER_BI_API_URL}v1.0/myorg//gateways/{gateway_id}/datasources/{datasource_id}/status"

        api_response = requests.get(endpoint_url, headers=self.headers, verify=True)

        return api_response

    def get_datasource_users(self, access_token, gateway_id, datasource_id):
        """Returns a list of users who have access to the specified data source.

        Args:
            gateway_id (str): ID of the gateway.
            datasource_id (str): ID of the datasource.


        Returns:
            Response: Response from the API call
        """

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        # Construct the endpoint URL
        endpoint_url = f"{app.config.POWER_BI_API_URL}v1.0/myorg//gateways/{gateway_id}/datasources/{datasource_id}/status"

        api_response = requests.get(endpoint_url, headers=self.headers, verify=True)

        return api_response
