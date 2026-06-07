"""
Sentiment Analysis Inference Module
Uses Local IndoBERT Pipeline (HuggingFace) instead of APIs
"""

import logging
from typing import Dict, Optional, Any, List
import pandas as pd
from transformers import pipeline
from nlp_config import SENTIMENT_MODEL_NAME, DEVICE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentModel:
    def __init__(self):
        self.model_type = "indobert"
        logger.info(f"Loading local sentiment model: {SENTIMENT_MODEL_NAME}...")
        self.analyzer: Optional[Any] = None
        try:
            self.analyzer = pipeline(
                "text-classification",  # Menggunakan text-classification untuk Pylance compatibility
                model=SENTIMENT_MODEL_NAME, 
                tokenizer=SENTIMENT_MODEL_NAME,
                device=DEVICE,
                truncation=True,
                max_length=512
            )
            logger.info("✓ Local Sentiment model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load sentiment model: {e}")
            self.analyzer = None

    def predict_single(self, text: str) -> Dict[str, Any]:
        if not self.analyzer or not text or not str(text).strip():
            return {'text': text, 'sentiment': 'Neutral', 'confidence': 0.0}

        try:
            safe_text = str(text)[:1500]
            result = self.analyzer(safe_text)[0]
            
            raw_label = result['label'].upper()
            confidence = round(float(result['score']), 4)
            
            if raw_label in ['POSITIVE', 'POSITIF', 'LABEL_2']:
                sentiment = 'Positive'
            elif raw_label in ['NEGATIVE', 'NEGATIF', 'LABEL_0']:
                sentiment = 'Negative'
            else:
                sentiment = 'Neutral'

            return {
                'text': text,
                'sentiment': sentiment,
                'confidence': confidence,
            }
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {'text': text, 'sentiment': 'Neutral', 'confidence': 0.0}

    def predict_batch(self, texts: list) -> list:
        """Fungsi pembantu untuk memproses list teks secara berurutan"""
        if not texts:
            return []
        return [self.predict_single(str(t)) for t in texts]


def predict_sentiment(text: str, model: Optional[SentimentModel] = None) -> Dict[str, Any]:
    if model is None:
        model = SentimentModel()
    return model.predict_single(text)

if __name__ == "__main__":
    model = SentimentModel()
    samples = [
        "aplikasi ini sangat membantu dan keren banget!",
        "jaringan selalu putus, sangat mengecewakan",
        "hari ini cuaca cukup cerah"
    ]
    for s in samples:
        print(predict_sentiment(s, model))