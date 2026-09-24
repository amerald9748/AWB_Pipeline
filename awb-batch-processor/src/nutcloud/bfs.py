import logging
from .scoring import score_nutstore_file

logger = logging.getLogger(__name__)

def perform_bfs_search(client, initial_results: list, awb_number: str):
    """
    Phase B: Priority-based Breadth-First Search (BFS)
    Takes initial results, scores them, and expands directories based on best candidates.
    """
    # Initialize Priority Queue to sort search results by highest match score first.
    # Queue Format: List of tuples -> (score, item_metadata)
    queue = []
    for item in initial_results:
        score = score_nutstore_file(item, awb_number)
        if score > 0:
            queue.append((score, item))
            
    queue.sort(key=lambda x: x[0], reverse=True)
    
    visited_paths = set()
    browse_count = 0
    MAX_BROWSE_REQUESTS = 20
    
    best_file_candidate = None
    best_file_score = 0.0
    
    while queue:
        # Get highest scored item
        current_score, current_item = queue.pop(0)
        
        # --- Process Node ---
        # Pop the highest scoring node from queue for processing. 
        # Check against visited paths to prevent infinite recursion on circular structures.
        path = current_item.get('path')
        if path in visited_paths:
            continue
        visited_paths.add(path)
        
        is_dir = current_item.get('isDir', False)
        name = current_item.get('name')
        
        logger.debug(f"[BFS] Processing: {name} | Score: {current_score} | Dir: {is_dir}")
        
        if is_dir:
            if browse_count >= MAX_BROWSE_REQUESTS:
                logger.warning("[BFS] Max browse requests reached. Stopping expansion.")
                continue
                
            logger.info(f"[BROWSE] Browsing folder: {name}")
            try:
                folder_content = client.browse(path, current_item.get('sndId'), current_item.get('sndMagic'))
                browse_count += 1
                
                if isinstance(folder_content, dict):
                    items = folder_content.get('items') or folder_content.get('list') or folder_content.get('contents') or []
                else:
                    items = folder_content
                    
                new_items = []
                for child in items:
                    if not child.get('path'):
                         child['path'] = f"{path.rstrip('/')}/{child['name']}"
                    
                    child['sndId'] = current_item.get('sndId')
                    child['sndMagic'] = current_item.get('sndMagic')
                    
                    child_score = score_nutstore_file(child, awb_number)
                    if child_score > 0:
                        new_items.append((child_score, child))
                
                queue.extend(new_items)
                queue.sort(key=lambda x: x[0], reverse=True)
                
            except Exception as e:
                logger.error(f"[BFS] Error browsing {name}: {e}")
                
        else:
            # --- Evaluate File Candidate ---
            # If the item is a file, compare its score against our best historical find.
            # The queue contains mixed node types, so we maintain the best file found during traversal.
            logger.info(f"[BFS] Found file candidate: {name} (Score: {current_score})")
            
            # Update best candidate
            if current_score > best_file_score:
                best_file_score = current_score
                best_file_candidate = current_item
                
                # Dynamic early-exit heuristic:
                # A score >= 0.4 implies both AWB number and target extension perfectly matched.
                if current_score >= 0.4:
                    logger.info(f"[BFS] Found excellent match. Stopping search.")
                    break
    
    if not best_file_candidate:
        msg = "No suitable file found after search."
        logger.warning(msg)
        return None, msg
        
    logger.info(f"[SELECT] Final selection: {best_file_candidate.get('name')} (Score: {best_file_score})")
    return best_file_candidate, None
