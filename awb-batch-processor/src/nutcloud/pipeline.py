import os
import logging
from .client import NutStoreClient
from .scoring import find_best_file_match, score_nutstore_file

logger = logging.getLogger(__name__)

def process_awb(awb_number: str, output_dir: str = r"D:\Automation_Workspace\Downloaded_AWBs") -> dict:
    """
    Orchestrates the search, browse, filter, and download pipeline using a priority BFS.
    Returns: {'success': bool, 'file': str, 'error': str}
    """
    client = NutStoreClient()
    
    # Phase A: Search
    logger.info(f"Processing AWB: {awb_number}")
    initial_results = client.search(awb_number)
    
    if not initial_results:
        msg = f"AWB {awb_number} not found."
        logger.error(msg)
        return {'success': False, 'file': None, 'error': msg}
        
    # Initialize Priority Queue with search results
    # Format: (score, item)
    # We want max score first, so we'll sort descending.
    queue = []
    for item in initial_results:
        score = score_nutstore_file(item, awb_number)
        if score > 0:
            queue.append((score, item))
            
    # Sort queue descending by score
    queue.sort(key=lambda x: x[0], reverse=True)
    
    visited_paths = set()
    browse_count = 0
    MAX_BROWSE_REQUESTS = 20
    
    best_file_candidate = None
    best_file_score = 0.0
    
    while queue:
        # Get highest scored item
        current_score, current_item = queue.pop(0)
        
        # If we have a file candidate better than the rest of the queue, we can potentially stop early?
        # Or just keep searching until we find a "perfect" match or run out of time.
        # Let's say if we find a file with > 0.5 score (meaning it has AWB in name + good ext), we might want to stop?
        # Actually, let's just process.
        
        path = current_item.get('path')
        if path in visited_paths:
            continue
        visited_paths.add(path)
        
        is_dir = current_item.get('isDir', False)
        name = current_item.get('name')
        
        logger.debug(f"[BFS] Processing: {name} | Score: {current_score} | Dir: {is_dir}")
        
        if is_dir:
            # Check limits
            if browse_count >= MAX_BROWSE_REQUESTS:
                logger.warning("[BFS] Max browse requests reached. Stopping expansion.")
                continue
                
            # Browse folder
            logger.info(f"[BROWSE] Browsing folder: {name}")
            try:
                folder_content = client.browse(path, current_item.get('sndId'), current_item.get('sndMagic'))
                browse_count += 1
                
                if isinstance(folder_content, dict):
                    items = folder_content.get('items') or folder_content.get('list') or folder_content.get('contents') or []
                else:
                    items = folder_content
                    
                # Score children and add to queue
                new_items = []
                for child in items:
                    # Construct full path/credentials
                    if not child.get('path'):
                         child['path'] = f"{path.rstrip('/')}/{child['name']}"
                    
                    child['sndId'] = current_item.get('sndId')
                    child['sndMagic'] = current_item.get('sndMagic')
                    
                    child_score = score_nutstore_file(child, awb_number)
                    if child_score > 0:
                        new_items.append((child_score, child))
                
                # Add to queue and re-sort
                queue.extend(new_items)
                queue.sort(key=lambda x: x[0], reverse=True)
                
            except Exception as e:
                logger.error(f"[BFS] Error browsing {name}: {e}")
                
        else:
            # It's a file. Is it better than our current best?
            # We already sorted, so the first file we encounter *should* be the best if our heuristic is perfect.
            # But the queue is mixed (Files and Folders).
            
            # If it's a file and score > 0 (which it is if it's in queue), it's a candidate.
            logger.info(f"[BFS] Found file candidate: {name} (Score: {current_score})")
            
            # Update best candidate
            if current_score > best_file_score:
                best_file_score = current_score
                best_file_candidate = current_item
                
                # If excellent match (e.g. AWB in name + Excel), maybe stop?
                # score >= 0.4 usually means matched AWB(0.3) + Excel(0.1).
                if current_score >= 0.4:
                    logger.info(f"[BFS] Found excellent match. Stopping search.")
                    break
    
    if not best_file_candidate:
        msg = "No suitable file found after search."
        logger.warning(msg)
        return {'success': False, 'file': None, 'error': msg}
        
    logger.info(f"[SELECT] Final selection: {best_file_candidate.get('name')} (Score: {best_file_score})")
    
    target_path = best_file_candidate['path']
    snd_id = best_file_candidate['sndId']
    snd_magic = best_file_candidate['sndMagic']

    # Phase C: Link Generation
    download_url = client.get_download_link(target_path, snd_id, snd_magic)
    if not download_url:
        msg = "Failed to get download link."
        logger.error(msg)
        return {'success': False, 'file': None, 'error': msg}
        
    # Phase D: Download
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = os.path.basename(target_path)
    temp_save_path = os.path.join(output_dir, filename)
    
    if client.download(download_url, temp_save_path):
        _, extension = os.path.splitext(filename)
        final_filename = f"{awb_number}{extension}"
        final_save_path = os.path.join(output_dir, final_filename)
        
        # Rename to AWB format
        try:
            if os.path.exists(final_save_path):
                os.remove(final_save_path) # Overwrite if exists
            os.rename(temp_save_path, final_save_path)
            logger.info(f"[PIPELINE] Renamed {filename} to {final_filename}")
            return {'success': True, 'file': final_save_path, 'error': None}
        except Exception as e:
            logger.error(f"[PIPELINE] Failed to rename file: {e}")
            return {'success': True, 'file': temp_save_path, 'error': f"Rename failed: {e}"}
    else:
        return {'success': False, 'file': None, 'error': "Download failed"}
