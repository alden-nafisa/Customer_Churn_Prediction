"""
Configuration settings for NLP system (100% Local Inference)
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import torch

# Load environment variables
load_dotenv()

# ==================== Paths ====================
PROJECT_ROOT = Path(__file__).parent.parent
NLP_DIR = PROJECT_ROOT / "nlp"
NLP_CACHE_DIR = NLP_DIR / "cache"
NLP_MODELS_DIR = NLP_DIR / "models"
NLP_DATA_DIR = NLP_DIR / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

for directory in [NLP_CACHE_DIR, NLP_MODELS_DIR, NLP_DATA_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ==================== Local NLP Models ====================
# Sentiment Model (IndoBERT Fine-tuned for 3-class sentiment)
SENTIMENT_MODEL_NAME = "mdhugol/indonesia-bert-sentiment-classification"

# Summarization Model (BART Multilingual or IndoBERT-to-IndoBERT)
SUMMARIZATION_MODEL_NAME = "cahya/bert2bert-indonesian-summarization"

# Auto-detect Hardware: Use GPU (CUDA) if available, otherwise CPU
DEVICE = 0 if torch.cuda.is_available() else -1

# ==================== Feature Flags ====================
ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CACHE_EXPIRY_HOURS = 24

# API Key YouTube tetap ada jika Anda menggunakan Scraper API asli
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")