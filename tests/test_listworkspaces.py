from unittest.mock import MagicMock
from services.listworkspaces import ListWorkspacesService


def _make_client(workspaces):
    ws = MagicMock()
    ws.id = "ws1"
    ws.display_name = "My Workspace"

    client = MagicMock()
    client.admin.workspaces.list_workspaces.return_value = iter(workspaces)
    return client


def test_list_workspaces_delegates_to_sdk():
    mock_ws = MagicMock(id="ws1", display_name="Test WS")
    client = _make_client([mock_ws])

    service = ListWorkspacesService(client)
    result = list(service.list_workspaces())

    client.admin.workspaces.list_workspaces.assert_called_once_with(
        type="Workspace", state="Active"
    )
    assert result == [mock_ws]


def test_list_workspaces_passes_type_and_state():
    client = _make_client([])

    service = ListWorkspacesService(client)
    list(service.list_workspaces(type="Personal", state="Deleted"))

    client.admin.workspaces.list_workspaces.assert_called_once_with(
        type="Personal", state="Deleted"
    )


def test_list_workspaces_returns_empty_iterable():
    client = _make_client([])
    service = ListWorkspacesService(client)
    assert list(service.list_workspaces()) == []


def test_no_list_workspaces_cont_method():
    client = MagicMock()
    service = ListWorkspacesService(client)
    assert not hasattr(service, "list_workspaces_cont")
