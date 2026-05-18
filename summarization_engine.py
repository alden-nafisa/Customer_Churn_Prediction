"""
Gemini-based Summarization Engine
Groups comments by sentiment and generates natural language summaries
"""

import logging
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
import google.generativeai as genai
from nlp_config import GEMINI_API_KEY, GEMINI_MODEL_NAME, GEMINI_MAX_TOKENS, GEMINI_TEMPERATURE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)


class SummarizationCache:
    """
    Smart caching for summaries to avoid API over-usage
    """
    
    def __init__(self, cache_dir: Path = None, expiry_hours: int = 24):
        """
        Initialize cache
        
        Args:
            cache_dir: Directory for cache files
            expiry_hours: Cache expiration time in hours
        """
        if cache_dir is None:
            cache_dir = Path(__file__).parent / "nlp" / "cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.expiry_hours = expiry_hours
        
        logger.info(f"✓ Cache initialized at {self.cache_dir}")
    
    def _get_cache_key(self, video_id: str, sentiment: str) -> str:
        """Generate cache key from video ID and sentiment"""
        key = f"{video_id}_{sentiment}"
        return hashlib.md5(key.encode()).hexdigest()[:16]
    
    def get(self, video_id: str, sentiment: str) -> Optional[str]:
        """Retrieve cached summary"""
        cache_key = self._get_cache_key(video_id, sentiment)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check expiry
            created_at = datetime.fromisoformat(data['created_at'])
            if datetime.now() - created_at > timedelta(hours=self.expiry_hours):
                logger.info(f"⏰ Cache expired for {video_id}/{sentiment}")
                cache_file.unlink()
                return None
            
            logger.info(f"✓ Cache hit for {video_id}/{sentiment}")
            return data['summary']
        
        except Exception as e:
            logger.warning(f"⚠ Cache retrieval failed: {e}")
            return None
    
    def set(self, video_id: str, sentiment: str, summary: str):
        """Store summary in cache"""
        cache_key = self._get_cache_key(video_id, sentiment)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        data = {
            'video_id': video_id,
            'sentiment': sentiment,
            'summary': summary,
            'created_at': datetime.now().isoformat(),
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ Cached summary for {video_id}/{sentiment}")
        except Exception as e:
            logger.warning(f"⚠ Cache write failed: {e}")


class GeminiSummarizationEngine:
    """
    Generate summaries using Gemini API
    """
    
    def __init__(self, cache_dir: Path = None, use_cache: bool = True):
        """
        Initialize Gemini summarization engine
        
        Args:
            cache_dir: Cache directory for summaries
            use_cache: Enable caching
        """
        self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        self.use_cache = use_cache
        self.cache = SummarizationCache(cache_dir) if use_cache else None
        self.stats = {
            'api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'tokens_used': 0,
        }
        
        logger.info(f"✓ Gemini engine initialized (Model: {GEMINI_MODEL_NAME})")
    
    def summarize_comments(self, 
                          comments: List[str],
                          sentiment: str,
                          video_title: str = None,
                          max_length: int = 150) -> str:
        """
        Generate summary for group of comments
        
        Args:
            comments: List of comments to summarize
            sentiment: Sentiment label (Positive, Neutral, Negative)
            video_title: Title of video for context
            max_length: Maximum summary length in words
        
        Returns:
            Natural language summary
        """
        if not comments:
            return f"No {sentiment.lower()} comments"
        
        # Create prompt
        comments_text = "\n".join(f"- {c}" for c in comments[:20])  # Limit to 20 for context
        
        context = f"Video: {video_title}\n" if video_title else ""
        
        prompt = f"""Analyze these {sentiment.lower()} YouTube comments and create a concise summary in Indonesian.
Focus on the main themes, issues, or praise mentioned.

{context}
Comments:
{comments_text}

Create a {max_length}-word summary that captures the key sentiment and themes. Be specific and mention actual topics from comments.
Start with the sentiment tone (e.g., "Mayoritas penonton..." or "Sebagian besar penonton...")"""
        
        try:
            # Call Gemini API
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'max_output_tokens': GEMINI_MAX_TOKENS,
                    'temperature': GEMINI_TEMPERATURE,
                }
            )
            
            self.stats['api_calls'] += 1
            summary = response.text.strip()
            
            logger.info(f"✓ Generated summary for {sentiment} sentiment ({len(summary)} chars)")
            return summary
        
        except Exception as e:
            logger.error(f"❌ Gemini API error: {e}")
            return f"Could not generate summary: {str(e)}"
    
    def summarize_by_sentiment(self, df: pd.DataFrame, 
                              video_id: str = None,
                              video_title: str = None) -> Dict[str, str]:
        """
        Generate summaries for each sentiment group
        
        Args:
            df: DataFrame with 'message' and 'sentiment' columns
            video_id: Video ID for caching
            video_title: Video title for context
        
        Returns:
            Dict with sentiment -> summary mapping
        """
        if 'sentiment' not in df.columns or 'message' not in df.columns:
            logger.error("DataFrame must have 'sentiment' and 'message' columns")
            return {}
        
        summaries = {}
        
        # Group by sentiment
        for sentiment in ['Positive', 'Neutral', 'Negative']:
            sentiment_df = df[df['sentiment'] == sentiment]
            
            if len(sentiment_df) == 0:
                summaries[sentiment] = f"No {sentiment.lower()} comments"
                continue
            
            # Check cache first
            if self.use_cache and video_id:
                cached = self.cache.get(video_id, sentiment)
                if cached:
                    summaries[sentiment] = cached
                    self.stats['cache_hits'] += 1
                    continue
            
            self.stats['cache_misses'] += 1
            
            # Generate summary
            comments = sentiment_df['message'].tolist()
            summary = self.summarize_comments(
                comments,
                sentiment,
                video_title
            )
            
            summaries[sentiment] = summary
            
            # Cache it
            if self.use_cache and video_id:
                self.cache.set(video_id, sentiment, summary)
        
        return summaries
    
    def create_session_summary(self, df: pd.DataFrame,
                              video_title: str = None,
                              video_channel: str = None) -> str:
        """
        Create overall session summary combining all sentiments
        
        Args:
            df: DataFrame with comments and sentiments
            video_title: Video title
            video_channel: Channel name
        
        Returns:
            Overall session summary
        """
        if df.empty:
            return "No comments to summarize"
        
        # Calculate statistics
        total_comments = len(df)
        sentiment_counts = df['sentiment'].value_counts().to_dict()
        sentiment_pcts = {k: f"{v/total_comments*100:.0f}%" 
                         for k, v in sentiment_counts.items()}
        
        # Get top keywords
        from collections import Counter
        all_words = ' '.join(df['message']).lower().split()
        top_keywords = [word for word, _ in Counter(all_words).most_common(10)]
        
        # Get sentiment-specific summaries
        summaries = self.summarize_by_sentiment(df, video_title=video_title)
        
        # Create overall summary
        sentiment_summary = "\n".join([
            f"- {sentiment} ({sentiment_pcts.get(sentiment, '0%')}): {summaries[sentiment]}"
            for sentiment in ['Positive', 'Neutral', 'Negative']
        ])
        
        overall_prompt = f"""Based on these sentiment summaries from a YouTube video, create a brief overall session summary.

Video: {video_title or 'Unknown'}
Channel: {video_channel or 'Unknown'}
Total Comments: {total_comments}

Sentiment Summaries:
{sentiment_summary}

Top Keywords: {', '.join(top_keywords)}

Create a 2-3 sentence summary that gives the overall impression of viewer response to this video."""
        
        try:
            response = self.model.generate_content(
                overall_prompt,
                generation_config={
                    'max_output_tokens': GEMINI_MAX_TOKENS,
                    'temperature': GEMINI_TEMPERATURE,
                }
            )
            
            self.stats['api_calls'] += 1
            summary = response.text.strip()
            
            logger.info(f"✓ Generated overall session summary")
            return summary
        
        except Exception as e:
            logger.error(f"❌ Failed to create session summary: {e}")
            return "Could not generate session summary"
    
    def get_stats(self) -> Dict:
        """Get API usage statistics"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {k: 0 for k in self.stats}


# Convenience functions
def summarize_comments(comments: List[str], sentiment: str) -> str:
    """Quick summarization"""
    engine = GeminiSummarizationEngine()
    return engine.summarize_comments(comments, sentiment)


# Example usage
if __name__ == "__main__":
    # Sample data
    sample_df = pd.DataFrame({
        'message': [
            'keren banget! suka sekali',
            'bagus banget kontennya',
            'mantap jiwa',
            'lumayan sih',
            'biasa aja',
            'jelek bet',
            'sangat mengecewakan',
            'buruk banget',
        ],
        'sentiment': [
            'Positive', 'Positive', 'Positive',
            'Neutral', 'Neutral',
            'Negative', 'Negative', 'Negative',
        ]
    })
    
    print("=" * 60)
    print("GEMINI SUMMARIZATION - DEMO")
    print("=" * 60)
    
    # Initialize engine
    engine = GeminiSummarizationEngine(use_cache=True)
    
    # Generate summaries by sentiment
    print("\nSummaries by Sentiment:")
    summaries = engine.summarize_by_sentiment(
        sample_df,
        video_id="test_video_123",
        video_title="Sample Video"
    )
    
    for sentiment, summary in summaries.items():
        print(f"\n{sentiment}:")
        print(f"  {summary}")
    
    # Overall session summary
    print("\nOverall Session Summary:")
    overall = engine.create_session_summary(
        sample_df,
        video_title="Sample Video",
        video_channel="Sample Channel"
    )
    print(f"  {overall}")
    
    print("\n" + "=" * 60)
    print("Stats:")
    print(engine.get_stats())
    print("=" * 60)
