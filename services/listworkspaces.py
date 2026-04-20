# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from microsoft_fabric_api import FabricClient


class ListWorkspacesService:

    def __init__(self, client: FabricClient):
        self._client = client

    def list_workspaces(self, type="Workspace", state="Active"):
        """Returns all workspaces for a tenant as an iterable of Workspace objects.

        Args:
            type (str): Workspace type filter. Default "Workspace".
            state (str): Workspace state filter. Default "Active".

        Returns:
            Iterable[Workspace]: SDK workspace model objects. Pagination is handled
                automatically by the SDK.
        """
        return self._client.admin.workspaces.list_workspaces(type=type, state=state)
