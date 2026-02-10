import pytest
from unittest.mock import MagicMock, patch
from src.nutcloud.client import NutStoreClient

@pytest.fixture
def mock_secrets():
    with patch('src.nutcloud.client.nutstore_cookies', {"umn": "test", "TDC_itoken": "test", "ta": "test"}):
        yield

@pytest.fixture
def client(mock_secrets):
    return NutStoreClient()

def test_search_awb_found(client):
    # Mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "sndIdStr": "hex123",
        "sndMagicStr": "magic123",
        "items": [
            {"path": "/Amazon/Test/AWB123.pdf", "isDir": False}
        ]
    }
    mock_response.raise_for_status.return_value = None
    
    with patch.object(client.session, 'get', return_value=mock_response) as mock_get:
        result = client.search("AWB123")
        
        assert result is not None
        assert result['sndId'] == "hex123"
        assert result['path'] == "/Amazon/Test/AWB123.pdf"
        assert result['isDir'] is False
        
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert kwargs['params']['keys'] == "AWB123"

def test_search_awb_not_found(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"items": []}
    
    with patch.object(client.session, 'get', return_value=mock_response):
        result = client.search("INVALID")
        assert result is None

def test_browse_folder(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"items": [{"name": "file1.pdf"}]}
    
    with patch.object(client.session, 'get', return_value=mock_response) as mock_get:
        result = client.browse("/path/to/folder", "id", "magic")
        assert result == {"items": [{"name": "file1.pdf"}]}
        
        # Checks if URL building is correct roughly (requests handles encoding mostly, but check calls)
        args, kwargs = mock_get.call_args
        assert "/browse/path/to/folder" in args[0]
