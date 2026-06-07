"""
Quick test to verify app integration:
1. Load app_lapisai.py
2. Check if both pages are accessible
3. Check if data loads properly
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("🧪 APP INTEGRATION TEST")
print("=" * 70)

# Test 1: Import app
print("\n[1/5] Testing app_lapisai imports...")
try:
    import app_lapisai_integrated
    print("✅ app_lapisai imported successfully")
except Exception as e:
    print(f"❌ Failed to import app_lapisai: {e}")
    sys.exit(1)

# Test 2: Import new_pages
print("\n[2/5] Testing new_pages functions...")
try:
    from new_pages import render_churn_analysis_prediction_page, render_audience_chat_analysis_page
    print("✅ Both page functions imported successfully")
except Exception as e:
    print(f"❌ Failed to import page functions: {e}")
    sys.exit(1)

# Test 3: Load engineered features
print("\n[3/5] Testing engineered_features CSV...")
try:
    import pandas as pd
    eng_features = pd.read_csv("engineered_features/lapisai_engineered_features.csv")
    print(f"✅ Loaded engineered_features: {len(eng_features)} customers, {len(eng_features.columns)} features")
    print(f"   Columns: {list(eng_features.columns[:10])}...")
except Exception as e:
    print(f"❌ Failed to load engineered_features: {e}")
    sys.exit(1)

# Test 4: Load sample chat data
print("\n[4/5] Testing youtube chat data...")
try:
    chat_df = pd.read_csv("youtube_chat_5_menit_cleaned.csv")
    print(f"✅ Loaded chat data: {len(chat_df)} comments")
    print(f"   Columns: {list(chat_df.columns)}")
except Exception as e:
    print(f"❌ Failed to load chat data: {e}")
    sys.exit(1)

# Test 5: Verify NLP modules
print("\n[5/5] Testing NLP modules...")
try:
    from nlp_preprocessor import NLPPreprocessor
    from sentiment_model import SentimentModel
    from nlp_visualizations import create_sentiment_timeline
    
    preprocessor = NLPPreprocessor()
    model = SentimentModel()
    
    print("✅ All NLP modules imported successfully")
except Exception as e:
    print(f"❌ Failed to import NLP modules: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED - App is ready!")
print("=" * 70)
print("\nTo launch app:")
print("  streamlit run app_lapisai.py")
