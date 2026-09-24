import os
import logging
from dotenv import load_dotenv
from .client import NutStoreClient
from .search import perform_initial_search
from .bfs import perform_bfs_search
from .downloader import download_file

load_dotenv()
logger = logging.getLogger(__name__)

def process_awb(awb_number: str, output_dir: str = None) -> dict:
    if output_dir is None:
        output_dir = os.getenv("OUTPUT_DIR", "./output")
    """
    Orchestrates the modularized search, bfs, and download pipeline.
    Returns: {'success': bool, 'file': str, 'error': str}
    """
    client = NutStoreClient()
    
    # Phase A: Search
    initial_results, error = perform_initial_search(client, awb_number)
    if error:
        return {'success': False, 'file': None, 'error': error}
        
    # Phase B: Priority-based Breadth-First Search (BFS)
    best_file_candidate, error = perform_bfs_search(client, initial_results, awb_number)
    if error:
        return {'success': False, 'file': None, 'error': error}
        
    # Phase C & D: Link Generation and Download
    final_file_path, error = download_file(client, best_file_candidate, awb_number, output_dir)
    if error and not final_file_path:
        return {'success': False, 'file': None, 'error': error}
        
    return {'success': True, 'file': final_file_path, 'error': error}
