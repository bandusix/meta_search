import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class ProgressTracker:
    """Tracks scraping progress to allow resuming"""
    
    def __init__(self, filepath: str = "scraper_progress.json"):
        self.filepath = filepath
        self.data = self._load()
        
    def _load(self) -> Dict:
        """Load progress from file"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load progress file: {e}")
        return {}
        
    def save(self, year: int, page: int):
        """Save current progress"""
        self.data['last_year'] = year
        self.data['last_page'] = page
        self.data['updated_at'] = datetime.now().isoformat()
        
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
            
    def get_last_page(self, year: int) -> int:
        """Get the last scraped page for a given year"""
        # Only return the page if the stored year matches the requested year
        # This assumes we scrape one year at a time or want to resume the specific year we stopped at
        if self.data.get('last_year') == year:
            return self.data.get('last_page', 0)
        return 0

    def reset(self):
        """Reset progress"""
        self.data = {}
        if os.path.exists(self.filepath):
            os.remove(self.filepath)
