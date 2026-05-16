#!/usr/bin/env python3
"""
Setup and initialization script for Customer Churn Prediction Dashboard
with NLP Sentiment Analysis Visualizations

This script:
1. Generates NLP artifacts (sentiment models, session summaries)
2. Creates visualization assets
3. Provides instructions for running the app
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def main():
    """Main setup function."""
    print("\n" + "="*80)
    print("🚀 CUSTOMER CHURN PREDICTION DASHBOARD - SETUP")
    print("="*80)
    
    print("\n1️⃣  SYSTEM CHECK")
    print("-" * 80)
    
    # Check required files
    required_files = [
        "youtube_chat_5_menit_cleaned.csv",
        "app_lapisai.py",
        "generate_nlp_visualizations.py",
    ]
    
    missing_files = []
    for fname in required_files:
        fpath = PROJECT_ROOT / fname
        if fpath.exists():
            print(f"  ✅ {fname}")
        else:
            print(f"  ❌ {fname} - NOT FOUND")
            missing_files.append(fname)
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        print("Setup cannot proceed.")
        return False
    
    print("\n2️⃣  GENERATING NLP VISUALIZATIONS")
    print("-" * 80)
    
    try:
        from generate_nlp_visualizations import (
            load_youtube_data,
            build_labeled_dataset,
            train_sentiment_model,
            build_session_summary,
            save_nlp_artifacts,
            create_sentiment_visualizations,
        )
        
        print("  Loading YouTube data...")
        df = load_youtube_data()
        print(f"  ✓ Loaded {len(df)} comments")
        
        print("  Building labeled dataset...")
        labeled_df = build_labeled_dataset(df)
        sentiment_counts = labeled_df["sentiment_label"].value_counts()
        print(f"  ✓ Sentiment distribution:")
        for sentiment, count in sentiment_counts.items():
            pct = count / len(labeled_df) * 100
            print(f"    - {sentiment}: {count} ({pct:.1f}%)")
        
        print("  Training sentiment model...")
        pipeline, metrics, test_predictions = train_sentiment_model(labeled_df)
        print(f"  ✓ Model performance:")
        print(f"    - Accuracy: {metrics['accuracy']:.3f}")
        print(f"    - Precision: {metrics['precision_macro']:.3f}")
        print(f"    - Recall: {metrics['recall_macro']:.3f}")
        print(f"    - F1-Score: {metrics['f1_macro']:.3f}")
        
        print("  Building session summary...")
        session_summary = build_session_summary(labeled_df)
        summary_text = session_summary.pop("extractive_summary", "")
        print(f"  ✓ Session stats:")
        print(f"    - Total comments: {session_summary['total_comments']}")
        print(f"    - Unique users: {session_summary['unique_commenters']}")
        print(f"    - Keywords: {len(session_summary['top_keywords'])}")
        
        print("  Creating visualizations...")
        visualizations = create_sentiment_visualizations(labeled_df, metrics)
        print(f"  ✓ Created {len(visualizations)} visualization objects")
        
        print("  Saving artifacts...")
        save_nlp_artifacts(pipeline, metrics, test_predictions, session_summary, summary_text)
        print(f"  ✓ All artifacts saved to artifacts/nlp/")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n3️⃣  INSTALLATION CHECK")
    print("-" * 80)
    
    required_packages = [
        "streamlit",
        "pandas",
        "plotly",
        "scikit-learn",
        "joblib",
        "nltk",
        "numpy",
    ]
    
    missing_packages = []
    for pkg in required_packages:
        try:
            __import__(pkg)
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} - MISSING")
            missing_packages.append(pkg)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages. Install with:")
        print(f"   pip install {' '.join(missing_packages)}")
    
    print("\n4️⃣  NEXT STEPS")
    print("-" * 80)
    print("""
✅ Setup complete! Your dashboard is ready to run.

To start the app:
   
   cd C:\\Users\\HP14\\Downloads\\pbl6\\Customer_Churn_Prediction
   streamlit run app_lapisai.py

Login credentials:
   Username: Admin123
   Password: 12345678

Dashboard features:
   🔮 Predict - Make churn predictions for new customers
   📈 Analysis - View model performance and diagnostics
   ℹ️  About - Project information
   📊 Advanced - Full analysis with NLP sentiment analysis
   
NLP Features:
   • Sentiment classification on YouTube chat data
   • Session summary generation
   • Keyword extraction
   • Representative comments analysis
   • Test predictions preview

Files generated:
   📁 artifacts/nlp/
      ├── naive_bayes_sentiment_pipeline.pkl
      ├── sentiment_metrics.json
      ├── sentiment_test_predictions.csv
      └── session_summary.json

Documentation:
   📖 See LAPISAI_COMPREHENSIVE_FEATURE_ANALYSIS.md for full details
   """)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
