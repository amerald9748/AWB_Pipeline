from unittest.mock import MagicMock, patch
import os
import pytest
from src.search_strategies import NameBasedSearchStrategy, DirectoryNameSearchStrategy, CompositeSearchStrategy, EverythingSearchStrategy
# Mock the PyEverything module for testing without actual installation
try:
    from PyEverything import SetSearch, Query, GetNumResults, GetResultFullPathName
except ImportError:
    # Create mock objects if PyEverything is not installed
    class MockPyEverything:
        def SetSearch(*args, **kwargs): pass
        def Query(*args, **kwargs): pass
        def GetNumResults(*args, **kwargs): return 0
        def GetResultFullPathName(*args, **kwargs): return ""
    SetSearch = MockPyEverything.SetSearch
    Query = MockPyEverything.Query
    GetNumResults = MockPyEverything.GetNumResults
    GetResultFullPathName = MockPyEverything.GetResultFullPathName


@pytest.fixture
def base_path():
    return "/dummy/path/to/awb"

@pytest.fixture
def mock_os_walk():
    with patch('os.walk') as mock_walk, patch('os.listdir') as mock_listdir:
        mock_walk.return_value = [
            ("/dummy/path/to/awb", ["MATU1234567"], []),  # Base directory
            ("/dummy/path/to/awb/MATU1234567", [], ["MATU1234567_清单.xlsx", "other.txt"])
        ]
        def side_effect(path):
            if os.path.normpath(path) == os.path.normpath("/dummy/path/to/awb/MATU1234567"):
                return ["MATU1234567_清单.xlsx", "other.txt"]
            return []
        mock_listdir.side_effect = side_effect
        yield


@pytest.fixture
def mock_everything_sdk():
    with patch('src.search_strategies.everything_sdk') as mock_sdk:
        yield mock_sdk

def test_name_based_search_strategy(mock_os_walk, base_path):
    strategy = NameBasedSearchStrategy()
    result = strategy.search("MATU1234567", base_path)
    expected = os.path.join(base_path, "MATU1234567", "MATU1234567_清单.xlsx")
    assert os.path.normpath(result) == os.path.normpath(expected)

def test_directory_name_search_strategy(mock_os_walk, base_path):
    strategy = DirectoryNameSearchStrategy()
    result = strategy.search("MATU1234567", base_path)
    expected = os.path.join(base_path, "MATU1234567", "MATU1234567_清单.xlsx")
    assert os.path.normpath(result) == os.path.normpath(expected)

def test_everything_search_strategy_found(base_path):
    expected = os.path.join(base_path, "MATU1234567", "MATU1234567_清单.xlsx")
    with patch('src.search_strategies.GetNumResults', return_value=1), \
         patch('src.search_strategies.GetResultFullPathName', return_value=expected):
        strategy = EverythingSearchStrategy()
        result = strategy.search("MATU1234567", base_path)
        assert os.path.normpath(result) == os.path.normpath(expected)

def test_everything_search_strategy_not_found(base_path):
    with patch('src.search_strategies.GetNumResults', return_value=0):
        strategy = EverythingSearchStrategy()
        result = strategy.search("NONEXISTENT", base_path)
        assert result is None

def test_composite_search_strategy(mock_os_walk, base_path):
    expected = os.path.join(base_path, "MATU1234567", "MATU1234567_清单.xlsx")
    # Test scenario where Everything finds it first
    with patch('src.search_strategies.GetNumResults', return_value=1), \
         patch('src.search_strategies.GetResultFullPathName', return_value=expected):
        strategy = CompositeSearchStrategy([EverythingSearchStrategy()])
        result = strategy.search("MATU1234567", base_path)
        assert os.path.normpath(result) == os.path.normpath(expected)

    # Reset mocks and test scenario where Everything doesn't find it, but NameBased does
    with patch('src.search_strategies.GetNumResults', return_value=0):
        strategy = CompositeSearchStrategy([EverythingSearchStrategy(), NameBasedSearchStrategy()])
        result = strategy.search("MATU1234567", base_path)
        assert os.path.normpath(result) == os.path.normpath(expected)