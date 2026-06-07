import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from nlp_config import SUMMARIZATION_MODEL_NAME, DEVICE, ENABLE_CACHING, NLP_CACHE_DIR, CACHE_EXPIRY_HOURS

# Mendefinisikan class dummy SummarizationCache agar tidak undefined
class SummarizationCache:
    def get(self, text: str) -> Optional[str]:
        return None
        
    def set(self, text: str, summary: str):
        pass

logging.basicConfig(level=logging.INFO)
# Mendefinisikan logger yang tadinya undefined
logger = logging.getLogger(__name__)

class IndoBERTSummarizationEngine:
    def __init__(self):
        self.use_cache = ENABLE_CACHING
        self.cache = SummarizationCache() if self.use_cache else None
        
        logger.info(f"Loading local summarization model: {SUMMARIZATION_MODEL_NAME}...")
        try:
            # Mengganti pipeline dengan pemanggilan arsitektur yang eksplisit
            self.tokenizer = AutoTokenizer.from_pretrained(SUMMARIZATION_MODEL_NAME)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(SUMMARIZATION_MODEL_NAME).to(DEVICE)
        except Exception as e:
            logger.error(f"❌ Failed to load summarizer: {e}")

    def summarize_text(self, text: str) -> str:
        if not text or not str(text).strip():
            return ""
            
        if self.use_cache and self.cache:
            cached = self.cache.get(text)
            if cached:
                return cached
                
        try:
            # Proses text-to-summary secara manual
            inputs = self.tokenizer(text, return_tensors="pt", max_length=512, truncation=True).to(DEVICE)
            
            outputs = self.model.generate(
                inputs["input_ids"],
                max_length=150,
                min_length=40,
                length_penalty=2.0,
                num_beams=4,
                early_stopping=True
            )
            
            summary_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            if self.use_cache and self.cache:
                self.cache.set(text, summary_text)
            
            return summary_text
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return "Sistem Gagal membuat ringkasan karena batas memori."

    def summarize_by_sentiment(self, comments_df: pd.DataFrame, video_id: Optional[str] = None, video_title: Optional[str] = None) -> Dict[str, str]:
        results = {}
        if comments_df is None or comments_df.empty:
            return {"Error": "Dataframe is empty or None"}

        if 'sentiment' not in comments_df.columns or 'comment' not in comments_df.columns:
            msg_col = 'message' if 'message' in comments_df.columns else 'comment'
            if msg_col not in comments_df.columns: 
                return {"Error": "Dataframe missing required columns"}
        else:
            msg_col = 'comment'

        for sentiment in ['Positive', 'Negative', 'Neutral']:
            texts = comments_df[comments_df['sentiment'] == sentiment][msg_col].dropna().astype(str).tolist()
            if texts:
                combined_text = " . ".join(texts[:30])
                summary = self.summarize_text(combined_text)
                results[sentiment] = summary if summary else "Tidak ada ringkasan."
            else:
                results[sentiment] = "Tidak ada data."
                
        return results

def create_summarizer() -> IndoBERTSummarizationEngine:
    """Factory function untuk membuat instansiasi engine."""
    return IndoBERTSummarizationEngine()