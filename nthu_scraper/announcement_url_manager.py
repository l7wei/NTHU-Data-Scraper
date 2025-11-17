"""
Announcement URL Management System

This module manages a list of announcement URLs for incremental crawling.
It supports:
- Loading and saving the URL list
- Adding new URLs discovered during full crawls
- Removing invalid/outdated URLs
- Periodic cleanup of dead links
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set


class AnnouncementURLManager:
    """Manages a list of announcement URLs for efficient crawling."""

    def __init__(self, url_list_path: Path):
        """
        Initialize the URL manager.

        Args:
            url_list_path: Path to the JSON file storing announcement URLs
        """
        self.url_list_path = url_list_path
        self.url_data: Dict[str, dict] = {}
        self.load()

    def load(self):
        """Load announcement URLs from the JSON file."""
        if self.url_list_path.exists():
            try:
                with open(self.url_list_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.url_data = data.get("urls", {})
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Failed to load URL list from {self.url_list_path}: {e}")
                self.url_data = {}
        else:
            print(f"URL list file does not exist, starting fresh: {self.url_list_path}")
            self.url_data = {}

    def save(self):
        """Save announcement URLs to the JSON file."""
        self.url_list_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "last_updated": datetime.now().isoformat(),
            "url_count": len(self.url_data),
            "urls": self.url_data,
        }
        with open(self.url_list_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)

    def add_url(self, url: str, metadata: Optional[dict] = None):
        """
        Add a new announcement URL to the list.

        Args:
            url: The announcement URL to add
            metadata: Optional metadata about the URL (department, title, etc.)
        """
        if url not in self.url_data:
            self.url_data[url] = {
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "last_crawled": None,
                "failed_attempts": 0,
                "metadata": metadata or {},
            }
        else:
            # Update last_seen timestamp
            self.url_data[url]["last_seen"] = datetime.now().isoformat()

    def mark_crawled(self, url: str, success: bool = True):
        """
        Mark a URL as crawled.

        Args:
            url: The URL that was crawled
            success: Whether the crawl was successful
        """
        if url in self.url_data:
            self.url_data[url]["last_crawled"] = datetime.now().isoformat()
            if success:
                self.url_data[url]["failed_attempts"] = 0
            else:
                self.url_data[url]["failed_attempts"] = (
                    self.url_data[url].get("failed_attempts", 0) + 1
                )

    def get_urls_to_crawl(self) -> List[str]:
        """
        Get list of URLs that should be crawled (excluding recently failed ones).

        Returns:
            List of URLs to crawl
        """
        urls = []
        for url, info in self.url_data.items():
            # Skip URLs that have failed too many times
            if info.get("failed_attempts", 0) >= 5:
                continue
            urls.append(url)
        return sorted(urls)

    def cleanup_old_urls(self, days: int = 90):
        """
        Remove URLs that haven't been seen in a full crawl for N days.

        Args:
            days: Number of days after which to remove unseen URLs
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        urls_to_remove = []

        for url, info in self.url_data.items():
            try:
                last_seen = datetime.fromisoformat(info.get("last_seen", ""))
                if last_seen < cutoff_date:
                    urls_to_remove.append(url)
            except (ValueError, TypeError):
                # If we can't parse the date, keep the URL
                pass

        for url in urls_to_remove:
            del self.url_data[url]

        if urls_to_remove:
            print(f"Cleaned up {len(urls_to_remove)} old URLs")

    def update_from_full_crawl(self, discovered_urls: Set[str]):
        """
        Update URL list based on URLs discovered in a full crawl.

        Args:
            discovered_urls: Set of URLs discovered during full crawl
        """
        # Update last_seen for all discovered URLs
        for url in discovered_urls:
            self.add_url(url)

        # Mark URLs not discovered in this crawl
        all_urls = set(self.url_data.keys())
        missing_urls = all_urls - discovered_urls

        # Increment failed_attempts for missing URLs
        for url in missing_urls:
            if url in self.url_data:
                failed = self.url_data[url].get("failed_attempts", 0)
                self.url_data[url]["failed_attempts"] = failed + 1

    def get_statistics(self) -> dict:
        """Get statistics about the URL list."""
        total = len(self.url_data)
        failed = sum(1 for info in self.url_data.values() if info.get("failed_attempts", 0) >= 5)
        recently_crawled = sum(
            1
            for info in self.url_data.values()
            if info.get("last_crawled") and
            datetime.fromisoformat(info["last_crawled"]) > datetime.now() - timedelta(hours=24)
        )

        return {
            "total_urls": total,
            "active_urls": total - failed,
            "failed_urls": failed,
            "recently_crawled": recently_crawled,
        }
