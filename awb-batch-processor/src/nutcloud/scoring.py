import logging
import os
from typing import Dict, Any, Optional
from src.utils import CUSTOMER_CODE_TO_AWB_MAP

logger = logging.getLogger(__name__)

# Constants derived from SearchStrategy in search_strategies.py
CHINESE_KEYWORDS = ["收货", "派送", "计划", "清单", "多伦多", "箱单明细"]
ENGLISH_KEYWORDS = ["unloading", "load", "plan", "TOR"]
BANNED_KEYWORDS = ["ci&pl", "清关", "west", "加西"]

def score_nutstore_file(item: Dict[str, Any], awb: str) -> float:
    """
    Score a NutStore file item based on how likely it is to be the correct AWB file.
    Adapted from SearchStrategy._score_result.
    
    Args:
        item: The file item dictionary from NutStore API (contains 'name', 'path', etc.)
        awb: The AWB number being searched for.
        
    Returns:
        A score between 0.0 and 1.0.
    """
    filename = item.get('name', '').lower()
    path = item.get('path', '').lower()
    is_dir = item.get('isDir', False)
    
    # 1. Folder Logic
    if is_dir:
        # Accept folders that might contain the file
        # Strict rejection for folders? Maybe "Invoice" folder if we only want loading plan?
        # For now, let's differ "clearance" folders if they are explicitly named "Clearance" 
        # but often the good file is IN the clearance folder. 
        # So we should probably be lenient with folders.
        
        score = 0.0
        # High score if AWB is in folder name
        if awb.lower() in filename:
            score += 0.7
        else:
            # If AWB not in name, but maybe it's a "Customs" folder inside a parent that had the AWB?
            # The BFS will handle parent relevance. 
            # If this is a root search result, it MUST match AWB usually.
            # But here we are scoring items.
            pass
            
        # Keywords for folders
        if "customs" in filename or "清关" in filename:
             score += 0.2
             
        return min(score, 1.0)

    # 2. File Logic (Existing strict logic)
    # Definite rejections: Only allow Excel files and reject unwanted keywords
    if not filename.endswith(('.xlsx', '.xls')) or any(kb in filename.lower() for kb in BANNED_KEYWORDS):
        return 0.0
        
    score = 0.0
    
    # Priority 1: Files with AWB number in name
    if awb.lower() in filename:
        score += 0.3  # Increased weight for explicit match
        
    # Check for Chinese keywords
    for keyword in CHINESE_KEYWORDS:
        if keyword in filename:
            score += 0.6
            break
            
    # Check for English keywords
    for keyword in ENGLISH_KEYWORDS:
        if keyword.lower() in filename:
            score += 0.6
            break
            
    
    # Check for customer keywords in filename if AWB maps to one?
    # Since we don't have the customer code passed in, we can't easily check specific customer.
    # But we can check if ANY customer name is in the path to gain confidence that it is the right file.
    for customer in CUSTOMER_CODE_TO_AWB_MAP:
        if customer.lower() in path:
            score += 0.1
            break
    
    return min(score, 1.0)

def find_best_file_match(items: list, awb: str) -> Optional[Dict[str, Any]]:
    """
    Finds the best matching file from a list of NutStore items.
    """
    scored_items = []
    
    for item in items:
        # We now allow folders in search candidates
        score = score_nutstore_file(item, awb)
        if score > 0:
            scored_items.append((score, item))
            logger.debug(f"File '{item.get('name')}' scored: {score}")
            
    if not scored_items:
        return None
        
    # Sort by score descending
    scored_items.sort(key=lambda x: x[0], reverse=True)
    
    best_score, best_item = scored_items[0]
    logger.info(f"Best match: {best_item.get('name')} (Score: {best_score})")
    
    return best_item
