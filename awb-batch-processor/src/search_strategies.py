import logging
from abc import ABC, abstractmethod
import os
import re
import subprocess
from PyEverything import SetSearch, Query, GetNumResults, GetResultFullPathName
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SearchStrategy(ABC):
    """
    Abstract base class for a search strategy.
    """
    # Chinese keywords that indicate this might be the right file
    _CHINESE_KEYWORDS = ["收货", "派送", "计划", "清单"]
    
    # English keywords that indicate this might be the right file (case-insensitive)
    _ENGLISH_KEYWORDS = ["unloading", "load", "plan"]
    
    def _score_result(self, filepath: str, awb: str) -> float:
        """
        Score a search result based on how likely it is to be the file we want.
        Higher score means more likely to be correct.

        Args:
            filepath: The path to the file to score
            awb: The AWB number being searched for

        Returns:
            A score between 0 and 1, where 1 is most likely to be correct
        """
        filename = os.path.basename(filepath).lower()
        
        # Definite rejections
        if "ci&pl" in filename.lower():
            return 0.0
        
        score = 0.0
        
        # Prefer files that are directly named with the AWB (highest priority)
        if filename.startswith(awb.lower()):
            score += 0.1
        
        # Check for Chinese keywords (high priority)
        for keyword in self._CHINESE_KEYWORDS:
            if keyword in filename:
                score += 0.2
                break  # Only count one Chinese keyword match
        
        # Check for English keywords (case-insensitive)
        filename_lower = filename.lower()
        for keyword in self._ENGLISH_KEYWORDS:
            if keyword.lower() in filename_lower:
                score += 0.2
                break  # Only count one English keyword match
        
        # Prefer files in directories containing the AWB
        parent_dir = os.path.basename(os.path.dirname(filepath)).lower()
        if awb.lower() in parent_dir:
            score += 0.1
            
        # Small bonus for .xlsx files (newer format)
        if filename.endswith('.xlsx'):
            score += 0.1
            
        return min(score, 1.0)

    @abstractmethod
    def search(self, awb: str, directory: str) -> Optional[str]:
        """
        Searches for files in the given directory.

        Args:
            awb: The AWB number to search for.
            directory: The directory to search in.

        Returns:
            The path to the most likely file, or None if no files are found.
        """
        pass

class EverythingSearchStrategy(SearchStrategy):
    """
    Searches for files using the Everything command-line tool (es.exe).
    This is the fastest method if Everything is installed and the index is up to date.
    """
    def _score_result(self, filepath: str, awb: str) -> float:
        """
        Score a search result based on how likely it is to be the file we want.
        """
        return SearchStrategy._score_result(self, filepath, awb)

    def search(self, awb: str, directory: str) -> Optional[str]:
        """
        Uses Everything to search for files.
        Returns the path to the most likely file, or None if no files are found.
        """
        try:
            # The search query will look for files that contain the AWB and have an excel extension.
            # The query is case-insensitive by default in Everything.
            query = f'\"{directory}\" \"{awb}\" <ext:xls|ext:xlsx>'
            
            logging.info(f"Executing Everything search with query: {query}")

            SetSearch(query)
            Query()

            results = []
            num_results = GetNumResults()
            
            if num_results > 0:
                # Collect all results and their scores
                scored_results = []
                for i in range(num_results):
                    filepath = GetResultFullPathName(i)
                    score = self._score_result(filepath, awb)
                    if score > 0:  # Only include results that weren't rejected
                        scored_results.append((score, filepath))
                
                # Sort by score in descending order
                scored_results.sort(reverse=True)
                results = [path for score, path in scored_results]
                
                if results:
                    logging.info(f"Everything search found {len(results)} potential files for '{awb}'")
                    for i, path in enumerate(results):
                        logging.info(f"Candidate {i+1}: {path}")
                else:
                    logging.info(f"Everything search found files for '{awb}' but all were filtered out.")
            else:
                logging.info(f"Everything search for '{awb}' found nothing.")
            
            return results[0] if results else None
            
        except Exception as e:
            logging.error(f"An error occurred during Everything search: {e}")
            return None

class NameBasedSearchStrategy(SearchStrategy):
    """
    A search strategy that finds files based on their names using a regex pattern.
    This is a fallback if Everything is not available.
    """
    def _score_result(self, filepath: str, awb: str) -> float:
        """
        Score a search result based on how likely it is to be the file we want.
        """
        return SearchStrategy._score_result(self, filepath, awb)

    def search(self, awb: str, directory: str) -> Optional[str]:
        """
        Walks through the directory and finds files with the AWB in their names.
        Returns the path to the most likely file, or None if no files are found.
        """
        pattern = re.compile(re.escape(awb), re.IGNORECASE)
        excel_extensions = ('.xlsx', '.xls')
        results = []

        logging.info(f"Starting name-based search for '{awb}' in '{directory}'")
        for root, _, files in os.walk(directory):
            for file in files:
                # Handle potential unicode characters in filenames
                try:
                    decoded_file = file
                except UnicodeDecodeError:
                    decoded_file = file.encode('utf-8', 'surrogateescape').decode('utf-8')

                if decoded_file.endswith(excel_extensions) and pattern.search(decoded_file):
                    found_path = os.path.join(root, file)
                    score = self._score_result(found_path, awb)
                    if score > 0:  # Only include results that weren't rejected
                        results.append((score, found_path))
        
        # Sort by score in descending order
        results.sort(reverse=True)
        results = [path for score, path in results]
        
        if results:
            logging.info(f"Name-based search found {len(results)} potential files for '{awb}'")
            for i, path in enumerate(results):
                logging.info(f"Candidate {i+1}: {path}")
        else:
            logging.info(f"Name-based search for '{awb}' found nothing.")
            
        return results[0] if results else None

class DirectoryNameSearchStrategy(SearchStrategy):
    """
    A search strategy that finds files based on the directory name.
    This is useful if files are organized in folders named after the AWB.
    """
    def _score_result(self, filepath: str, awb: str) -> float:
        """
        Score a search result based on how likely it is to be the file we want.
        """
        score = SearchStrategy._score_result(self, filepath, awb)
        # Add extra score for files in AWB-named directories
        if score > 0:  # Only if the file wasn't rejected
            score += 0.1  # Small bonus for being in the right directory
        return min(score, 1.0)

    def search(self, awb: str, directory: str) -> Optional[str]:
        """
        Walks through the directory and finds directories with the AWB in their names,
        then returns excel files from those directories.
        Returns the path to the most likely file, or None if no files are found.
        """
        pattern = re.compile(re.escape(awb), re.IGNORECASE)
        excel_extensions = ('.xlsx', '.xls')
        results = []

        logging.info(f"Starting directory-name-based search for '{awb}' in '{directory}'")
        for root, dirs, _ in os.walk(directory):
            for d in dirs:
                if pattern.search(d):
                    dir_path = os.path.join(root, d)
                    logging.info(f"Found matching directory: {dir_path}")
                    try:
                        for f in os.listdir(dir_path):
                            if f.endswith(excel_extensions):
                                found_path = os.path.join(dir_path, f)
                                score = self._score_result(found_path, awb)
                                if score > 0:  # Only include results that weren't rejected
                                    results.append((score, found_path))
                    except FileNotFoundError:
                        logging.error(f"Directory not found, it might have been deleted: {dir_path}")
                        continue
        
        # Sort by score in descending order
        results.sort(reverse=True)
        results = [path for score, path in results]
        
        if results:
            logging.info(f"Directory-name-based search found {len(results)} potential files for '{awb}'")
            for i, path in enumerate(results):
                logging.info(f"Candidate {i+1}: {path}")
        else:
            logging.info(f"Directory-name-based search for '{awb}' found nothing.")
            
        return results[0] if results else None

class CompositeSearchStrategy(SearchStrategy):
    """
    A composite search strategy that tries multiple strategies and combines their results.
    """
    def __init__(self, strategies: List[SearchStrategy]):
        self._strategies = strategies

    def search(self, awb: str, directory: str) -> Optional[str]:
        """
        Iterates through the strategies and returns the first valid result.
        If EverythingSearchStrategy finds a result, we use it since it's fastest and most reliable.
        Otherwise, we try other strategies as fallback.
        """
        logging.info(f"Starting composite search for '{awb}'")
        
        for strategy in self._strategies:
            logging.info(f"Trying strategy: {strategy.__class__.__name__}")
            result = strategy.search(awb, directory)
            
            if result:
                logging.info(f"Strategy {strategy.__class__.__name__} found a result: {result}")
                return result
        
        logging.warning(f"Composite search for '{awb}' failed. No files found.")
        return None

def get_default_search_strategy() -> SearchStrategy:
    """
    Returns a default composite search strategy.
    """
    return CompositeSearchStrategy([
        EverythingSearchStrategy(),
        NameBasedSearchStrategy(),
        DirectoryNameSearchStrategy(),
    ])

if __name__ == '__main__':
    # Create a test instance of the EverythingSearchStrategy
    everything_search = EverythingSearchStrategy()

    # The AWB to search for
    awb_to_find = "CCLU7823213"

    # The directory to search in (replace with the actual path)
    # Based on the example, it might be something like 'D:\\UnloadingPlans'
    search_directory = r"D:\UnloadingPlans"

    # Perform the search
    result_path = everything_search.search(awb_to_find, search_directory)

    # Print the result
    if result_path:
        print(f"Found file at: {result_path}")
    else:
        print(f"File for AWB '{awb_to_find}' not found.")
