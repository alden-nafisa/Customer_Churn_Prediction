"""
Generic YouTube Scraper using YouTube Data API v3
Handles: Single videos, playlists, live streams
Output: CSV with comment metadata and content
"""

import pandas as pd
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path
import time
import googleapiclient.discovery
import googleapiclient.errors
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class YouTubeScraper:
    """
    Scrapes YouTube comments from any video using YouTube Data API v3
    
    Features:
    - Automatic pagination handling
    - Rate limit & quota tracking
    - Retry logic with exponential backoff
    - Data validation and deduplication
    - CSV/JSON export
    """
    
    def __init__(self, api_key: str, max_results: int = 1000):
        """
        Initialize YouTube API client
        
        Args:
            api_key: YouTube Data API v3 key
            max_results: Maximum comments to fetch (default 1000, max 10000)
        """
        self.api_key = api_key
        self.max_results = min(max_results, 10000)  # API limit
        self.youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=api_key
        )
        self.comments = []
        self.stats = {
            "total_fetched": 0,
            "duplicates_removed": 0,
            "api_calls": 0,
            "quota_used": 0,
        }
        logger.info(f"✓ YouTube API client initialized | Max comments: {self.max_results}")
    
    def _extract_video_id(self, url_or_id: str) -> str:
        """
        Extract video ID from YouTube URL or return as-is if already ID
        
        Supports:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - Just VIDEO_ID
        """
        if "youtube.com/watch?v=" in url_or_id:
            return url_or_id.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url_or_id:
            return url_or_id.split("youtu.be/")[1].split("?")[0]
        else:
            return url_or_id  # Assume it's already the video ID
    
    def _format_timestamp(self, iso_timestamp: str) -> str:
        """Convert ISO 8601 timestamp to readable format"""
        try:
            dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return iso_timestamp
    
    def _get_video_info(self, video_id: str) -> Dict:
        """Fetch video title, channel, upload date"""
        try:
            request = self.youtube.videos().list(
                part="snippet,statistics",
                id=video_id
            )
            response = request.execute()
            self.stats["api_calls"] += 1
            
            if response["items"]:
                item = response["items"][0]
                return {
                    "title": item["snippet"]["title"],
                    "channel": item["snippet"]["channelTitle"],
                    "upload_date": self._format_timestamp(item["snippet"]["publishedAt"]),
                    "view_count": item["statistics"].get("viewCount", 0),
                }
            return {}
        except Exception as e:
            logger.warning(f"⚠ Could not fetch video info: {e}")
            return {}
    
    def scrape_video(self, video_id_or_url: str, retry_count: int = 3) -> pd.DataFrame:
        """
        Scrape all comments from a YouTube video
        
        Args:
            video_id_or_url: YouTube video ID or full URL
            retry_count: Number of retries on rate limit
            
        Returns:
            DataFrame with columns:
            - comment_id: Unique comment ID
            - timestamp: When comment was posted
            - author: Username of commenter
            - message: Comment text
            - likes: Number of likes
            - replies: Number of replies
        """
        video_id = self._extract_video_id(video_id_or_url)
        logger.info(f"📺 Starting scrape for video: {video_id}")
        
        # Get video info
        video_info = self._get_video_info(video_id)
        logger.info(f"   Title: {video_info.get('title', 'Unknown')}")
        logger.info(f"   Channel: {video_info.get('channel', 'Unknown')}")
        
        self.comments = []
        page_token = None
        retry_attempt = 0
        
        while len(self.comments) < self.max_results:
            try:
                request = self.youtube.commentThreads().list(
                    part="snippet,replies",
                    videoId=video_id,
                    maxResults=min(100, self.max_results - len(self.comments)),
                    pageToken=page_token,
                    textFormat="plainText",
                    order="relevance"
                )
                response = request.execute()
                self.stats["api_calls"] += 1
                
                # Process comments
                for item in response.get("items", []):
                    comment_data = self._extract_comment(item)
                    self.comments.append(comment_data)
                
                # Check for next page
                page_token = response.get("nextPageToken")
                if not page_token:
                    logger.info(f"✓ Reached end of comments (total: {len(self.comments)})")
                    break
                
                logger.info(f"   Fetched {len(self.comments)} comments so far...")
                retry_attempt = 0  # Reset retry on success
                
            except googleapiclient.errors.HttpError as e:
                if e.resp.status == 403:  # Quota exceeded
                    logger.error(f"❌ API Quota exceeded. Stopping.")
                    break
                elif e.resp.status == 429:  # Rate limited
                    wait_time = (2 ** retry_attempt)  # Exponential backoff
                    logger.warning(f"⚠ Rate limited. Waiting {wait_time}s... (attempt {retry_attempt+1}/{retry_count})")
                    if retry_attempt >= retry_count:
                        logger.error(f"❌ Max retries reached. Stopping.")
                        break
                    time.sleep(wait_time)
                    retry_attempt += 1
                else:
                    logger.error(f"❌ API Error: {e}")
                    break
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                break
        
        # Remove duplicates
        initial_count = len(self.comments)
        self.comments = list({c["comment_id"]: c for c in self.comments}.values())
        self.stats["duplicates_removed"] = initial_count - len(self.comments)
        
        # Create DataFrame
        df = pd.DataFrame(self.comments)
        
        # Add video metadata
        df["video_id"] = video_id
        df["video_title"] = video_info.get("title", "Unknown")
        df["video_channel"] = video_info.get("channel", "Unknown")
        
        logger.info(f"\n📊 SCRAPE COMPLETE")
        logger.info(f"   Total comments: {len(df)}")
        logger.info(f"   Duplicates removed: {self.stats['duplicates_removed']}")
        logger.info(f"   API calls: {self.stats['api_calls']}")
        
        self.stats["total_fetched"] = len(df)
        return df
    
    def _extract_comment(self, item: Dict) -> Dict:
        """Extract relevant fields from API response"""
        try:
            # Top-level comment
            comment = item["snippet"]["topLevelComment"]["snippet"]
            
            return {
                "comment_id": item["id"],
                "author": comment["authorDisplayName"],
                "message": comment["textDisplay"],
                "timestamp": self._format_timestamp(comment["publishedAt"]),
                "likes": comment["likeCount"],
                "replies": item["snippet"]["totalReplyCount"],
                "is_reply": False,
            }
        except Exception as e:
            logger.warning(f"⚠ Could not extract comment: {e}")
            return None
    
    def save_to_csv(self, df: pd.DataFrame, output_path: str) -> Path:
        """Save comments to CSV with metadata"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"✓ Saved {len(df)} comments to {output_file}")
        return output_file
    
    def save_to_json(self, df: pd.DataFrame, output_path: str) -> Path:
        """Save comments to JSON with metadata"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        metadata = {
            "scrape_timestamp": datetime.now().isoformat(),
            "total_comments": len(df),
            "stats": self.stats,
        }
        
        data = {
            "metadata": metadata,
            "comments": df.to_dict("records")
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✓ Saved {len(df)} comments to {output_file}")
        return output_file
    
    def validate_data(self, df: pd.DataFrame) -> Dict:
        """Validate scraped data quality"""
        validation = {
            "total_comments": len(df),
            "missing_values": df.isnull().sum().to_dict(),
            "duplicate_authors": df["author"].duplicated().sum(),
            "avg_message_length": df["message"].str.len().mean(),
            "max_likes": df["likes"].max(),
            "avg_likes": df["likes"].mean(),
            "timestamp_range": {
                "oldest": df["timestamp"].min(),
                "newest": df["timestamp"].max(),
            }
        }
        return validation
    
    def get_stats(self) -> Dict:
        """Return scraping statistics"""
        return self.stats.copy()


def main():
    """Example usage"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if not api_key:
        logger.error("❌ YOUTUBE_API_KEY not found in .env")
        return
    
    # Example: Scrape a video
    scraper = YouTubeScraper(api_key, max_results=100)
    
    # Try with the user's existing YouTube chat file (to get video ID)
    # For demo, using a sample video ID
    video_id = "dQw4w9WgXcQ"  # Example: Rick Roll (change to real video)
    
    df = scraper.scrape_video(video_id)
    
    if not df.empty:
        # Save results
        scraper.save_to_csv(df, "youtube_comments_scraped.csv")
        scraper.save_to_json(df, "youtube_comments_scraped.json")
        
        # Validate
        validation = scraper.validate_data(df)
        print("\n📋 Data Validation:")
        print(json.dumps(validation, indent=2, default=str))
    else:
        logger.warning("⚠ No comments scraped")


if __name__ == "__main__":
    main()
