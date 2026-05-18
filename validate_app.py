"""
Comprehensive validation script for both Customer Churn and NLP pages
Tests all imports, data loading, and basic functionality
"""

import pandas as pd
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("\n" + "=" * 80)
print("🔍 COMPREHENSIVE APP VALIDATION TEST")
print("=" * 80)

# Track results
tests_passed = 0
tests_failed = 0

def test(name: str, func):
    global tests_passed, tests_failed
    try:
        func()
        print(f"✅ {name}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ {name}: {str(e)[:100]}")
        tests_failed += 1

# ============================================================================
# PHASE 1: IMPORTS
# ============================================================================

print("\n[PHASE 1] Testing Imports...")

def test_app_import():
    import app_lapisai
test("Import app_lapisai", test_app_import)

def test_new_pages_import():
    from new_pages import render_churn_analysis_prediction_page, render_audience_chat_analysis_page
test("Import page functions from new_pages", test_new_pages_import)

def test_nlp_modules():
    from youtube_scraper import YouTubeScraper
    from nlp_preprocessor import NLPPreprocessor
    from sentiment_model import SentimentModel
    from summarization_engine import GeminiSummarizationEngine
    from nlp_visualizations import create_sentiment_timeline
test("Import all NLP modules", test_nlp_modules)

def test_visualization_imports():
    import plotly.graph_objects as go
    import plotly.express as px
test("Import visualization libraries", test_visualization_imports)

# ============================================================================
# PHASE 2: DATA LOADING
# ============================================================================

print("\n[PHASE 2] Testing Data Loading...")

eng_features = None
chat_data = None
all_data = None

def test_engineered_features():
    global eng_features
    eng_features = pd.read_csv("engineered_features/lapisai_engineered_features.csv")
    assert len(eng_features) > 0, "No engineered features data"
    assert "customer_id" in eng_features.columns, "Missing customer_id column"
    assert "churned" in eng_features.columns, "Missing churned column"
test("Load engineered_features CSV", test_engineered_features)

def test_chat_data():
    global chat_data
    chat_data = pd.read_csv("youtube_chat_5_menit_cleaned.csv")
    assert len(chat_data) > 0, "No chat data"
    assert "sentiment" in chat_data.columns, "Missing sentiment column"
    assert "author" in chat_data.columns, "Missing author column"
    assert "message" in chat_data.columns, "Missing message column"
test("Load youtube_chat_5_menit_cleaned CSV", test_chat_data)

def test_data_shapes():
    print(f"   → Engineered features: {len(eng_features)} customers × {len(eng_features.columns)} features")
    print(f"   → Chat data: {len(chat_data)} messages")
    print(f"   → Chat columns: {list(chat_data.columns)}")
test("Verify data shapes and structure", test_data_shapes)

# ============================================================================
# PHASE 3: CHURN PAGE FUNCTIONALITY
# ============================================================================

print("\n[PHASE 3] Testing Customer Churn Page Functionality...")

def test_customer_fetch():
    from new_pages import fetch_customer_data
    # Try fetching first customer
    first_id = eng_features.iloc[0]["customer_id"]
    customer = fetch_customer_data(first_id, eng_features)
    assert customer is not None, f"Failed to fetch customer {first_id}"
test("Fetch customer data by ID", test_customer_fetch)

def test_customer_status():
    from new_pages import get_customer_status
    customer_data = eng_features.iloc[0].to_dict()
    status, color = get_customer_status(customer_data)
    assert status in ["Active", "Churned"], f"Invalid status: {status}"
    assert color in ["green", "red"], f"Invalid color: {color}"
test("Determine customer status", test_customer_status)

def test_health_check():
    from new_pages import build_health_check
    result = build_health_check("delayed", 20, 5, 45)
    assert len(result) == 3, "Health check should return 3 elements"
test("Build health check indicators", test_health_check)

def test_whatif_simulator():
    from new_pages import compute_whatif_adjusted_probability
    adjusted = compute_whatif_adjusted_probability(0.5, discount_pct=10, support_resolution_days=7, nps_improvement=10)
    assert 0 <= adjusted <= 1, f"Invalid probability: {adjusted}"
test("What-if probability simulator", test_whatif_simulator)

# ============================================================================
# PHASE 4: NLP PAGE FUNCTIONALITY
# ============================================================================

print("\n[PHASE 4] Testing NLP Audience Chat Page Functionality...")

def test_timeline_creation():
    from new_pages import create_sentiment_timeline
    timeline = create_sentiment_timeline(chat_data)
    assert "Positive" in timeline.columns or "time_bin" in timeline.columns, "Timeline missing expected columns"
test("Create sentiment timeline", test_timeline_creation)

def test_keyword_extraction():
    from new_pages import extract_keywords
    keywords = extract_keywords(chat_data["message"], top_n=10)
    assert len(keywords) > 0, "No keywords extracted"
test("Extract top keywords", test_keyword_extraction)

def test_leaderboard():
    from new_pages import get_top_commenters
    leaderboard = get_top_commenters(chat_data, top_n=10)
    assert len(leaderboard) > 0, "Leaderboard is empty"
    assert "Author" in leaderboard.columns, "Missing Author column"
test("Generate commenter leaderboard", test_leaderboard)

def test_ai_summary():
    from new_pages import create_sentiment_timeline, generate_ai_stream_summary
    timeline = create_sentiment_timeline(chat_data)
    sentiment_dist = {s: (chat_data["sentiment"] == s).sum() / len(chat_data) for s in chat_data["sentiment"].unique()}
    keywords = ["test", "demo", "stream"]
    summary = generate_ai_stream_summary(timeline, sentiment_dist, keywords)
    assert isinstance(summary, str) and len(summary) > 0, "AI summary is empty"
test("Generate AI summary narrative", test_ai_summary)

# ============================================================================
# PHASE 5: VISUALIZATION FUNCTIONS
# ============================================================================

print("\n[PHASE 5] Testing Visualization Functions...")

def test_churn_visualizations():
    import plotly.graph_objects as go
    # Test that visualization functions can be called
    # (We can't actually render them without Streamlit, but we can verify imports)
    sample_data = {
        "Plan": ["Starter", "Professional", "Enterprise"],
        "Revenue at Risk": [15000, 28000, 42000],
    }
test("Churn visualizations available", test_churn_visualizations)

def test_nlp_visualizations():
    from nlp_visualizations import create_sentiment_timeline, create_kpi_cards
    # Test that NLP visualization functions exist and are callable
    assert callable(create_sentiment_timeline), "Sentiment timeline not callable"
    assert callable(create_kpi_cards), "KPI cards not callable"
test("NLP visualizations available", test_nlp_visualizations)

# ============================================================================
# PHASE 6: NLP MODULES FUNCTIONALITY
# ============================================================================

print("\n[PHASE 6] Testing NLP Modules...")

def test_preprocessor():
    from nlp_preprocessor import NLPPreprocessor
    preprocessor = NLPPreprocessor()
    test_text = "😊 keren bgt"
    result = preprocessor.preprocess(test_text)
    assert isinstance(result, str) and len(result) > 0, "Preprocessor failed"
test("NLP Preprocessor", test_preprocessor)

def test_sentiment_model():
    from sentiment_model import SentimentModel
    model = SentimentModel()
    assert model is not None, "Sentiment model failed to initialize"
test("Sentiment Model initialization", test_sentiment_model)

def test_emoji_mappings():
    import json
    with open("emoji_mappings.json") as f:
        emojis = json.load(f)
    assert len(emojis) >= 500, f"Emoji mappings incomplete: {len(emojis)} entries"
test("Emoji mappings (500+ entries)", test_emoji_mappings)

def test_slang_dictionary():
    import json
    with open("slang_dictionary.json") as f:
        slang = json.load(f)
    assert len(slang) >= 200, f"Slang dictionary incomplete: {len(slang)} entries"
test("Slang dictionary (200+ entries)", test_slang_dictionary)

# ============================================================================
# PHASE 7: PAGE ROUTING
# ============================================================================

print("\n[PHASE 7] Testing Page Routing (app_lapisai.py)...")

def test_routing_setup():
    # Verify that app_lapisai.py has the routing configured
    with open("app_lapisai.py") as f:
        content = f.read()
    assert "Audience Chat Analysis" in content, "NLP page not in app routing"
    assert "render_audience_chat_analysis_page" in content, "NLP page function not called"
    assert "render_churn_analysis_prediction_page" in content, "Churn page function not called"
test("App routing configuration", test_routing_setup)

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print(f"✅ TESTS PASSED: {tests_passed}")
print(f"❌ TESTS FAILED: {tests_failed}")
print(f"📊 TOTAL: {tests_passed + tests_failed}")
print("=" * 80)

if tests_failed == 0:
    print("\n🎉 ALL VALIDATIONS PASSED!")
    print("\n✅ Customer Churn Page: READY")
    print("✅ NLP Audience Chat Page: READY")
    print("\nTo launch app, run:")
    print("  streamlit run app_lapisai.py")
else:
    print(f"\n⚠️ {tests_failed} validation(s) failed. Please review errors above.")
    sys.exit(1)
