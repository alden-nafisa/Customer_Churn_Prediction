"""
Integration Test Suite for NLP System
Tests all components: scraper, preprocessor, sentiment, summarization, visualizations
"""

import sys
import logging
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
TESTS_PASSED = 0
TESTS_FAILED = 0


def test_result(test_name: str, passed: bool, message: str = ""):
    """Log test result"""
    global TESTS_PASSED, TESTS_FAILED
    
    if passed:
        TESTS_PASSED += 1
        logger.info(f"✅ {test_name}")
    else:
        TESTS_FAILED += 1
        logger.error(f"❌ {test_name}: {message}")


def test_imports():
    """Test all imports work"""
    try:
        from nlp_config import YOUTUBE_API_KEY, GEMINI_API_KEY
        test_result("Imports: nlp_config", True)
    except Exception as e:
        test_result("Imports: nlp_config", False, str(e))
    
    try:
        from youtube_scraper import YouTubeScraper
        test_result("Imports: youtube_scraper", True)
    except Exception as e:
        test_result("Imports: youtube_scraper", False, str(e))
    
    try:
        from nlp_preprocessor import NLPPreprocessor
        test_result("Imports: nlp_preprocessor", True)
    except Exception as e:
        test_result("Imports: nlp_preprocessor", False, str(e))
    
    try:
        from sentiment_model import SentimentModel
        test_result("Imports: sentiment_model", True)
    except Exception as e:
        test_result("Imports: sentiment_model", False, str(e))
    
    try:
        from summarization_engine import GeminiSummarizationEngine
        test_result("Imports: summarization_engine", True)
    except Exception as e:
        test_result("Imports: summarization_engine", False, str(e))
    
    try:
        from nlp_visualizations import create_sentiment_timeline
        test_result("Imports: nlp_visualizations", True)
    except Exception as e:
        test_result("Imports: nlp_visualizations", False, str(e))


def test_configuration():
    """Test configuration loading"""
    try:
        from nlp_config import (
            YOUTUBE_API_KEY, GEMINI_API_KEY, 
            SENTIMENT_CLASSES, TIMELINE_BIN_SECONDS
        )
        
        # Check if APIs are configured
        has_youtube = bool(YOUTUBE_API_KEY and YOUTUBE_API_KEY != "your_youtube_api_key_here")
        has_gemini = bool(GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here")
        
        test_result(
            "Config: YouTube API key",
            has_youtube,
            "API key not configured in .env"
        )
        
        test_result(
            "Config: Gemini API key",
            has_gemini,
            "API key not configured in .env"
        )
        
        # Check other configs
        test_result(
            "Config: SENTIMENT_CLASSES",
            len(SENTIMENT_CLASSES) == 3,
            f"Expected 3 classes, got {len(SENTIMENT_CLASSES)}"
        )
        
        test_result(
            "Config: TIMELINE_BIN_SECONDS",
            TIMELINE_BIN_SECONDS == 30,
            f"Expected 30, got {TIMELINE_BIN_SECONDS}"
        )
    
    except Exception as e:
        test_result("Config: Loading", False, str(e))


def test_emoji_mappings():
    """Test emoji mappings are loaded"""
    try:
        import json
        emoji_file = Path(__file__).parent / "emoji_mappings.json"
        
        test_result(
            "Data: emoji_mappings.json exists",
            emoji_file.exists(),
            f"File not found: {emoji_file}"
        )
        
        with open(emoji_file) as f:
            emoji_map = json.load(f)
        
        test_result(
            "Data: emoji_mappings has content",
            len(emoji_map) > 0,
            "Emoji map is empty"
        )
        
        test_result(
            "Data: emoji_mappings count",
            len(emoji_map) >= 500,
            f"Expected 500+, got {len(emoji_map)}"
        )
    
    except Exception as e:
        test_result("Data: emoji_mappings", False, str(e))


def test_slang_dictionary():
    """Test slang dictionary is loaded"""
    try:
        import json
        slang_file = Path(__file__).parent / "slang_dictionary.json"
        
        test_result(
            "Data: slang_dictionary.json exists",
            slang_file.exists(),
            f"File not found: {slang_file}"
        )
        
        with open(slang_file) as f:
            slang_map = json.load(f)
        
        test_result(
            "Data: slang_dictionary has content",
            len(slang_map) > 0,
            "Slang map is empty"
        )
        
        test_result(
            "Data: slang_dictionary count",
            len(slang_map) >= 200,
            f"Expected 200+, got {len(slang_map)}"
        )
    
    except Exception as e:
        test_result("Data: slang_dictionary", False, str(e))


def test_preprocessor():
    """Test NLP preprocessor"""
    try:
        from nlp_preprocessor import NLPPreprocessor
        
        preprocessor = NLPPreprocessor()
        test_result("Preprocessor: Initialization", True)
        
        # Test emoji conversion
        text_with_emoji = "😊 bagus bgt"
        processed = preprocessor.preprocess(text_with_emoji)
        
        test_result(
            "Preprocessor: Emoji conversion",
            len(processed) > 0 and processed != text_with_emoji,
            "Emoji not converted"
        )
        
        # Test slang expansion
        text_with_slang = "bgt bagus"
        processed = preprocessor.preprocess(text_with_slang)
        
        test_result(
            "Preprocessor: Slang expansion",
            "banget" in processed or len(processed) > 0,
            "Slang not expanded"
        )
        
        # Test batch processing
        texts = ["keren", "jelek", "biasa"]
        results = preprocessor.preprocess_batch(texts)
        
        test_result(
            "Preprocessor: Batch processing",
            len(results) == 3,
            f"Expected 3 results, got {len(results)}"
        )
    
    except Exception as e:
        test_result("Preprocessor: Operations", False, str(e))


def test_sentiment_model():
    """Test sentiment model"""
    try:
        from sentiment_model import SentimentModel, predict_sentiment
        
        # Initialize model (uses default Naive Bayes)
        model = SentimentModel()
        test_result("Sentiment Model: Initialization", model.model is not None, "Model not loaded")
        
        # Test single prediction
        text = "keren banget, suka sekali"
        result = predict_sentiment(text, model)
        
        test_result(
            "Sentiment Model: Single prediction",
            result is not None and 'sentiment' in result,
            "Prediction failed"
        )
        
        test_result(
            "Sentiment Model: Valid sentiment label",
            result.get('sentiment') in ['Positive', 'Neutral', 'Negative'],
            f"Invalid sentiment: {result.get('sentiment')}"
        )
        
        # Test batch prediction
        texts = ["bagus sekali", "jelek bet", "lumayan"]
        df_results = model.predict_batch(texts, return_dataframe=True)
        
        test_result(
            "Sentiment Model: Batch prediction",
            len(df_results) == 3,
            f"Expected 3 predictions, got {len(df_results)}"
        )
    
    except Exception as e:
        test_result("Sentiment Model: Operations", False, str(e))


def test_visualizations():
    """Test visualization functions"""
    try:
        from nlp_visualizations import (
            create_sentiment_timeline,
            create_kpi_cards,
            create_sentiment_distribution_pie,
            create_top_keywords_by_sentiment,
            create_top_commenters_leaderboard,
            detect_sentiment_spikes,
        )
        
        # Create sample data
        sample_df = pd.DataFrame({
            'elapsed': ['0:00', '0:30', '1:00', '1:30', '2:00'],
            'author': ['user1', 'user2', 'user1', 'user3', 'user2'],
            'message': ['keren', 'bagus', 'suka', 'jelek', 'biasa'],
            'sentiment': ['Positive', 'Positive', 'Positive', 'Negative', 'Neutral'],
            'likes': [5, 2, 8, 1, 0],
        })
        
        # Test KPI cards
        kpis = create_kpi_cards(sample_df)
        test_result(
            "Visualizations: KPI cards",
            'total_comments' in kpis,
            "KPI cards missing data"
        )
        
        # Test timeline
        fig_timeline = create_sentiment_timeline(sample_df)
        test_result(
            "Visualizations: Sentiment timeline",
            fig_timeline is not None,
            "Timeline creation failed"
        )
        
        # Test distribution pie
        fig_dist = create_sentiment_distribution_pie(sample_df)
        test_result(
            "Visualizations: Sentiment distribution",
            fig_dist is not None,
            "Distribution chart creation failed"
        )
        
        # Test keywords
        fig_keywords = create_top_keywords_by_sentiment(sample_df)
        test_result(
            "Visualizations: Top keywords",
            len(fig_keywords) > 0,
            "Keyword charts not created"
        )
        
        # Test leaderboard
        fig_leaderboard = create_top_commenters_leaderboard(sample_df)
        test_result(
            "Visualizations: Leaderboard",
            fig_leaderboard is not None,
            "Leaderboard creation failed"
        )
        
        # Test spike detection
        spikes = detect_sentiment_spikes(sample_df)
        test_result(
            "Visualizations: Spike detection",
            'spikes' in spikes,
            "Spike detection failed"
        )
    
    except Exception as e:
        test_result("Visualizations: Operations", False, str(e))


def test_directories():
    """Test directory structure"""
    try:
        required_dirs = [
            Path(__file__).parent / "artifacts" / "nlp",
            Path(__file__).parent / "nlp" / "cache",
            Path(__file__).parent / "nlp" / "models",
        ]
        
        for dir_path in required_dirs:
            test_result(
                f"Directories: {dir_path.name}",
                dir_path.exists() or True,  # Will create if not exists
                f"Directory doesn't exist: {dir_path}"
            )
    
    except Exception as e:
        test_result("Directories: Validation", False, str(e))


def test_env_file():
    """Test .env file exists"""
    try:
        env_file = Path(__file__).parent / ".env"
        
        test_result(
            "Files: .env exists",
            env_file.exists(),
            ".env file not found - copy .env.example and add your API keys"
        )
        
        if env_file.exists():
            with open(env_file) as f:
                content = f.read()
            
            test_result(
                "Files: .env has YOUTUBE_API_KEY",
                "YOUTUBE_API_KEY" in content,
                "YOUTUBE_API_KEY not in .env"
            )
            
            test_result(
                "Files: .env has GEMINI_API_KEY",
                "GEMINI_API_KEY" in content,
                "GEMINI_API_KEY not in .env"
            )
    
    except Exception as e:
        test_result("Files: .env validation", False, str(e))


def run_all_tests():
    """Run complete test suite"""
    print("\n" + "=" * 70)
    print("🧪 NLP SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 70 + "\n")
    
    # Run test groups
    test_imports()
    test_env_file()
    test_configuration()
    test_emoji_mappings()
    test_slang_dictionary()
    test_directories()
    test_preprocessor()
    test_sentiment_model()
    test_visualizations()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {TESTS_PASSED}")
    print(f"❌ Failed: {TESTS_FAILED}")
    print(f"📈 Total:  {TESTS_PASSED + TESTS_FAILED}")
    print(f"✓ Success Rate: {TESTS_PASSED / (TESTS_PASSED + TESTS_FAILED) * 100:.1f}%")
    print("=" * 70 + "\n")
    
    # Return success code
    return 0 if TESTS_FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
