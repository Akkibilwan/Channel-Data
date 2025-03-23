import streamlit as st
import pandas as pd
import numpy as np
import re
import time
from datetime import datetime
import googleapiclient.discovery
import io

# Set page configuration
st.set_page_config(page_title="YouTube Channel Analyzer", page_icon="📊", layout="wide")

# Add custom CSS
st.markdown("""
<style>
    .header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #FF0000;
        text-align: center;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Function to convert YouTube duration to seconds using regex
def parse_duration(duration):
    # YouTube duration format is PT#H#M#S
    hours = 0
    minutes = 0
    seconds = 0
    
    hour_match = re.search(r'(\d+)H', duration)
    if hour_match:
        hours = int(hour_match.group(1))
    
    minute_match = re.search(r'(\d+)M', duration)
    if minute_match:
        minutes = int(minute_match.group(1))
    
    second_match = re.search(r'(\d+)S', duration)
    if second_match:
        seconds = int(second_match.group(1))
    
    return hours * 3600 + minutes * 60 + seconds

# Function to format duration
def format_duration(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
    else:
        return f"{int(minutes):02d}:{int(seconds):02d}"

# Function to extract channel info from URL
def extract_channel_info(url):
    # Handle @username format
    username_match = re.search(r'youtube\.com/@([^/\s?]+)', url)
    if username_match:
        return '@' + username_match.group(1)
    
    # Handle /channel/ format
    channel_match = re.search(r'youtube\.com/channel/([^/\s?]+)', url)
    if channel_match:
        return channel_match.group(1)
    
    # Handle /c/ format
    custom_match = re.search(r'youtube\.com/c/([^/\s?]+)', url)
    if custom_match:
        return custom_match.group(1)
    
    # Handle /user/ format
    user_match = re.search(r'youtube\.com/user/([^/\s?]+)', url)
    if user_match:
        return user_match.group(1)
    
    return url

# Function to get YouTube API client
def get_youtube_api():
    api_key = st.secrets["youtube_api_key"]
    youtube = googleapiclient.discovery.build(
        "youtube", "v3", developerKey=api_key
    )
    return youtube

# Function to get channel data
def get_channel_data(youtube, channel_identifier):
    # Try direct channel ID
    try:
        response = youtube.channels().list(
            part="snippet,statistics,contentDetails",
            id=channel_identifier
        ).execute()
        
        if response.get('items'):
            return response['items'][0]
    except Exception as e:
        st.write(f"Error with channel ID: {str(e)}")
    
    # Try username
    try:
        response = youtube.channels().list(
            part="snippet,statistics,contentDetails",
            forUsername=channel_identifier.lstrip('@')
        ).execute()
        
        if response.get('items'):
            return response['items'][0]
    except Exception as e:
        st.write(f"Error with username: {str(e)}")
    
    # Try search
    try:
        search_response = youtube.search().list(
            part="snippet",
            q=channel_identifier,
            type="channel",
            maxResults=1
        ).execute()
        
        if search_response.get('items'):
            channel_id = search_response['items'][0]['id']['channelId']
            
            response = youtube.channels().list(
                part="snippet,statistics,contentDetails",
                id=channel_id
            ).execute()
            
            if response.get('items'):
                return response['items'][0]
    except Exception as e:
        st.write(f"Error with search: {str(e)}")
    
    return None

# Function to get videos from channel
def get_videos(youtube, uploads_playlist_id):
    videos = []
    next_page_token = None
    
    progress = st.progress(0)
    status_text = st.empty()
    page_count = 0
    
    try:
        while True:
            page_count += 1
            status_text.text(f"Fetching videos... Page {page_count}")
            
            response = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()
            
            for item in response.get('items', []):
                video_id = item['contentDetails']['videoId']
                videos.append({
                    'video_id': video_id,
                    'title': item['snippet'].get('title', ''),
                    'upload_date': item['snippet'].get('publishedAt', '')
                })
            
            next_page_token = response.get('nextPageToken')
            
            if not next_page_token:
                break
            
            progress.progress(min(0.95, page_count / 20))
            time.sleep(0.1)
        
        progress.progress(1.0)
        status_text.text(f"Found {len(videos)} videos!")
        time.sleep(1)
        status_text.empty()
        progress.empty()
    
    except Exception as e:
        st.error(f"Error getting videos: {str(e)}")
    
    return videos

# Function to get video details
def get_video_details(youtube, videos):
    video_details = []
    video_batches = [videos[i:i+50] for i in range(0, len(videos), 50)]
    
    progress = st.progress(0)
    status_text = st.empty()
    
    for i, batch in enumerate(video_batches):
        try:
            video_ids = [v['video_id'] for v in batch]
            status_text.text(f"Getting video details... Batch {i+1}/{len(video_batches)}")
            
            response = youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=','.join(video_ids)
            ).execute()
            
            for item in response.get('items', []):
                video_id = item['id']
                
                # Find basic info
                basic_info = next((v for v in batch if v['video_id'] == video_id), {})
                
                # Parse video data
                try:
                    # Duration
                    duration_str = item['contentDetails'].get('duration', 'PT0S')
                    duration_seconds = parse_duration(duration_str)
                    
                    # Determine if it's a short, based on the modified condition
                    is_short = False
                    if '#shorts' in item['snippet'].get('title', '').lower() or \
                       '#shorts' in item['snippet'].get('description', '').lower() or \
                       'shorts' in item['snippet'].get('tags', []) or \
                       duration_seconds <= 60:  # Most shorts are 60 seconds or less
                        is_short = True
                    
                    # Statistics
                    stats = item.get('statistics', {})
                    views = int(stats.get('viewCount', 0))
                    likes = int(stats.get('likeCount', 0))
                    comments = int(stats.get('commentCount', 0))
                    
                    # Engagement rate
                    engagement_rate = 0
                    if views > 0:
                        engagement_rate = round((likes + comments) / views * 100, 2)
                    
                    # Upload date and age
                    upload_date_str = basic_info.get('upload_date', '')
                    upload_date = datetime.fromisoformat(upload_date_str.replace('Z', '+00:00'))
                    days_since_upload = (datetime.now().astimezone() - upload_date).days
                    month = upload_date.strftime("%B %Y")
                    
                    # Calculate views per hour
                    hours_since_upload = max(1, days_since_upload * 24)
                    views_per_hour = round(views / hours_since_upload, 2)
                    
                    # Calculate VPH metrics
                    vph_24h = round((views / days_since_upload) * (24 / 24), 2) if days_since_upload >= 1 else views_per_hour
                    vph_3d = round((views / days_since_upload) * (24 / 72), 2) if days_since_upload >= 3 else views_per_hour
                    vph_1w = round((views / days_since_upload) * (24 / 168), 2) if days_since_upload >= 7 else views_per_hour
                    vph_1m = round((views / days_since_upload) * (24 / 720), 2) if days_since_upload >= 30 else views_per_hour
                    
                    # Add to results
                    video_details.append({
                        'video_id': video_id,
                        'title': basic_info.get('title', ''),
                        'upload_date': upload_date_str,
                        'duration_seconds': duration_seconds,
                        'duration': format_duration(duration_seconds),
                        'is_short': is_short,
                        'video_type': 'Short' if is_short else 'Long-form',
                        'views': views,
                        'views_per_hour': views_per_hour,
                        'vph_24h': vph_24h,
                        'vph_3d': vph_3d,
                        'vph_1w': vph_1w,
                        'vph_1m': vph_1m,
                        'likes': likes,
                        'comments': comments,
                        'engagement_rate': engagement_rate,
                        'description': item['snippet'].get('description', ''),
                        'thumbnail_url': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                        'days_since_upload': days_since_upload,
                        'days_old': days_since_upload,
                        'month': month
                    })
                except Exception as e:
                    st.write(f"Error processing video {video_id}: {str(e)}")
            
            progress.progress((i + 1) / len(video_batches))
            time.sleep(0.1)
        
        except Exception as e:
            st.error(f"Error getting video details for batch {i+1}: {str(e)}")
    
    progress.progress(1.0)
    status_text.text("Completed processing all videos!")
    time.sleep(1)
    status_text.empty()
    progress.empty()
    
    return video_details

# Function to calculate daily view metrics (VidIQ style) with video type filtering
def calculate_view_metrics(df, max_days=None, video_type='all'):
    # Filter videos based on type
    if video_type == 'long_form':
        filtered_df = df[~df['is_short']].copy()
    elif video_type == 'shorts':
        filtered_df = df[df['is_short']].copy()
    else:  # 'all'
        filtered_df = df.copy()
    
    # If no videos match the filter, return empty DataFrame
    if filtered_df.empty:
        return pd.DataFrame(columns=['day', 'dailyViewSnapshot_lowest', 'dailyViewSnapshot_highest', 
                                    'cumulativeViewTotal_min', 'cumulativeViewTotal_median',
                                    'cumulativeViewTotal_max', 'cumulativeViewTotal_overall',
                                    'cumulative_lowest', 'cumulative_highest', 'sample_size'])
    
    # If max_days is None or 0, set it to the age of the oldest video
    if not max_days:
        max_days = int(filtered_df['days_since_upload'].max()) + 1
    
    # Initialize the data structures
    daily_snapshot = {day: [] for day in range(1, max_days + 1)}
    cumulative_totals = {day: [] for day in range(1, max_days + 1)}
    
    # Process each video
    for _, video in filtered_df.iterrows():
        total_views = video['views']
        days_old = video['days_since_upload']
        
        # Skip videos with no views
        if total_views == 0:
            continue
        
        # For older videos, estimate daily and cumulative views
        if days_old > 0:
            # Calculate assumed daily views
            daily_views = []
            cumulative = 0
            
            # Use a model that assumes front-loaded views (typical for YouTube)
            # Day 1 gets most views, gradually decreasing
            total_time_weight = sum([1/(i**0.5) for i in range(1, days_old + 1)])
            
            for day in range(1, min(days_old + 1, max_days + 1)):
                # Weight gives higher values to earlier days
                day_weight = 1/(day**0.5)
                
                # Estimate daily views for this day
                day_views = int(total_views * (day_weight / total_time_weight))
                daily_views.append(day_views)
                
                # Add to cumulative
                cumulative += day_views
                
                # Store in our data structures
                daily_snapshot[day].append(day_views)
                cumulative_totals[day].append(cumulative)
    
    # Calculate metrics for each day
    results = []
    cumulative_lowest = 0
    cumulative_highest = 0
    
    for day in range(1, max_days + 1):
        # Daily view snapshot
        if daily_snapshot[day]:
            daily_lowest = int(min(daily_snapshot[day]))
            daily_highest = int(max(daily_snapshot[day]))
        else:
            daily_lowest = 0
            daily_highest = 0
        
        # Cumulative view totals
        if cumulative_totals[day]:
            cumulative_min = int(min(cumulative_totals[day]))
            cumulative_median = int(np.median(cumulative_totals[day]))
            cumulative_max = int(max(cumulative_totals[day]))
            
            # Update running totals
            cumulative_lowest += daily_lowest
            cumulative_highest += daily_highest
        else:
            cumulative_min = 0
            cumulative_median = 0
            cumulative_max = 0
        
        # Store the results
        results.append({
            'day': day,
            'dailyViewSnapshot_lowest': daily_lowest,
            'dailyViewSnapshot_highest': daily_highest,
            'cumulativeViewTotal_min': cumulative_min,
            'cumulativeViewTotal_median': cumulative_median,
            'cumulativeViewTotal_max': cumulative_max,
            'cumulativeViewTotal_overall': cumulative_median,  # This matches VidIQ's overall metric
            'cumulative_lowest': cumulative_lowest,
            'cumulative_highest': cumulative_highest,
            'sample_size': len(daily_snapshot[day])
        })
    
    return pd.DataFrame(results)

# Main app
def main():
    st.markdown('<h1 class="header">YouTube Channel Analyzer</h1>', unsafe_allow_html=True)
    
    # Input for channel URL
    channel_url = st.text_input("Enter YouTube Channel URL:", 
                              placeholder="https://www.youtube.com/@ChannelName")
    
    # Create columns for options
    col1, col2 = st.columns(2)
    
    with col1:
        # Days to analyze (making it optional)
        use_max_days = st.checkbox("Limit analysis to specific number of days", value=False)
        max_days = None
        if use_max_days:
            max_days = st.slider("Days to analyze:", min_value=7, max_value=365, value=30)
    
    with col2:
        # Video type filter
        video_type_filter = st.selectbox(
            "Video type to analyze:",
            options=[
                "All Videos", 
                "Long-form Videos", 
                "Shorts"
            ],
            index=0
        )
        
        # Map selection to filter values
        video_type_map = {
            "All Videos": "all",
            "Long-form Videos": "long_form",
            "Shorts": "shorts"
        }
        video_type = video_type_map[video_type_filter]
    
    # Analyze button
    if st.button("Analyze Channel", type="primary"):
        if not channel_url:
            st.warning("Please enter a YouTube channel URL")
            return
        
        with st.spinner("Analyzing YouTube channel..."):
            # Get channel identifier
            channel_identifier = extract_channel_info(channel_url)
            
            # Get YouTube API
            youtube = get_youtube_api()
            
            # Get channel data
            channel_data = get_channel_data(youtube, channel_identifier)
            
            if not channel_data:
                st.error("Could not find channel. Please check the URL.")
                st.info("Make sure the URL is correct and formatted as one of these:\n"
                       "- https://www.youtube.com/@ChannelName\n"
                       "- https://www.youtube.com/channel/CHANNEL_ID\n")
                return
            
            # Display channel info
            col1, col2 = st.columns([1, 3])
            
            with col1:
                # Channel thumbnail
                if 'thumbnails' in channel_data.get('snippet', {}):
                    st.image(
                        channel_data['snippet']['thumbnails'].get('high', {}).get('url', ''),
                        width=150
                    )
            
            with col2:
                # Channel details
                st.markdown(f"### {channel_data['snippet'].get('title', 'Unknown Channel')}")
                st.write(f"**Subscribers:** {int(channel_data.get('statistics', {}).get('subscriberCount', 0)):,}")
                st.write(f"**Total Videos:** {int(channel_data.get('statistics', {}).get('videoCount', 0)):,}")
                st.write(f"**Total Views:** {int(channel_data.get('statistics', {}).get('viewCount', 0)):,}")
            
            # Get uploads playlist
            uploads_playlist_id = channel_data.get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads')
            
            if not uploads_playlist_id:
                st.error("Could not find videos for this channel.")
                return
            
            # Get videos
            st.subheader("Fetching Videos")
            videos = get_videos(youtube, uploads_playlist_id)
            
            if not videos:
                st.warning("No videos found for this channel.")
                return
            
            # Get video details
            st.subheader("Getting Video Details")
            video_details = get_video_details(youtube, videos)
            
            if not video_details:
                st.warning("Could not get video details.")
                return
            
            # Create DataFrame
            video_df = pd.DataFrame(video_details)
            
            # Sort by upload date (newest first)
            video_df = video_df.sort_values('upload_date', ascending=False).reset_index(drop=True)
            
            # Display videos
            st.subheader("Channel Videos")
            
            # Add filter interface
            video_filter_type = st.radio(
                "Filter videos:", 
                ["All Videos", "Long-form Videos", "Shorts"],
                horizontal=True
            )
            
            # Add video URL
            video_df['video_url'] = video_df['video_id'].apply(lambda x: f"https://www.youtube.com/watch?v={x}")
            
            # Filter dataframe based on selection
            if video_filter_type == "Long-form Videos":
                filtered_df = video_df[~video_df['is_short']]
            elif video_filter_type == "Shorts":
                filtered_df = video_df[video_df['is_short']]
            else:
                filtered_df = video_df
            
            # Count video types
            total_videos = len(video_df)
            long_form_count = len(video_df[~video_df['is_short']])
            shorts_count = len(video_df[video_df['is_short']])
            
            st.write(f"Total Videos: {total_videos} | Long-form Videos: {long_form_count} | Shorts: {shorts_count}")
            
            # Show current filter counts
            st.write(f"Currently showing: {len(filtered_df)} videos")
            
            # Display dataframe
            st.dataframe(
                filtered_df,
                column_config={
                    "video_id": "Video ID",
                    "video_url": st.column_config.LinkColumn("Video Link"),
                    "title": "Title",
                    "upload_date": "Upload Date",
                    "duration": "Duration",
                    "duration_seconds": st.column_config.NumberColumn("Duration (sec)", format="%d"),
                    "video_type": "Video Type",
                    "views": st.column_config.NumberColumn("Views", format="%d"),
                    "views_per_hour": st.column_config.NumberColumn("Views Per Hour", format="%.2f"),
                    "vph_24h": st.column_config.NumberColumn("VPH (24h)", format="%.2f"),
                    "vph_3d": st.column_config.NumberColumn("VPH (3d)", format="%.2f"),
                    "vph_1w": st.column_config.NumberColumn("VPH (1w)", format="%.2f"),
                    "vph_1m": st.column_config.NumberColumn("VPH (1m)", format="%.2f"),
                    "likes": st.column_config.NumberColumn("Likes", format="%d"),
                    "comments": st.column_config.NumberColumn("Comments", format="%d"),
                    "engagement_rate": st.column_config.NumberColumn("Engagement Rate (%)", format="%.2f"),
                    "days_since_upload": "Days Since Upload",
                    "month": "Month",
                    "is_short": None  # Hide this column
                }
            )
            
            # Calculate view metrics
            st.subheader(f"View Performance Metrics ({video_type_filter})")
            
            # Calculate metrics based on selected filter
            view_metrics = calculate_view_metrics(video_df, max_days, video_type)
            
            # Display view metrics with pagination if needed
            if len(view_metrics) > 30:
                st.write("Showing lifetime metrics (scroll to see more):")
                st.write("- **Daily View Snapshot (Lowest/Highest)**: The lowest and highest daily views for videos on each day")
                st.write("- **Cumulative View Total**: The total views accumulated by day X of a video's life")
                st.write("- **Cumulative Running Totals**: The running sum of daily lowest/highest views")
                
                # Paginate the metrics
                metrics_per_page = 30
                total_pages = (len(view_metrics) + metrics_per_page - 1) // metrics_per_page
                
                page = st.slider("Page", 1, total_pages, 1)
                start_idx = (page - 1) * metrics_per_page
                end_idx = min(start_idx + metrics_per_page, len(view_metrics))
                
                st.dataframe(
                    view_metrics.iloc[start_idx:end_idx],
                    column_config={
                        "day": "Day",
                        "dailyViewSnapshot_lowest": st.column_config.NumberColumn("Daily Lowest", format="%d"),
                        "dailyViewSnapshot_highest": st.column_config.NumberColumn("Daily Highest", format="%d"),
                        "cumulativeViewTotal_min": st.column_config.NumberColumn("Cumulative Min", format="%d"),
                        "cumulativeViewTotal_median": st.column_config.NumberColumn("Cumulative Median", format="%d"),
                        "cumulativeViewTotal_max": st.column_config.NumberColumn("Cumulative Max", format="%d"),
                        "cumulativeViewTotal_overall": st.column_config.NumberColumn("Cumulative Overall", format="%d"),
                        "cumulative_lowest": st.column_config.NumberColumn("Cumulative Running Lowest", format="%d"),
                        "cumulative_highest": st.column_config.NumberColumn("Cumulative Running Highest", format="%d"),
                        "sample_size": "Sample Size"
                    }
                )
            else:
                st.write("View performance metrics:")
                st.write("- **Daily View Snapshot (Lowest/Highest)**: The lowest and highest daily views for videos on each day")
                st.write("- **Cumulative View Total**: The total views accumulated by day X of a video's life")
                st.write("- **Cumulative Running Totals**: The running sum of daily lowest/highest views")
                
                st.dataframe(
                    view_metrics,
                    column_config={
                        "day": "Day",
                        "dailyViewSnapshot_lowest": st.column_config.NumberColumn("Daily Lowest", format="%d"),
                        "dailyViewSnapshot_highest": st.column_config.NumberColumn("Daily Highest", format="%d"),
                        "cumulativeViewTotal_min": st.column_config.NumberColumn("Cumulative Min", format="%d"),
                        "cumulativeViewTotal_median": st.column_config.NumberColumn("Cumulative Median", format="%d"),
                        "cumulativeViewTotal_max": st.column_config.NumberColumn("Cumulative Max", format="%d"),
                        "cumulativeViewTotal_overall": st.column_config.NumberColumn("Cumulative Overall", format="%d"),
                        "cumulative_lowest": st.column_config.NumberColumn("Cumulative Running Lowest", format="%d"),
                        "cumulative_highest": st.column_config.NumberColumn("Cumulative Running Highest", format="%d"),
                        "sample_size": "Sample Size"
                    }
                )
            
            # Create Excel download
            st.subheader("Download Data")
            
            # Create Excel file with sheets for each type
            excel_buffer = io.BytesIO()
            
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                # Add video data
                video_df.to_excel(writer, sheet_name='All Videos', index=False)
                
                # Add filtered video data
                long_form_df = video_df[~video_df['is_short']].copy()
                if not long_form_df.empty:
                    long_form_df.to_excel(writer, sheet_name='Long-form Videos', index=False)
                
                shorts_df = video_df[video_df['is_short']].copy()
                if not shorts_df.empty:
                    shorts_df.to_excel(writer, sheet_name='Shorts', index=False)
                
                # Add metrics for selected video type
                view_metrics.to_excel(writer, sheet_name=f'Metrics - {video_type_filter}', index=False)
                
                # Add metrics for all video types
                all_metrics = calculate_view_metrics(video_df, max_days, 'all')
                all_metrics.to_excel(writer, sheet_name='Metrics - All Videos', index=False)
                
                long_form_metrics = calculate_view_metrics(video_df, max_days, 'long_form')
                if not long_form_metrics.empty:
                    long_form_metrics.to_excel(writer, sheet_name='Metrics - Long-form', index=False)
                
                shorts_metrics = calculate_view_metrics(video_df, max_days, 'shorts')
                if not shorts_metrics.empty:
                    shorts_metrics.to_excel(writer, sheet_name='Metrics - Shorts', index=False)
                
                # Add summary statistics sheet
                summary_data = {
                    'Metric': [
                        'Total Videos',
                        'Long-form Videos',
                        'Shorts',
                        'Total Views',
                        'Long-form Views',
                        'Shorts Views',
                        'Average Views (All)',
                        'Average Views (Long-form)',
                        'Average Views (Shorts)',
                        'Average Engagement Rate (All)',
                        'Average Engagement Rate (Long-form)',
                        'Average Engagement Rate (Shorts)',
                        'Total Watch Time (hours)',
                        'Average Duration (All)',
                        'Average Duration (Long-form)',
                        'Average Duration (Shorts)'
                    ],
                    'Value': [
                        len(video_df),
                        len(long_form_df),
                        len(shorts_df),
                        video_df['views'].sum(),
                        long_form_df['views'].sum() if not long_form_df.empty else 0,
                        shorts_df['views'].sum() if not shorts_df.empty else 0,
                        round(video_df['views'].mean(), 2),
                        round(long_form_df['views'].mean(), 2) if not long_form_df.empty else 0,
                        round(shorts_df['views'].mean(), 2) if not shorts_df.empty else 0,
                        round(video_df['engagement_rate'].mean(), 2),
                        round(long_form_df['engagement_rate'].mean(), 2) if not long_form_df.empty else 0,
                        round(shorts_df['engagement_rate'].mean(), 2) if not shorts_df.empty else 0,
                        round((video_df['duration_seconds'].sum() / 3600), 2),
                        format_duration(int(video_df['duration_seconds'].mean())),
                        format_duration(int(long_form_df['duration_seconds'].mean())) if not long_form_df.empty else '00:00',
                        format_duration(int(shorts_df['duration_seconds'].mean())) if not shorts_df.empty else '00:00'
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary Statistics', index=False)
            
            excel_buffer.seek(0)
            
            # Download button
            st.download_button(
                label="Download Excel Report",
                data=excel_buffer,
                file_name=f"{channel_data['snippet'].get('title', 'channel')}_youtube_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
