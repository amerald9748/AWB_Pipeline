import os
import requests
import time
import random
import logging
from urllib.parse import quote
from config.secrets import nutstore_cookies

logger = logging.getLogger(__name__)

class NutStoreClient:
    BASE_URL = "https://www.jianguoyun.com/d/ajax"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        })
        
        # Load authentication cookies
        self.session.cookies.update(nutstore_cookies)

    def _sleep(self):
        """Random sleep to prevent throttling."""
        time.sleep(random.uniform(0.5, 1.5))

    def search(self, awb: str):
        """
        Phase A: Search for the AWB.
        Returns a dict with 'sndId', 'sndMagic', 'path', 'isDir' if found, else None.
        """
        self._sleep()
        url = f"{self.BASE_URL}/search/run"
        params = {
            "keys": awb,
            "all": "false",
            "ft": "false"
        }
        
        logger.info(f"[SEARCH] Searching for AWB: {awb}")
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                logger.warning(f"[SEARCH] No results found for AWB: {awb}")
                return []
            
            all_items = []
            for r in results:
                snd_id = r.get("sndIdStr")
                snd_magic = r.get("sndMagicStr")
                for item in r.get("items", []):
                    # Attach credentials to each item
                    item['sndId'] = snd_id
                    item['sndMagic'] = snd_magic
                    
                    # Ensure 'name' exists for scoring
                    if 'name' not in item and 'path' in item:
                        item['name'] = os.path.basename(item['path'])
                        
                    all_items.append(item)
            
            if not all_items:
                logger.warning(f"[SEARCH] No items found in any results for AWB: {awb}")
                return []
                
            logger.info(f"[SEARCH] Found {len(all_items)} potential matches for {awb}")
            return all_items
            
        except Exception as e:
            logger.error(f"[SEARCH] Error searching for {awb}: {e}")
            raise

    def browse(self, path: str, snd_id: str, snd_magic: str):
        """
        Phase B: List folder contents.
        """
        self._sleep()
        encoded_path = quote(path)
        # Note: The prompt says "URL is dynamic. Structure: .../d/ajax/browse + {URL_ENCODED_PATH}"
        # But requests handles params usually. However, the requirement is specific about the URL structure.
        # "endpoint/d/ajax/browse/Amazon/MyFolder..."
        # But also says query parameters sndId, sndMagic.
        
        # We need to construct the URL carefully.
        # If path starts with /, we might need to strip it or handle it.
        # Assuming path from search is like "/Amazon/..."
        
        # It seems the browse endpoint is path-based: /d/ajax/browse{path}
        
        url = f"{self.BASE_URL}/browse{path}" # Path usually already has leading slash
        
        params = {
            "sndId": snd_id,
            "sndMagic": snd_magic
        }
        
        logger.info(f"[BROWSE] Listing contents of: {path}")
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"[BROWSE] Error browsing {path}: {e}")
            raise

    def get_download_link(self, path: str, snd_id: str, snd_magic: str):
        """Phase C: Get download link."""
        self._sleep()
        url = f"{self.BASE_URL}/dlink"
        params = {
            "sndId": snd_id,
            "sndMagic": snd_magic,
            "path": path,
            "forwin": "true"
        }
        
        logger.info(f"[LINK] Getting download link for: {path}")
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            download_url = data.get("url") or data.get("data")
            
            if download_url and download_url.startswith('/'):
                download_url = "https://www.jianguoyun.com" + download_url
                
            return download_url
        except Exception as e:
            logger.error(f"[LINK] Error getting link for {path}: {e}")
            raise

    def download(self, url: str, save_path: str):
        """Phase D: Download file."""
        self._sleep()
        logger.info(f"[DOWNLOAD] Downloading to: {save_path}")
        try:
            with self.session.get(url, stream=True) as r:
                r.raise_for_status()
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            logger.info("[DOWNLOAD] Success")
            return True
        except Exception as e:
            logger.error(f"[DOWNLOAD] Failed: {e}")
            raise
