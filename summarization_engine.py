import logging
from typing import Dict, Optional
import pandas as pd
# Menghapus 'pipeline' karena tidak dipakai
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from nlp_config import SUMMARIZATION_MODEL_NAME, DEVICE, ENABLE_CACHING

# Saya ubah Dummy cache menjadi in-memory cache sederhana agar benar-benar berfungsi
class SummarizationCache:
    def __init__(self):
        self._cache = {}

    def get(self, text: str) -> Optional[str]:
        return self._cache.get(text)
        
    def set(self, text: str, summary: str):
        self._cache[text] = summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndoBERTSummarizationEngine:
    def __init__(self):
        self.use_cache = ENABLE_CACHING
        self.cache = SummarizationCache() if self.use_cache else None
        
        # Inisialisasi awal dengan None untuk mencegah AttributeError jika gagal load
        self.tokenizer = None
        self.model = None
        
        logger.info(f"Loading local summarization model: {SUMMARIZATION_MODEL_NAME}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(SUMMARIZATION_MODEL_NAME)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(SUMMARIZATION_MODEL_NAME).to(DEVICE)
            logger.info("Summarization model loaded successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to load summarizer: {e}")

    def summarize_text(self, text: str) -> str:
        # Cek apakah model berhasil dimuat
        if self.model is None or self.tokenizer is None:
            return "Sistem gagal membuat ringkasan karena model tidak tersedia."

        if not text or not str(text).strip():
            return ""
            
        if self.use_cache and self.cache:
            cached = self.cache.get(text)
            if cached:
                return cached
                
        try:
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

        # PERBAIKAN LOGIKA: Wajib cek kolom 'sentiment' dulu, jika tidak ada, proses tidak bisa dilanjut
        if 'sentiment' not in comments_df.columns:
            return {"Error": "Dataframe missing required 'sentiment' column"}

        # Penentuan kolom pesan
        msg_col = 'comment'
        if 'comment' not in comments_df.columns:
            if 'message' in comments_df.columns:
                msg_col = 'message'
            else:
                return {"Error": "Dataframe missing required message/comment columns"}

        for sentiment in ['Positive', 'Negative', 'Neutral']:
            texts = comments_df[comments_df['sentiment'] == sentiment][msg_col].dropna().astype(str).tolist()
            if texts:
                # PERBAIKAN: Mengurangi dari 30 menjadi 15 komentar
                # Alasan: Batas token model umumnya 512. Jika 30 komentar digabung, kemungkinan besar token akan terpotong (truncated)
                # sehingga komentar di urutan belakang tidak ikut diringkas.
                combined_text = " . ".join(texts[:15]) 
                summary = self.summarize_text(combined_text)
                results[sentiment] = summary if summary else "Tidak ada ringkasan."
            else:
                results[sentiment] = "Tidak ada data."
                
        return results

def create_summarizer() -> IndoBERTSummarizationEngine:
    """Factory function untuk membuat instansiasi engine."""
    return IndoBERTSummarizationEngine()