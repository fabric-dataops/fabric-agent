import json
import os
import pytest
from unittest.mock import MagicMock, patch, call


def _make_workspace(ws_id, display_name):
    ws = MagicMock()
    ws.id = ws_id
    ws.display_name = display_name
    ws.as_dict.return_value = {"id": ws_id, "displayName": display_name}
    return ws


def _make_item(item_id, item_type, ws_id):
    item = MagicMock()
    item.id = item_id
    item.type = item_type
    item.as_dict.return_value = {"id": item_id, "type": item_type}
    return item


@patch("get_workspace_items.save_output")
@patch("get_workspace_items.ListItemsService")
@patch("get_workspace_items.ListWorkspacesService")
@patch("get_workspace_items.FabricClient")
@patch("get_workspace_items.build_credential")
def test_main_fetches_all_workspaces_and_items(
    mock_cred, mock_client_cls, mock_ws_svc_cls, mock_items_svc_cls, mock_save, tmp_path
):
    ws1 = _make_workspace("ws-1", "Alpha")
    ws2 = _make_workspace("ws-2", "Beta")
    item1 = _make_item("item-1", "Notebook", "ws-1")
    item2 = _make_item("item-2", "Report", "ws-2")

    mock_ws_svc = MagicMock()
    mock_ws_svc.list_workspaces.return_value = iter([ws1, ws2])
    mock_ws_svc_cls.return_value = mock_ws_svc

    mock_items_svc = MagicMock()
    mock_items_svc.list_items.side_effect = [iter([item1]), iter([item2])]
    mock_items_svc_cls.return_value = mock_items_svc

    import get_workspace_items
    get_workspace_items.output_path = str(tmp_path)

    get_workspace_items.main()

    mock_cred.assert_called_once()
    mock_client_cls.assert_called_once_with(mock_cred.return_value)
    mock_ws_svc_cls.assert_called_once_with(mock_client_cls.return_value)
    mock_items_svc_cls.assert_called_once_with(mock_client_cls.return_value)

    assert mock_items_svc.list_items.call_count == 2
    mock_items_svc.list_items.assert_any_call("ws-1", None)
    mock_items_svc.list_items.assert_any_call("ws-2", None)

    assert mock_save.call_count == 2


@patch("get_workspace_items.save_output")
@patch("get_workspace_items.ListItemsService")
@patch("get_workspace_items.ListWorkspacesService")
@patch("get_workspace_items.FabricClient")
@patch("get_workspace_items.build_credential")
def test_main_single_workspace_skips_workspace_fetch(
    mock_cred, mock_client_cls, mock_ws_svc_cls, mock_items_svc_cls, mock_save, tmp_path
):
    item1 = _make_item("item-1", "Notebook", "ws-42")

    mock_items_svc = MagicMock()
    mock_items_svc.list_items.return_value = iter([item1])
    mock_items_svc_cls.return_value = mock_items_svc

    import get_workspace_items
    get_workspace_items.output_path = str(tmp_path)

    get_workspace_items.main(workspace_id="ws-42")

    mock_ws_svc_cls.return_value.list_workspaces.assert_not_called()
    mock_items_svc.list_items.assert_called_once_with("ws-42", None)
    mock_save.assert_called_once()


@patch("get_workspace_items.save_output")
@patch("get_workspace_items.ListItemsService")
@patch("get_workspace_items.ListWorkspacesService")
@patch("get_workspace_items.FabricClient")
@patch("get_workspace_items.build_credential")
def test_main_passes_item_type_filter(
    mock_cred, mock_client_cls, mock_ws_svc_cls, mock_items_svc_cls, mock_save, tmp_path
):
    ws1 = _make_workspace("ws-1", "Alpha")
    item1 = _make_item("item-1", "Report", "ws-1")

    mock_ws_svc = MagicMock()
    mock_ws_svc.list_workspaces.return_value = iter([ws1])
    mock_ws_svc_cls.return_value = mock_ws_svc

    mock_items_svc = MagicMock()
    mock_items_svc.list_items.return_value = iter([item1])
    mock_items_svc_cls.return_value = mock_items_svc

    import get_workspace_items
    get_workspace_items.output_path = str(tmp_path)

    get_workspace_items.main(item_type="Report")

    mock_items_svc.list_items.assert_called_once_with("ws-1", "Report")


@patch("get_workspace_items.save_output")
@patch("get_workspace_items.ListItemsService")
@patch("get_workspace_items.ListWorkspacesService")
@patch("get_workspace_items.FabricClient")
@patch("get_workspace_items.build_credential")
def test_main_injects_workspace_id_into_items(
    mock_cred, mock_client_cls, mock_ws_svc_cls, mock_items_svc_cls, mock_save, tmp_path
):
    ws1 = _make_workspace("ws-99", "Alpha")
    item1 = _make_item("item-1", "Notebook", "ws-99")

    mock_ws_svc = MagicMock()
    mock_ws_svc.list_workspaces.return_value = iter([ws1])
    mock_ws_svc_cls.return_value = mock_ws_svc

    mock_items_svc = MagicMock()
    mock_items_svc.list_items.return_value = iter([item1])
    mock_items_svc_cls.return_value = mock_items_svc

    import get_workspace_items
    get_workspace_items.output_path = str(tmp_path)

    get_workspace_items.main()

    saved_items = mock_save.call_args[0][1]
    assert saved_items[0]["workspaceId"] == "ws-99"
