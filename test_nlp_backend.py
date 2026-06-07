#!/usr/bin/env python
"""Test NLP backend functions"""

import pandas as pd
# Assuming the file path is correct for your structure, you can modify it as needed.
try:
    from backend.app.main import create_sentiment_analysis_payload
    # Pylance Golden Rule: Provide required arguments and don't pass None directly if expecting a DataFrame.
    test_df = pd.DataFrame({
        "time": ["2026-06-07 12:40:00"], 
        "author": ["Tester"], 
        "sentiment": ["Positive"], 
        "message": ["Ini hanya pesan tes"]
    })
    
    result = create_sentiment_analysis_payload(df=test_df)
    print('✅ Backend NLP Functions Work!')
    print(f'Total Feedback: {result.get("total_feedback", 0)}')
    print(f'Sentiment Distribution: {result.get("sentiment_distribution", {})}')
    print(f'Emotion Distribution: {result.get("emotion_distribution", {})}')
    print(f'Keywords Count: {len(result.get("keywords", []))}')
    print(f'Raw Feedback Count: {len(result.get("raw_feedback", []))}')
    print()
    
    if result.get("keywords"):
        print(f'Sample Keyword: {result["keywords"][0]}')
    
    if result.get("raw_feedback"):
        feedback = result["raw_feedback"][0]
        print(f'Sample Feedback:')
        print(f'  - Time: {feedback.get("time", "")}')
        print(f'  - Author: {feedback.get("author", "")}')
        print(f'  - Sentiment: {feedback.get("sentiment", "")}')
        print(f'  - Emotion: {feedback.get("emotion", "")}')
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()