import streamlit as st
import pandas as pd
import numpy as np
import time
import re
from datetime import datetime, timedelta
import googleapiclient.discovery
import isodate
import io
import plotly.graph_objects as go
import plotly.express as px

# Set page configuration
st.set_page_config(page_title="YouTube Channel Analyzer", page_icon="📊", layout="wide")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #FF0000;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 600;
    }
    .metric-label {
        font-size: 1rem;
        color: #6c757d;
    }
</style>
""", unsafe_allow_html=True)

# Custom function for number formatting
def format_number(num):
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(num)

# Function to convert YouTube duration to seconds
def duration_to_seconds(duration_str):
    return int(isodate.parse_duration(duration_str).total_seconds())

# Function to format seconds to readable duration
def format_duration(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
    else:
        return f"{int(minutes):02d}:{int(seconds):02d}"

# Function to extract channel ID from URL
def extract_channel_id(url):
    patterns = [
        r'(?:youtube\.com\/channel\/)([^\/\?]+)',  # Standard channel URL
        r'(?:youtube\.com\/c\/)([^\/\?]+)',        # Custom URL
        r'(?:youtube\.com\/@)([^\/\?]+)',          # Handle URL
        r'(?:youtube\.com\/user\/)([^\/\?]+)'      # Legacy username URL
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

# Function to build YouTube API client
def get_youtube_api():
    api_key = st.secrets["youtube_api_key"]
    youtube = googleapiclient.discovery.build(
        "youtube", "v3", developerKey=api_key
    )
    return youtube

# Function to get channel information
def get_channel_info(youtube, channel_id):
    try:
        # First try direct channel ID
        request = youtube.channels().list(
            part="snippet,statistics,contentDetails",
            id=channel_id
        )
        response = request.execute()
        
        # If no results, try as username or handle
        if not response['items']:
            request = youtube.channels().list(
                part="snippet,statistics,contentDetails",
                forUsername=channel_id
            )
            response = request.execute()
            
        # If still no results and it might be a handle (starts with @)
        if not response['items'] and channel_id.startswith('@'):
            # For handles, we need to search for the channel
            request = youtube.search().list(
                part="snippet",
                q=channel_id,
                type="channel",
                maxResults=1
            )
            search_response = request.execute()
            
            if search_response['items']:
                channel_id = search_response['items'][0]['id']['channelId']
                request = youtube.channels().list(
                    part="snippet,statistics,contentDetails",
                    id=channel_id
                )
                response = request.execute()
        
        if response['items']:
            return response['items'][0]
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching channel info: {str(e)}")
        return None

# Function to get all videos from a channel
def get_all_videos(youtube, playlist_id, max_results=500):
    videos = []
    next_page_token = None
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        count = 0
        total_found = 0
        
        while True:
            request = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            if not total_found:
                # Get approximate total
                total_found = min(response.get('pageInfo', {}).get('totalResults', 0), max_results)
                if total_found == 0:
                    break
            
            for item in response['items']:
                if count >= max_results:
                    break
                    
                video_id = item['contentDetails']['videoId']
                videos.append({
                    'video_id': video_id,
                    'title': item['snippet']['title'],
                    'upload_date': item['snippet']['publishedAt'],
                    'description': item['snippet']['description'],
                    'thumbnail_url': item['snippet']['thumbnails']['high']['url'] if 'high' in item['snippet']['thumbnails'] else '',
                })
                count += 1
                
            progress = min(count / total_found, 1.0) if total_found > 0 else 1.0
            progress_bar.progress(progress)
            status_text.text(f"Fetched {count} videos out of approximately {total_found}...")
            
            next_page_token = response.get('nextPageToken')
            
            if next_page_token is None or count >= max_results:
                break
                
        status_text.text(f"Completed! Found {len(videos)} videos.")
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
        
        return videos
    except Exception as e:
        st.error(f"Error fetching videos: {str(e)}")
        progress_bar.empty()
        status_text.empty()
        return []

# Function to get video details in batches
def get_video_details(youtube, video_ids):
    video_details = []
    batches = [video_ids[i:i+50] for i in range(0, len(video_ids), 50)]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, batch in enumerate(batches):
        try:
            request = youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=",".join(batch)
            )
            response = request.execute()
            
            for item in response['items']:
                try:
                    duration_seconds = duration_to_seconds(item['contentDetails']['duration'])
                    
                    # Calculate engagement rate
                    views = int(item['statistics'].get('viewCount', 0))
                    likes = int(item['statistics'].get('likeCount', 0))
                    comments = int(item['statistics'].get('commentCount', 0))
                    engagement_rate = ((likes + comments) / views * 100) if views > 0 else 0
                    
                    # Calculate days since upload
                    upload_date = datetime.fromisoformat(item['snippet']['publishedAt'].replace('Z', '+00:00'))
                    days_since_upload = (datetime.now().astimezone() - upload_date).days
                    
                    # Calculate month
                    month = upload_date.strftime("%B %Y")
                    
                    video_details.append({
                        'video_id': item['id'],
                        'title': item['snippet']['title'],
                        'upload_date': item['snippet']['publishedAt'],
                        'duration_seconds': duration_seconds,
                        'duration': format_duration(duration_seconds),
                        'views': views,
                        'likes': likes,
                        'comments': comments,
                        'engagement_rate': round(engagement_rate, 2),
                        'description': item['snippet']['description'],
                        'thumbnail_url': item['snippet']['thumbnails']['high']['url'] if 'high' in item['snippet']['thumbnails'] else '',
                        'days_since_upload': days_since_upload,
                        'days_old': days_since_upload,
                        'month': month
                    })
                except Exception as e:
                    st.warning(f"Error processing video {item['id']}: {str(e)}")
                    continue
                    
            progress = (i + 1) / len(batches)
            progress_bar.progress(progress)
            status_text.text(f"Processing video details... Batch {i+1}/{len(batches)}")
            
            # Add a small delay to avoid API quota issues
            time.sleep(0.5)
            
        except Exception as e:
            st.error(f"Error fetching video details for batch {i+1}: {str(e)}")
            continue
    
    status_text.text("Completed processing video details!")
    time.sleep(1)
    status_text.empty()
    progress_bar.empty()
    
    return video_details

# Function to calculate views per hour metrics
def calculate_vph_metrics(df):
    now = datetime.now().astimezone()
    
    for index, row in df.iterrows():
        upload_time = datetime.fromisoformat(row['upload_date'].replace('Z', '+00:00'))
        hours_since_upload = (now - upload_time).total_seconds() / 3600
        
        # Overall views per hour (all time)
        if hours_since_upload > 0:
            df.at[index, 'views_per_hour'] = round(row['views'] / hours_since_upload, 2)
        else:
            df.at[index, 'views_per_hour'] = 0
        
        # VPH for different time periods
        # For videos older than the specified period, calculate based on that period
        # For newer videos, calculate based on actual age
        
        # 24 hours VPH
        if hours_since_upload >= 24:
            df.at[index, 'vph_24h'] = round(row['views'] / 24, 2)
        else:
            df.at[index, 'vph_24h'] = round(row['views'] / max(1, hours_since_upload), 2)
        
        # 3 days VPH
        if hours_since_upload >= 72:
            df.at[index, 'vph_3d'] = round(row['views'] / 72, 2)
        else:
            df.at[index, 'vph_3d'] = round(row['views'] / max(1, hours_since_upload), 2)
        
        # 1 week VPH
        if hours_since_upload >= 168:
            df.at[index, 'vph_1w'] = round(row['views'] / 168, 2)
        else:
            df.at[index, 'vph_1w'] = round(row['views'] / max(1, hours_since_upload), 2)
        
        # 1 month VPH
        if hours_since_upload >= 720:
            df.at[index, 'vph_1m'] = round(row['views'] / 720, 2)
        else:
            df.at[index, 'vph_1m'] = round(row['views'] / max(1, hours_since_upload), 2)
    
    return df

# Function to calculate view range statistics
def calculate_view_ranges(df, max_days=30):
    # For videos within the max_days range
    recent_df = df[df['days_since_upload'] <= max_days].copy()
    
    # Initialize ranges dataframe
    day_ranges = []
    
    for day in range(1, max_days + 1):
        # Filter videos that are at least 'day' days old
        videos_on_day = recent_df[recent_df['days_since_upload'] >= day].copy()
        
        if not videos_on_day.empty:
            # Calculate cumulative views up to that day
            videos_on_day['day_views'] = videos_on_day.apply(
                lambda row: min(row['views'], row['views'] * day / row['days_since_upload']) 
                if row['days_since_upload'] > day else row['views'],
                axis=1
            )
            
            # Get percentiles
            p25 = np.percentile(videos_on_day['day_views'], 25)
            p50 = np.percentile(videos_on_day['day_views'], 50)
            p75 = np.percentile(videos_on_day['day_views'], 75)
            p90 = np.percentile(videos_on_day['day_views'], 90)
            
            day_ranges.append({
                'day': day,
                'lower_range': round(p25),
                'median': round(p50),
                'upper_range': round(p75),
                'top_performers': round(p90),
                'sample_size': len(videos_on_day)
            })
    
    return pd.DataFrame(day_ranges)

# Main app
def main():
    st.markdown('<h1 class="main-header">YouTube Channel Analyzer</h1>', unsafe_allow_html=True)
    
    # Input for channel URL
    channel_url = st.text_input("Enter YouTube Channel URL:", placeholder="https://www.youtube.com/@example")
    
    max_videos = st.slider("Maximum number of videos to analyze:", 10, 500, 100)
    
    if st.button("Analyze Channel", type="primary"):
        if channel_url:
            with st.spinner("Analyzing channel data..."):
                # Extract channel ID from URL
                channel_id = extract_channel_id(channel_url)
                
                if not channel_id:
                    st.error("Could not extract channel ID from the URL. Please check the URL format.")
                    return
                
                # Get YouTube API client
                youtube = get_youtube_api()
                
                # Get channel information
                channel_info = get_channel_info(youtube, channel_id)
                
                if not channel_info:
                    st.error("Channel not found. Please check the URL and try again.")
                    return
                
                # Display channel header
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    st.image(
                        channel_info['snippet']['thumbnails']['high']['url'],
                        width=150
                    )
                
                with col2:
                    st.markdown(f"### {channel_info['snippet']['title']}")
                    st.write(channel_info['snippet']['description'][:150] + "..." if len(channel_info['snippet']['description']) > 150 else channel_info['snippet']['description'])
                
                with col3:
                    st.metric("Subscribers", format_number(int(channel_info['statistics'].get('subscriberCount', 0))))
                    st.metric("Total Videos", format_number(int(channel_info['statistics'].get('videoCount', 0))))
                
                # Channel metrics
                st.markdown("---")
                st.markdown('<h2 class="sub-header">Channel Metrics</h2>', unsafe_allow_html=True)
                
                metric1, metric2, metric3, metric4 = st.columns(4)
                
                with metric1:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{format_number(int(channel_info["statistics"].get("viewCount", 0)))}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Total Views</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with metric2:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{datetime.fromisoformat(channel_info["snippet"]["publishedAt"].replace("Z", "+00:00")).strftime("%b %d, %Y")}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Channel Created</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with metric3:
                    days_active = (datetime.now().astimezone() - datetime.fromisoformat(channel_info["snippet"]["publishedAt"].replace("Z", "+00:00"))).days
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{days_active:,}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Days Active</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with metric4:
                    avg_views_per_video = int(int(channel_info["statistics"].get("viewCount", 0)) / int(channel_info["statistics"].get("videoCount", 1)))
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{format_number(avg_views_per_video)}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Avg. Views Per Video</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Get uploads playlist ID
                uploads_playlist_id = channel_info['contentDetails']['relatedPlaylists']['uploads']
                
                # Get videos from the channel
                st.markdown("---")
                st.markdown('<h2 class="sub-header">Video Analysis</h2>', unsafe_allow_html=True)
                
                videos = get_all_videos(youtube, uploads_playlist_id, max_results=max_videos)
                
                if not videos:
                    st.warning("No videos found for this channel.")
                    return
                
                # Get detailed video information
                video_ids = [video['video_id'] for video in videos]
                video_details = get_video_details(youtube, video_ids)
                
                if not video_details:
                    st.warning("Could not retrieve video details.")
                    return
                
                # Create DataFrame
                df = pd.DataFrame(video_details)
                
                # Calculate views per hour metrics
                df = calculate_vph_metrics(df)
                
                # Reorder columns according to the requested format
                df = df[['video_id', 'title', 'upload_date', 'duration_seconds', 'duration', 
                          'views', 'views_per_hour', 'vph_24h', 'vph_3d', 'vph_1w', 'vph_1m',
                          'likes', 'comments', 'engagement_rate', 'description', 'thumbnail_url',
                          'days_since_upload', 'days_old', 'month']]
                
                # Calculate view ranges
                view_ranges_df = calculate_view_ranges(df)
                
                # Display video data
                st.dataframe(
                    df.sort_values('upload_date', ascending=False),
                    column_config={
                        "video_id": "Video ID",
                        "title": "Title",
                        "upload_date": "Upload Date",
                        "duration_seconds": "Duration (sec)",
                        "duration": "Duration",
                        "views": "Views",
                        "views_per_hour": "Views Per Hour",
                        "vph_24h": "VPH (24h)",
                        "vph_3d": "VPH (3d)",
                        "vph_1w": "VPH (1w)",
                        "vph_1m": "VPH (1m)",
                        "likes": "Likes",
                        "comments": "Comments",
                        "engagement_rate": "Engagement Rate (%)",
                        "description": st.column_config.TextColumn("Description", width="medium"),
                        "thumbnail_url": "Thumbnail URL",
                        "days_since_upload": "Days Since Upload",
                        "days_old": "Days Old",
                        "month": "Month"
                    },
                    hide_index=True
                )
                
                # Display view ranges
                st.markdown("---")
                st.markdown('<h2 class="sub-header">View Performance Ranges</h2>', unsafe_allow_html=True)
                st.write("This shows the typical view ranges for videos at different ages:")
                
                # Display view ranges as a table
                st.dataframe(
                    view_ranges_df,
                    column_config={
                        "day": "Day",
                        "lower_range": "Lower Range (25%)",
                        "median": "Median (50%)",
                        "upper_range": "Upper Range (75%)",
                        "top_performers": "Top Performers (90%)",
                        "sample_size": "Sample Size"
                    },
                    hide_index=True
                )
                
                # Create view range visualization
                st.markdown("### View Range Visualization")
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=view_ranges_df['day'],
                    y=view_ranges_df['top_performers'],
                    fill=None,
                    mode='lines',
                    line_color='rgba(0, 100, 255, 0.8)',
                    name='Top Performers (90%)'
                ))
                
                fig.add_trace(go.Scatter(
                    x=view_ranges_df['day'],
                    y=view_ranges_df['upper_range'],
                    fill='tonexty',
                    mode='lines',
                    line_color='rgba(0, 176, 246, 0.8)',
                    name='Upper Range (75%)'
                ))
                
                fig.add_trace(go.Scatter(
                    x=view_ranges_df['day'],
                    y=view_ranges_df['median'],
                    fill='tonexty',
                    mode='lines',
                    line_color='rgba(73, 222, 255, 0.8)',
                    name='Median (50%)'
                ))
                
                fig.add_trace(go.Scatter(
                    x=view_ranges_df['day'],
                    y=view_ranges_df['lower_range'],
                    fill='tonexty',
                    mode='lines',
                    line_color='rgba(144, 238, 255, 0.8)',
                    name='Lower Range (25%)'
                ))
                
                fig.update_layout(
                    title='Cumulative View Ranges Over Time',
                    xaxis_title='Days Since Upload',
                    yaxis_title='Views',
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                    hovermode="x unified",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Create Excel download option
                st.markdown("---")
                st.markdown('<h2 class="sub-header">Download Data</h2>', unsafe_allow_html=True)
                
                # Create Excel file in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Video Data', index=False)
                    view_ranges_df.to_excel(writer, sheet_name='View Ranges', index=False)
                
                output.seek(0)
                
                # Provide download button
                st.download_button(
                    label="Download Excel Report",
                    data=output,
                    file_name=f"{channel_info['snippet']['title']}_youtube_analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # Add note about API usage
                st.markdown("""
                **Note:** This app uses the YouTube Data API v3. The analysis is limited by API quotas.
                The app is optimized to use minimal API calls while providing comprehensive data.
                """)
        else:
            st.warning("Please enter a YouTube channel URL.")

if __name__ == "__main__":
    main()
