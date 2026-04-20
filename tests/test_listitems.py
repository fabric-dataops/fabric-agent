from unittest.mock import MagicMock
from services.listitems import ListItemsService


def _make_client(items):
    client = MagicMock()
    client.core.items.list_items.return_value = iter(items)
    return client


def test_list_items_delegates_to_sdk():
    mock_item = MagicMock(id="item1", display_name="My Notebook", type="Notebook")
    client = _make_client([mock_item])

    service = ListItemsService(client)
    result = list(service.list_items("ws1"))

    client.core.items.list_items.assert_called_once_with("ws1", type=None)
    assert result == [mock_item]


def test_list_items_passes_item_type_filter():
    client = _make_client([])

    service = ListItemsService(client)
    list(service.list_items("ws1", item_type="Report"))

    client.core.items.list_items.assert_called_once_with("ws1", type="Report")


def test_list_items_returns_empty_iterable():
    client = _make_client([])
    service = ListItemsService(client)
    assert list(service.list_items("ws1")) == []


def test_no_list_items_cont_method():
    client = MagicMock()
    service = ListItemsService(client)
    assert not hasattr(service, "list_items_cont")
