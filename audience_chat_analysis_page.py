"""
Audience Chat Analysis Page for Streamlit Dashboard
Displays NLP sentiment analysis results with interactive visualizations
"""

import streamlit as st
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import our custom modules
from youtube_scraper import YouTubeScraper
from nlp_preprocessor import NLPPreprocessor
from sentiment_model import SentimentModel, predict_sentiment
from nlp_config import ENABLE_CACHING, YOUTUBE_API_KEY
from summarization_engine import create_summarizer
from nlp_visualizations import (
    create_sentiment_timeline,
    create_kpi_cards,
    create_sentiment_distribution_pie,
    create_top_keywords_by_sentiment,
    create_top_commenters_leaderboard,
    detect_sentiment_spikes,
    create_spike_alert_banner,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize Streamlit session state"""
    if 'youtube_data' not in st.session_state:
        st.session_state.youtube_data = None
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'sentiments' not in st.session_state:
        st.session_state.sentiments = None
    if 'scraper_status' not in st.session_state:
        st.session_state.scraper_status = None


def scrape_youtube_video(video_id_or_url: str) -> Optional[pd.DataFrame]:
    if not YOUTUBE_API_KEY:
        st.error("❌ YouTube API Key not configured. Check .env file.")
        return None
    
    try:
        with st.spinner("🎬 Scraping YouTube comments..."):
            scraper = YouTubeScraper(YOUTUBE_API_KEY, max_results=500)
            df = scraper.scrape_video(video_id_or_url)
            
            if df.empty:
                st.warning("⚠️ No comments found for this video")
                return None
            
            st.success(f"✓ Scraped {len(df)} comments!")
            logger.info(f"Scraped {len(df)} comments from {video_id_or_url}")
            
            return df
    
    except Exception as e:
        st.error(f"❌ Scraping failed: {str(e)}")
        logger.error(f"Scraping error: {e}")
        return None


def preprocess_comments(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    
    try:
        with st.spinner("🔍 Preprocessing comments..."):
            preprocessor = NLPPreprocessor(
                remove_special_chars=False,  
                remove_stopwords=False
            )
            
            df['message_clean'] = df['message'].apply(preprocessor.preprocess)
            
            st.success("✓ Preprocessing complete!")
            
            stats = preprocessor.get_stats()
            col1, col2, col3 = st.columns(3)
            col1.metric("Mentions Removed", stats.get('mentions_removed', 0))
            col2.metric("Emojis Converted", stats.get('emojis_converted', 0))
            col3.metric("Slang Expanded", stats.get('slang_expanded', 0))
            
            return df
    
    except Exception as e:
        st.error(f"❌ Preprocessing failed: {str(e)}")
        logger.error(f"Preprocessing error: {e}")
        return df


def classify_sentiments(df: pd.DataFrame) -> pd.DataFrame:
    if 'message_clean' not in df.columns:
        st.error("❌ Please preprocess comments first")
        return df
    
    try:
        with st.spinner("😊 Classifying sentiments..."):
            model = SentimentModel() 
            
            # Use fixed predict_batch definition inside SentimentModel
            predictions = model.predict_batch(df['message_clean'].tolist())
            predictions_df = pd.DataFrame(predictions)
            
            df = df.reset_index(drop=True)
            df['sentiment'] = predictions_df['sentiment']
            df['confidence'] = predictions_df['confidence']
            
            st.success("✓ Sentiment classification complete!")
            
            sentiment_counts = df['sentiment'].value_counts()
            col1, col2, col3 = st.columns(3)
            col1.metric("😊 Positive", sentiment_counts.get('Positive', 0))
            col2.metric("😐 Neutral", sentiment_counts.get('Neutral', 0))
            col3.metric("😞 Negative", sentiment_counts.get('Negative', 0))
            
            return df
    
    except Exception as e:
        st.error(f"❌ Sentiment classification failed: {str(e)}")
        logger.error(f"Classification error: {e}")
        return df


def generate_summaries(df: pd.DataFrame, video_title: Optional[str] = None) -> Dict[str, str]:
    if 'sentiment' not in df.columns:
        st.error("❌ Please classify sentiments first")
        return {}
    
    try:
        with st.spinner("✍️ Generating AI summaries..."):
            # FIX: Removed use_cache argument
            engine = create_summarizer()
            
            # String casting if video_title is None
            video_title_str = str(video_title) if video_title is not None else ""
            summaries = engine.summarize_by_sentiment(df, video_title=video_title_str)
            
            st.success("✓ Summaries generated!")
            return summaries
    
    except Exception as e:
        st.warning(f"⚠️ Could not generate summaries: {str(e)}")
        logger.warning(f"Summarization error: {e}")
        return {}


def render_audience_chat_analysis_page():
    st.set_page_config(page_title="Audience Chat Analysis", layout="wide")
    initialize_session_state()
    
    st.title("📊 Audience Chat Analysis")
    st.markdown("Analyze YouTube comments sentiment, trends, and viewer engagement")
    
    st.header("1️⃣ YouTube Video Input")
    col1, col2 = st.columns([3, 1])
    with col1:
        video_input = st.text_input("Enter YouTube Video URL or ID:")
    with col2:
        scrape_button = st.button("🎬 Scrape Comments", use_container_width=True)
    
    if scrape_button and video_input:
        youtube_data = scrape_youtube_video(video_input)
        if youtube_data is not None:
            st.session_state.youtube_data = youtube_data
            st.session_state.processed_data = None  
    
    if st.session_state.youtube_data is not None:
        st.success(f"✓ Loaded {len(st.session_state.youtube_data)} comments")
        with st.expander("👀 View Raw Comments (first 10)"):
            st.dataframe(st.session_state.youtube_data[['author', 'message', 'timestamp']].head(10), use_container_width=True)
    
    if st.session_state.youtube_data is not None:
        st.header("2️⃣ Data Processing")
        if st.button("🔍 Preprocess Comments", use_container_width=True):
            processed = preprocess_comments(st.session_state.youtube_data.copy())
            st.session_state.processed_data = processed
        
        if st.session_state.processed_data is not None:
            if st.button("😊 Classify Sentiments", use_container_width=True):
                classified = classify_sentiments(st.session_state.processed_data.copy())
                st.session_state.sentiments = classified
    
    if st.session_state.sentiments is not None:
        df = st.session_state.sentiments
        
        video_title = df['video_title'].iloc[0] if 'video_title' in df.columns else None
        
        st.header("3️⃣ Sentiment Analysis Results")
        
        kpis = create_kpi_cards(df)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📊 Total Comments", kpis.get('total_comments', 0))
        col2.metric("👥 Unique Commenters", kpis.get('unique_commenters', 0))
        col3.metric("💬 Avg Likes", f"{kpis.get('engagement_rate', 0):.1f}")
        col4.metric("📈 Comments/Min", f"{len(df) / 5:.1f}")
        
        st.markdown("### Sentiment Breakdown")
        col1, col2, col3 = st.columns(3)
        col1.metric("😊 Positive", f"{kpis.get('positive_count',0)} ({kpis.get('positive_pct','0%')})")
        col2.metric("😐 Neutral", f"{kpis.get('neutral_count',0)} ({kpis.get('neutral_pct','0%')})")
        col3.metric("😞 Negative", f"{kpis.get('negative_count',0)} ({kpis.get('negative_pct','0%')})")
        
        spikes = detect_sentiment_spikes(df)
        if spikes.get('spikes'):
            st.warning(f"⚠️ Sentiment Spikes Detected:\n{create_spike_alert_banner(spikes)}")
        else:
            st.success("✓ No significant sentiment spikes detected")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Timeline", "Distribution", "Keywords", "Commenters", "Summaries"])
        
        with tab1:
            st.markdown("### Sentiment Timeline")
            fig_timeline = create_sentiment_timeline(df, bin_seconds=30)
            st.plotly_chart(fig_timeline, use_container_width=True)
        
        with tab2:
            st.markdown("### Sentiment Distribution")
            fig_dist = create_sentiment_distribution_pie(df)
            st.plotly_chart(fig_dist, use_container_width=True)
        
        with tab3:
            st.markdown("### Top Keywords by Sentiment")
            fig_keywords = create_top_keywords_by_sentiment(df, top_n=10)
            col1, col2, col3 = st.columns(3)
            if 'Positive' in fig_keywords:
                with col1: st.plotly_chart(fig_keywords['Positive'], use_container_width=True)
            if 'Neutral' in fig_keywords:
                with col2: st.plotly_chart(fig_keywords['Neutral'], use_container_width=True)
            if 'Negative' in fig_keywords:
                with col3: st.plotly_chart(fig_keywords['Negative'], use_container_width=True)
        
        with tab4:
            st.markdown("### Top 10 Most Active Commenters")
            fig_leaderboard = create_top_commenters_leaderboard(df, top_n=10)
            st.plotly_chart(fig_leaderboard, use_container_width=True)
        
        with tab5:
            st.markdown("### AI-Generated Summaries")
            summaries = generate_summaries(df, video_title)
            if summaries:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("#### 😊 Positive Feedback")
                    st.info(summaries.get('Positive', 'No summary available'))
                with col2:
                    st.markdown("#### 😐 Neutral Comments")
                    st.info(summaries.get('Neutral', 'No summary available'))
                with col3:
                    st.markdown("#### 😞 Negative Feedback")
                    st.warning(summaries.get('Negative', 'No summary available'))
        
        st.divider()
        st.markdown("### 📥 Export Results")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(label="📊 Download CSV", data=csv, file_name=f"youtube_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv", use_container_width=True)
        with col2:
            json_str = df.to_json(orient='records', force_ascii=False)
            st.download_button(label="📄 Download JSON", data=json_str, file_name=f"youtube_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", mime="application/json", use_container_width=True)
        with col3:
            st.info("✓ Analysis complete! Export your results above.")


if __name__ == "__main__":
    render_audience_chat_analysis_page()