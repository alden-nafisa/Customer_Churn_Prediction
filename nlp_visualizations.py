"""
NLP Visualizations for YouTube Sentiment Analysis Dashboard
Handles: Timeline, KPIs, Keywords, Leaderboard, Spike Detection
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sentiment_timeline(df: pd.DataFrame, 
                             bin_seconds: int = 30,
                             colors: Dict = None) -> go.Figure:
    """
    Create sentiment timeline with 30-second bins
    Shows emotion changes over stream time
    
    Args:
        df: DataFrame with 'elapsed' and 'sentiment' columns
        bin_seconds: Bin size in seconds (30 for 30-sec bins)
        colors: Custom color map for sentiments
    
    Returns:
        Plotly figure
    """
    if df.empty:
        return go.Figure().add_annotation(text="No data")
    
    default_colors = {
        'Positive': '#00CC96',  # Green
        'Neutral': '#636EFA',   # Blue
        'Negative': '#EF553B'   # Red
    }
    colors = colors or default_colors
    
    try:
        # Parse elapsed time MM:SS to seconds
        df = df.copy()
        df['elapsed_seconds'] = df['elapsed'].apply(_parse_elapsed)
        
        # Create bins
        df['time_bin'] = (df['elapsed_seconds'] // bin_seconds * bin_seconds).astype(int)
        
        # Count by bin and sentiment
        timeline_data = df.groupby(['time_bin', 'sentiment']).size().reset_index(name='count')
        
        # Create figure
        fig = go.Figure()
        
        for sentiment in ['Positive', 'Neutral', 'Negative']:
            sentiment_data = timeline_data[timeline_data['sentiment'] == sentiment]
            
            fig.add_trace(go.Scatter(
                x=sentiment_data['time_bin'],
                y=sentiment_data['count'],
                name=sentiment,
                mode='lines+markers',
                line=dict(color=colors.get(sentiment, '#000'), width=3),
                marker=dict(size=8),
                hovertemplate='<b>%{fullData.name}</b><br>Time: %{x}s<br>Count: %{y}<extra></extra>'
            ))
        
        fig.update_layout(
            title='Sentiment Timeline (30-second bins)',
            xaxis_title='Time (seconds)',
            yaxis_title='Message Count',
            hovermode='x unified',
            template='plotly_white',
            height=400,
            showlegend=True,
        )
        
        logger.info("✓ Sentiment timeline created")
        return fig
    
    except Exception as e:
        logger.error(f"❌ Timeline creation failed: {e}")
        return go.Figure().add_annotation(text=f"Error: {e}")


def create_kpi_cards(df: pd.DataFrame) -> Dict:
    """
    Create KPI metrics for sentiment analysis
    
    Returns dict with:
    - total_comments
    - positive_pct, neutral_pct, negative_pct
    - positive_count, neutral_count, negative_count
    - unique_commenters
    - engagement_rate
    """
    if df.empty:
        return {}
    
    total = len(df)
    sentiment_counts = df['sentiment'].value_counts().to_dict()
    
    kpis = {
        'total_comments': total,
        'unique_commenters': df['author'].nunique() if 'author' in df.columns else 0,
        'engagement_rate': (df['likes'].sum() / total) if 'likes' in df.columns else 0,
        
        'positive_count': sentiment_counts.get('Positive', 0),
        'positive_pct': f"{sentiment_counts.get('Positive', 0) / total * 100:.1f}%",
        
        'neutral_count': sentiment_counts.get('Neutral', 0),
        'neutral_pct': f"{sentiment_counts.get('Neutral', 0) / total * 100:.1f}%",
        
        'negative_count': sentiment_counts.get('Negative', 0),
        'negative_pct': f"{sentiment_counts.get('Negative', 0) / total * 100:.1f}%",
    }
    
    return kpis


def create_sentiment_distribution_pie(df: pd.DataFrame,
                                     colors: Dict = None) -> go.Figure:
    """Create pie chart for overall sentiment distribution"""
    if df.empty:
        return go.Figure()
    
    default_colors = {
        'Positive': '#00CC96',
        'Neutral': '#636EFA',
        'Negative': '#EF553B'
    }
    colors = colors or default_colors
    
    sentiment_counts = df['sentiment'].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=sentiment_counts.index,
        values=sentiment_counts.values,
        marker=dict(colors=[colors.get(s, '#000') for s in sentiment_counts.index]),
        textposition='auto',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title='Sentiment Distribution',
        height=400,
        template='plotly_white',
    )
    
    logger.info("✓ Sentiment distribution chart created")
    return fig


def create_top_keywords_by_sentiment(df: pd.DataFrame,
                                    top_n: int = 8,
                                    colors: Dict = None) -> Dict[str, go.Figure]:
    """
    Create separate keyword charts for each sentiment
    
    Returns dict with 3 figures (Positive, Neutral, Negative)
    """
    if df.empty:
        return {}
    
    default_colors = {
        'Positive': '#00CC96',
        'Neutral': '#636EFA',
        'Negative': '#EF553B'
    }
    colors = colors or default_colors
    
    figures = {}
    
    for sentiment in ['Positive', 'Neutral', 'Negative']:
        sentiment_df = df[df['sentiment'] == sentiment]
        
        if sentiment_df.empty:
            continue
        
        # Extract words
        all_words = ' '.join(sentiment_df['message']).lower().split()
        
        # Filter common stopwords
        stopwords = {'yang', 'itu', 'ini', 'dan', 'untuk', 'di', 'ke', 'dari', 
                    'dengan', 'atau', 'adalah', 'a', 'the', 'of', 'in', 'to', 'on'}
        
        words = [w for w in all_words if len(w) > 2 and w not in stopwords]
        word_counts = Counter(words).most_common(top_n)
        
        if not word_counts:
            continue
        
        keywords, counts = zip(*word_counts)
        
        fig = go.Figure(data=[go.Bar(
            x=keywords,
            y=counts,
            marker_color=colors.get(sentiment, '#000'),
            hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
        )])
        
        fig.update_layout(
            title=f'Top {top_n} Keywords - {sentiment}',
            xaxis_title='Keyword',
            yaxis_title='Frequency',
            height=300,
            template='plotly_white',
            showlegend=False,
        )
        
        figures[sentiment] = fig
    
    logger.info("✓ Top keywords charts created")
    return figures


def create_top_commenters_leaderboard(df: pd.DataFrame,
                                     top_n: int = 10) -> go.Figure:
    """
    Create leaderboard of most active commenters
    Shows comment count and positive sentiment %
    """
    if df.empty or 'author' not in df.columns:
        return go.Figure()
    
    # Count comments per author
    author_counts = df['author'].value_counts().head(top_n)
    
    # Calculate positive sentiment % for each author
    author_sentiments = {}
    for author in author_counts.index:
        author_df = df[df['author'] == author]
        positive_count = (author_df['sentiment'] == 'Positive').sum()
        positive_pct = positive_count / len(author_df) * 100
        author_sentiments[author] = positive_pct
    
    # Create figure
    fig = go.Figure(data=[go.Bar(
        x=author_counts.values,
        y=author_counts.index,
        orientation='h',
        marker=dict(
            color=[author_sentiments.get(a, 0) for a in author_counts.index],
            colorscale='RdYlGn',
            cmin=0,
            cmax=100,
            colorbar=dict(title="Positive %")
        ),
        text=[f"{v} comments" for v in author_counts.values],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>Comments: %{x}<br>Positive: %{marker.color:.0f}%<extra></extra>'
    )])
    
    fig.update_layout(
        title=f'Top {top_n} Most Active Commenters',
        xaxis_title='Number of Comments',
        yaxis_title='Author',
        height=400,
        template='plotly_white',
        showlegend=False,
    )
    
    logger.info("✓ Leaderboard created")
    return fig


def detect_sentiment_spikes(df: pd.DataFrame,
                           bin_seconds: int = 30,
                           threshold: float = 2.0) -> Dict:
    """
    Detect significant sentiment spikes/drops
    Alert if sentiment count > 2x average for that time bin
    
    Returns dict with:
    - spikes: List of {time, sentiment, count, avg, ratio}
    """
    if df.empty:
        return {'spikes': []}
    
    try:
        df = df.copy()
        df['elapsed_seconds'] = df['elapsed'].apply(_parse_elapsed)
        df['time_bin'] = (df['elapsed_seconds'] // bin_seconds * bin_seconds).astype(int)
        
        spikes = []
        
        # Analyze each sentiment
        for sentiment in ['Positive', 'Neutral', 'Negative']:
            sentiment_df = df[df['sentiment'] == sentiment]
            
            if sentiment_df.empty:
                continue
            
            # Count by bin
            bin_counts = sentiment_df.groupby('time_bin').size()
            avg_count = bin_counts.mean()
            
            # Find spikes
            for time_bin, count in bin_counts.items():
                if count > avg_count * threshold:
                    ratio = count / avg_count
                    spikes.append({
                        'time': time_bin,
                        'sentiment': sentiment,
                        'count': int(count),
                        'average': float(avg_count),
                        'ratio': float(ratio),
                    })
        
        # Sort by ratio (most significant first)
        spikes = sorted(spikes, key=lambda x: x['ratio'], reverse=True)
        
        logger.info(f"✓ Detected {len(spikes)} sentiment spikes")
        return {'spikes': spikes}
    
    except Exception as e:
        logger.error(f"❌ Spike detection failed: {e}")
        return {'spikes': []}


def create_spike_alert_banner(spikes: Dict) -> str:
    """Create HTML banner for sentiment spike alerts"""
    spike_list = spikes.get('spikes', [])
    
    if not spike_list:
        return "No significant sentiment spikes detected ✓"
    
    # Show top 3 spikes
    alerts = []
    for spike in spike_list[:3]:
        alert = (f"⚠️ {spike['sentiment']} spike at {spike['time']}s: "
                f"{spike['count']} comments ({spike['ratio']:.1f}x average)")
        alerts.append(alert)
    
    return "\n".join(alerts)


def _parse_elapsed(elapsed_str: str) -> int:
    """Parse MM:SS or M:SS format to total seconds"""
    try:
        parts = str(elapsed_str).split(':')
        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        elif len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        else:
            return 0
    except:
        return 0


# Example usage
if __name__ == "__main__":
    # Sample data
    import pandas as pd
    
    data = {
        'elapsed': ['0:00', '0:30', '1:00', '1:30', '2:00', '0:15', '0:45', '1:15'],
        'author': ['user1', 'user2', 'user1', 'user3', 'user2', 'user4', 'user1', 'user3'],
        'message': ['keren', 'bagus', 'suka', 'jelek', 'biasa', 'mantap', 'amazing', 'buruk'],
        'sentiment': ['Positive', 'Positive', 'Positive', 'Negative', 'Neutral', 'Positive', 'Positive', 'Negative'],
        'likes': [5, 2, 8, 1, 0, 10, 15, 0],
    }
    
    df = pd.DataFrame(data)
    
    print("=" * 60)
    print("NLP VISUALIZATIONS - DEMO")
    print("=" * 60)
    
    # Create visualizations
    print("\n1. KPI Cards:")
    kpis = create_kpi_cards(df)
    for key, value in kpis.items():
        print(f"   {key}: {value}")
    
    print("\n2. Sentiment Timeline:")
    fig_timeline = create_sentiment_timeline(df)
    print(f"   ✓ Created timeline with {len(df)} comments")
    
    print("\n3. Sentiment Distribution:")
    fig_dist = create_sentiment_distribution_pie(df)
    print(f"   ✓ Created distribution chart")
    
    print("\n4. Top Keywords:")
    fig_keywords = create_top_keywords_by_sentiment(df)
    print(f"   ✓ Created {len(fig_keywords)} keyword charts")
    
    print("\n5. Top Commenters:")
    fig_leaderboard = create_top_commenters_leaderboard(df, top_n=5)
    print(f"   ✓ Created leaderboard")
    
    print("\n6. Sentiment Spikes:")
    spikes = detect_sentiment_spikes(df)
    print(f"   {create_spike_alert_banner(spikes)}")
    
    print("\n" + "=" * 60)
