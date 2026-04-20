# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from microsoft_fabric_api import FabricClient


class ListItemsService:

    def __init__(self, client: FabricClient):
        self._client = client

    def list_items(self, workspace_id: str, item_type: str = None):
        """Returns all items in a workspace as an iterable of Item objects.

        Args:
            workspace_id (str): The workspace ID to list items from.
            item_type (str | None): Optional item type filter (e.g. "Report",
                "SemanticModel", "Lakehouse", "Notebook"). None returns all types.

        Returns:
            Iterable[Item]: SDK item model objects. Pagination is handled
                automatically by the SDK.
        """
        return self._client.core.items.list_items(workspace_id, type=item_type)
