"""
Configuration settings for NLP system
Loads from .env file for secure credential management
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==================== Paths ====================
PROJECT_ROOT = Path(__file__).parent.parent
NLP_DIR = PROJECT_ROOT / "nlp"
NLP_CACHE_DIR = NLP_DIR / "cache"
NLP_MODELS_DIR = NLP_DIR / "models"
NLP_DATA_DIR = NLP_DIR / "data"
NLP_TESTS_DIR = NLP_DIR / "tests"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "nlp"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
for directory in [NLP_CACHE_DIR, NLP_MODELS_DIR, NLP_DATA_DIR, NLP_TESTS_DIR, ARTIFACTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ==================== API Keys ====================
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY not found in .env file")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# ==================== YouTube Scraper Settings ====================
YOUTUBE_MAX_RESULTS = int(os.getenv("YOUTUBE_MAX_RESULTS", 1000))
YOUTUBE_SCRAPER_TIMEOUT = int(os.getenv("YOUTUBE_SCRAPER_TIMEOUT", 30))
YOUTUBE_RETRY_ATTEMPTS = int(os.getenv("YOUTUBE_RETRY_ATTEMPTS", 3))

# ==================== Model Settings ====================
INDOBERT_MODEL_NAME = os.getenv("INDOBERT_MODEL_NAME", "indobert-base-p1")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 32))
MAX_COMMENTS_PROCESS = int(os.getenv("MAX_COMMENTS_PROCESS", 10000))
SENTIMENT_CLASSES = ["Positive", "Neutral", "Negative"]
NUM_CLASSES = len(SENTIMENT_CLASSES)

# ==================== Gemini API Settings ====================
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro")
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", 1000))
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", 0.7))

# ==================== Feature Flags ====================
ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"
ENABLE_SENTIMENT_SURGE_DETECTION = os.getenv("ENABLE_SENTIMENT_SURGE_DETECTION", "true").lower() == "true"
ENABLE_GPU_INFERENCE = os.getenv("ENABLE_GPU_INFERENCE", "false").lower() == "true"

# ==================== Logging ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / os.getenv("LOG_FILE", "nlp_system.log")

# ==================== Data Processing ====================
EMOJI_MAPPING_FILE = NLP_DATA_DIR / "emoji_mappings.json"
SLANG_DICTIONARY_FILE = NLP_DATA_DIR / "slang_dictionary.json"

# ==================== Cache Settings ====================
CACHE_EXPIRY_HOURS = 24
MAX_CACHE_SIZE_MB = 500

# ==================== Timeline Analysis ====================
TIMELINE_BIN_SECONDS = 30
SENTIMENT_SPIKE_THRESHOLD = 2.0

# ==================== Validation ====================
MIN_COMMENTS_FOR_ANALYSIS = 10
MIN_MESSAGE_LENGTH = 1
MAX_MESSAGE_LENGTH = 5000

print(f"[OK] NLP Configuration Loaded | Project: {PROJECT_ROOT} | APIs: {'OK' if YOUTUBE_API_KEY and GEMINI_API_KEY else 'MISSING'}")
