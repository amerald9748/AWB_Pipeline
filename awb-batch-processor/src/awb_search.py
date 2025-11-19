from typing import Optional
from search_strategies import SearchStrategy, get_default_search_strategy
from utils import get_logger, CUSTOMER_CODE_TO_AWB_MAP
import json
import os

log_file_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'awb_search.log')
logger = get_logger(__name__, log_file_path)

def get_search_directory(customer_code: Optional[str] = None) -> str:
    """
    Reads the base search path from the settings.json file
    and appends a customer-specific path if a customer code is provided.
    """
    settings_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json')
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)
    base_path = settings['paths']['base_search_path']

    if customer_code and customer_code in CUSTOMER_CODE_TO_AWB_MAP:
        customer_folder = CUSTOMER_CODE_TO_AWB_MAP[customer_code]
        return os.path.join(base_path, customer_folder)
    
    return base_path

def find_awb_file(pipeline_input: dict, search_strategy: Optional[SearchStrategy] = None) -> Optional[str]:
    """
    Finds a file for a given AWB number using a search strategy.

    Args:
        pipeline_input: A dictionary containing 'customer_code' and 'awb'.
        search_strategy: The search strategy to use. If None, the default strategy is used.

    Returns:
        The path to the file if found, otherwise None.
    """
    if search_strategy is None:
        search_strategy = get_default_search_strategy()
    
    customer_code = pipeline_input.get("customer_code")
    awb = pipeline_input.get("awb")

    if not awb:
        logger.error("AWB number is missing from the pipeline input.")
        return None

    search_directory = get_search_directory(customer_code)
    
    logger.info(f"Searching for AWB '{awb}' in directory '{search_directory}'")
    
    result = search_strategy.search(awb, search_directory)
    
    if result:
        logger.info(f"Found file for AWB '{awb}': {result}")
    else:
        logger.warning(f"Could not find a file for AWB '{awb}'")
        
    return result
