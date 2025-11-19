import unittest
import os
import shutil
import tempfile
from pathlib import Path

# Add the src directory to the python path
import sys
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from search_strategies import NameBasedSearchStrategy, DirectoryNameSearchStrategy, CompositeSearchStrategy, EverythingSearchStrategy
from awb_search import find_awb_file

class TestSearchStrategies(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        # Create some dummy files and directories for testing
        # File with AWB in the name
        Path(self.test_dir, "TRHU8167267 收货派送计划.xlsx").touch()
        Path(self.test_dir, "CSLU6073202  收货派送计划.xlsx").touch()
        
        # File in a directory named after the AWB
        os.makedirs(Path(self.test_dir, "MATU2579936"))
        Path(self.test_dir, "MATU2579936", "派送清单.xlsx").touch()

        # A file with mixed naming
        Path(self.test_dir, "Unloading Plan-SMCU1260277.xls").touch()

        # A file in a nested directory
        os.makedirs(Path(self.test_dir, "nested", "folder"))
        Path(self.test_dir, "nested", "folder", "CAAU9476527.xlsx").touch()


    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_name_based_search(self):
        strategy = NameBasedSearchStrategy()
        
        # Test with existing file
        result = strategy.search("TRHU8167267", self.test_dir)
        self.assertIsNotNone(result)
        self.assertEqual(os.path.basename(result), "TRHU8167267 收货派送计划.xlsx")

        # Test with another existing file
        result = strategy.search("SMCU1260277", self.test_dir)
        self.assertIsNotNone(result)
        self.assertEqual(os.path.basename(result), "Unloading Plan-SMCU1260277.xls")

        # Test with nested file
        result = strategy.search("CAAU9476527", self.test_dir)
        self.assertIsNotNone(result)
        self.assertEqual(os.path.basename(result), "CAAU9476527.xlsx")

        # Test with non-existing file
        result = strategy.search("NONEXISTENT", self.test_dir)
        self.assertIsNone(result)

    def test_directory_name_search(self):
        strategy = DirectoryNameSearchStrategy()

        # Test with existing directory
        result = strategy.search("MATU2579936", self.test_dir)
        self.assertIsNotNone(result)
        self.assertEqual(os.path.basename(result), "派送清单.xlsx")

        # Test with non-existing directory
        result = strategy.search("NONEXISTENT", self.test_dir)
        self.assertIsNone(result)

    def test_everything_search(self):
        # This test requires Everything to be running and the test directory to be indexed.
        # We will create a file and then search for it.
        # Note: Everything indexing can take a few seconds. We might need to add a small delay.
        import time
        time.sleep(5) # Wait for Everything to index the new file.

        strategy = EverythingSearchStrategy()

        # Test with existing file
        result = strategy.search("TRHU8167267", self.test_dir)
        self.assertIsNotNone(result)
        self.assertEqual(os.path.basename(result), "TRHU8167267 收货派送计划.xlsx")

        # Test with another existing file
        result = strategy.search("SMCU1260277", self.test_dir)
        self.assertIsNotNone(result)
        self.assertEqual(os.path.basename(result), "Unloading Plan-SMCU1260277.xls")

        # Test with nested file
        result = strategy.search("CAAU9476527", self.test_dir)
        self.assertIsNotNone(result)
        self.assertEqual(os.path.basename(result), "CAAU9476527.xlsx")

        # Test with non-existing file
        result = strategy.search("NONEXISTENT", self.test_dir)
        self.assertIsNone(result)

    def test_composite_search(self):
        strategy = CompositeSearchStrategy([
            NameBasedSearchStrategy(),
            DirectoryNameSearchStrategy()
        ])

        # Test name-based search
        result = strategy.search("TRHU8167267", self.test_dir)
        self.assertIsNotNone(result)
        self.assertEqual(os.path.basename(result), "TRHU8167267 收货派送计划.xlsx")

        # Test directory-name-based search
        result = strategy.search("MATU2579936", self.test_dir)
        self.assertIsNotNone(result)
        self.assertEqual(os.path.basename(result), "派送清单.xlsx")

        # Test with non-existing file
        result = strategy.search("NONEXISTENT", self.test_dir)
        self.assertIsNone(result)

    def test_find_awb_file(self):
        # This test requires mocking get_search_directory to point to our test_dir
        # We will patch it for this test
        
        import awb_search
        original_get_search_directory = awb_search.get_search_directory
        awb_search.get_search_directory = lambda: self.test_dir

        # Test with a file that should be found by NameBasedSearchStrategy
        result = find_awb_file("TRHU8167267")
        self.assertIsNotNone(result)
        self.assertEqual(os.path.basename(result), "TRHU8167267 收货派送计划.xlsx")

        # Test with a file that should be found by DirectoryNameSearchStrategy
        result = find_awb_file("MATU2579936")
        self.assertIsNotNone(result)
        self.assertEqual(os.path.basename(result), "派送清单.xlsx")

        # Test with a non-existent awb
        result = find_awb_file("NONEXISTENT")
        self.assertIsNone(result)

        # Restore original function
        awb_search.get_search_directory = original_get_search_directory

if __name__ == '__main__':
    unittest.main()
