#!/usr/bin/env python
"""Test NLP backend functions"""

from backend.app.main import create_sentiment_analysis_payload

try:
    result = create_sentiment_analysis_payload()
    print('✅ Backend NLP Functions Work!')
    print(f'Total Feedback: {result["total_feedback"]}')
    print(f'Sentiment Distribution: {result["sentiment_distribution"]}')
    print(f'Emotion Distribution: {result["emotion_distribution"]}')
    print(f'Keywords Count: {len(result["keywords"])}')
    print(f'Raw Feedback Count: {len(result["raw_feedback"])}')
    print()
    
    if result["keywords"]:
        print(f'Sample Keyword: {result["keywords"][0]}')
    
    if result["raw_feedback"]:
        feedback = result["raw_feedback"][0]
        print(f'Sample Feedback:')
        print(f'  - Time: {feedback["time"]}')
        print(f'  - Author: {feedback["author"]}')
        print(f'  - Sentiment: {feedback["sentiment"]}')
        print(f'  - Emotion: {feedback["emotion"]}')
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
