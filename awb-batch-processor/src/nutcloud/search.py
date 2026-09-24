import logging

logger = logging.getLogger(__name__)

def perform_initial_search(client, awb_number: str):
    """
    Phase A: Execute the exact initial search against the database.
    Does not score results or expand directories.
    """
    logger.info(f"Processing AWB: {awb_number}")
    initial_results = client.search(awb_number)
    
    if not initial_results:
        msg = f"AWB {awb_number} not found."
        logger.error(msg)
        return None, msg
    return initial_results, None
