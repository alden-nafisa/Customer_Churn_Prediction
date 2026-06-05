"""
Local IndoBERT-based Summarization Engine
Replaces cloud-based Gemini API with local inference
Supports both extractive and abstractive summarization
"""

import logging
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check GPU availability
DEVICE = 0 if torch.cuda.is_available() else -1
if DEVICE == 0:
    logger.info("✅ GPU available - using CUDA")
else:
    logger.info("💻 CPU mode - no GPU detected")


class SummarizationCache:
    """
    Smart caching for summaries to avoid re-computation
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
    
    def _get_cache_key(self, text_hash: str, model_type: str) -> str:
        """Generate cache key"""
        key = f"{text_hash}_{model_type}"
        return hashlib.md5(key.encode()).hexdigest()[:16]
    
    def get(self, text: str, model_type: str = "indobert") -> Optional[str]:
        """Retrieve cached summary"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_key = self._get_cache_key(text_hash, model_type)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check expiry
            created_at = datetime.fromisoformat(data['created_at'])
            if datetime.now() - created_at > timedelta(hours=self.expiry_hours):
                logger.debug(f"⏰ Cache expired")
                cache_file.unlink()
                return None
            
            logger.debug(f"✓ Cache hit")
            return data['summary']
        
        except Exception as e:
            logger.warning(f"⚠ Cache retrieval failed: {e}")
            return None
    
    def set(self, text: str, summary: str, model_type: str = "indobert"):
        """Store summary in cache"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_key = self._get_cache_key(text_hash, model_type)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        data = {
            'text_hash': text_hash,
            'model_type': model_type,
            'summary': summary,
            'created_at': datetime.now().isoformat(),
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"✓ Cached summary")
        except Exception as e:
            logger.warning(f"⚠ Cache write failed: {e}")


class IndoBERTSummarizationEngine:
    """
    Generate summaries using local IndoBERT models
    Replaces GeminiSummarizationEngine entirely
    """
    
    def __init__(self, cache_enabled: bool = True, cache_dir: Path = None):
        """
        Initialize summarization engine
        
        Args:
            cache_enabled: Enable result caching
            cache_dir: Cache directory path
        """
        self.cache_enabled = cache_enabled
        self.cache = SummarizationCache(cache_dir) if cache_enabled else None
        
        # Load models
        self.sentiment_classifier = None
        self.summarizer = None
        self._load_models()
    
    def _load_models(self):
        """Load IndoBERT and summarization models"""
        try:
            logger.info("Loading IndoBERT sentiment classifier...")
            # Use IndoBERT for sentiment classification
            self.sentiment_classifier = pipeline(
                "text-classification",
                model="indobert-base-p1",
                device=DEVICE,
                truncation=True,
                max_length=512
            )
            logger.info("✓ IndoBERT classifier loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load sentiment classifier: {e}")
            self.sentiment_classifier = None
        
        try:
            logger.info("Loading multilingual summarization model...")
            # Use BART for multilingual summarization (works well with Indonesian)
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-multilingual",
                device=DEVICE,
                truncation=True,
                max_length=1024
            )
            logger.info("✓ BART multilingual summarizer loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load summarizer: {e}")
            self.summarizer = None
    
    def summarize_text(self, text: str, max_length: int = 150, 
                      min_length: int = 50) -> Optional[str]:
        """
        Generate summary for single text
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length
            min_length: Minimum summary length
        
        Returns:
            Summary string or None
        """
        if not text or not self.summarizer:
            return None
        
        # Check cache
        if self.cache_enabled:
            cached = self.cache.get(text, "indobert_summarizer")
            if cached:
                return cached
        
        try:
            logger.debug(f"Summarizing text ({len(text)} chars)...")
            
            # Truncate if too long
            if len(text) > 1024:
                text = text[:1024]
            
            # Generate summary
            summary = self.summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )
            
            if summary and len(summary) > 0:
                summary_text = summary[0]['summary_text']
                
                # Cache result
                if self.cache_enabled:
                    self.cache.set(text, summary_text, "indobert_summarizer")
                
                return summary_text
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Summarization failed: {e}")
            return None
    
    def summarize_grouped(self, texts: List[str], group_label: str = "Group",
                         max_length: int = 200) -> Dict[str, any]:
        """
        Generate summary for grouped texts (e.g., by sentiment)
        
        Args:
            texts: List of texts to summarize
            group_label: Label for the group (e.g., "Positive", "Negative")
            max_length: Maximum summary length
        
        Returns:
            Dict with summary and metadata
        """
        if not texts:
            return {
                'group': group_label,
                'count': 0,
                'summary': None,
                'error': 'No texts provided'
            }
        
        try:
            # Combine texts with separators
            combined_text = " | ".join(texts[:50])  # Limit to first 50 texts
            
            if len(combined_text) < 50:
                # Too short to summarize, return first text
                summary = texts[0]
            else:
                summary = self.summarize_text(combined_text, max_length=max_length)
            
            return {
                'group': group_label,
                'count': len(texts),
                'summary': summary or texts[0],  # Fallback to first text
                'sample_texts': texts[:3],  # First 3 texts as samples
                'source': 'indobert'
            }
        
        except Exception as e:
            logger.error(f"❌ Grouped summarization failed: {e}")
            return {
                'group': group_label,
                'count': len(texts),
                'summary': None,
                'error': str(e)
            }
    
    def get_sentiment_summary(self, comments_df: pd.DataFrame) -> Dict[str, str]:
        """
        Generate summaries grouped by sentiment
        
        Args:
            comments_df: DataFrame with 'comment' and 'sentiment' columns
        
        Returns:
            Dict with summaries for each sentiment
        """
        results = {}
        
        for sentiment in ['Positive', 'Negative', 'Neutral']:
            # Filter comments by sentiment
            sentiment_comments = comments_df[
                comments_df['sentiment'].str.strip() == sentiment
            ]['comment'].tolist()
            
            if sentiment_comments:
                summary_result = self.summarize_grouped(
                    sentiment_comments,
                    group_label=sentiment,
                    max_length=150
                )
                results[sentiment] = summary_result['summary']
            else:
                results[sentiment] = None
        
        return results
    
    def batch_summarize(self, texts: List[str], 
                       batch_size: int = 32) -> List[str]:
        """
        Summarize multiple texts in batches
        
        Args:
            texts: List of texts to summarize
            batch_size: Number of texts to process at once
        
        Returns:
            List of summaries
        """
        summaries = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}")
            
            for text in batch:
                summary = self.summarize_text(text)
                summaries.append(summary)
        
        return summaries
    
    def health_check(self) -> Dict[str, bool]:
        """Check if models are loaded"""
        return {
            'sentiment_classifier': self.sentiment_classifier is not None,
            'summarizer': self.summarizer is not None,
            'cache_enabled': self.cache_enabled,
            'device': 'GPU' if DEVICE == 0 else 'CPU'
        }


# Convenience functions
def create_summarizer(cache_enabled: bool = True) -> IndoBERTSummarizationEngine:
    """Create summarization engine"""
    return IndoBERTSummarizationEngine(cache_enabled=cache_enabled)


def summarize(text: str, engine: IndoBERTSummarizationEngine = None) -> Optional[str]:
    """Quick summarize function"""
    if engine is None:
        engine = create_summarizer()
    return engine.summarize_text(text)


# Example usage
if __name__ == "__main__":
    engine = create_summarizer()
    
    print("=" * 70)
    print("INDOBERT SUMMARIZATION ENGINE - DEMO")
    print("=" * 70)
    print(f"Health: {engine.health_check()}\n")
    
    # Test texts
    test_texts = [
        "Produk ini sangat bagus, kualitasnya luar biasa, saya sangat puas dengan pembelian ini. Pengiriman cepat dan layanan pelanggan sangat responsif.",
        "Konten video ini menghibur dan edukatif, saya belajar banyak hal baru. Presenter sangat profesional dan penjelasannya mudah dipahami.",
        "Sangat kecewa dengan kualitas produk, tidak sesuai ekspektasi. Pengiriman lambat dan komunikasi kurang baik."
    ]
    
    print("Sample Summarizations:")
    for i, text in enumerate(test_texts, 1):
        summary = summarize(text, engine)
        print(f"\nText {i}:")
        print(f"  Original ({len(text)} chars): {text[:80]}...")
        print(f"  Summary ({len(summary) if summary else 0} chars): {summary}")
    
    print("\n" + "=" * 70)
