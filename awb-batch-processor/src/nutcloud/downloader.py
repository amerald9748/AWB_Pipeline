import os
import logging

logger = logging.getLogger(__name__)

def download_file(client, best_file_candidate: dict, awb_number: str, output_dir: str):
    """
    Phases C & D: Obtain the direct download link and download the file.
    Saves it to output_dir with the AWB_Number as its prefixed name.
    """
    target_path = best_file_candidate['path']
    snd_id = best_file_candidate['sndId']
    snd_magic = best_file_candidate['sndMagic']

    # Phase C: Link Generation
    download_url = client.get_download_link(target_path, snd_id, snd_magic)
    if not download_url:
        msg = "Failed to get download link."
        logger.error(msg)
        return None, msg
        
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
            return final_save_path, None
        except Exception as e:
            logger.error(f"[PIPELINE] Failed to rename file: {e}")
            return temp_save_path, f"Rename failed: {e}"
    else:
        return None, "Download failed"
