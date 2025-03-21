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

# Function to calculate daily view ranges (VidIQ style)
def calculate_daily_view_ranges(df, max_days=30):
    # Create data structure to hold daily performance
    daily_views = {day: [] for day in range(1, max_days + 1)}
    
    # For each video, estimate its views at each day of its lifecycle
    for _, video in df.iterrows():
        total_views = video['views']
        days_old = video['days_since_upload']
        
        # Skip videos with no views
        if total_views == 0:
            continue
        
        # For each day in the video's lifecycle (up to max_days)
        for day in range(1, min(max_days + 1, days_old + 1)):
            # For older videos, we need to estimate historical views
            if days_old > max_days:
                # Estimate using a curve that models typical YouTube view distribution
                # Views tend to accumulate faster in earlier days
                
                # Calculate what fraction of total days this represents
                day_fraction = day / days_old
                
                # Use a curve that gives more weight to early days
                # Power values less than 1 create curves where growth is faster initially
                view_fraction = day_fraction ** 0.7
                
                # Calculate estimated views at this day
                day_views = int(total_views * view_fraction)
            else:
                # For newer videos, use actual total views for current age
                day_views = total_views
            
            # Add to our collection
            daily_views[day].append(day_views)
    
    # Now calculate statistics for each day
    results = []
    for day in range(1, max_days + 1):
        views = daily_views[day]
        
        # Only include days with enough data
        if len(views) >= 3:  # Require at least 3 videos for meaningful stats
            results.append({
                'day': day,
                'min_views': int(min(views)),
                'average_min': int(np.percentile(views, 10)),  # Bottom 10% average
                'lower_range': int(np.percentile(views, 25)),
                'median': int(np.percentile(views, 50)),
                'upper_range': int(np.percentile(views, 75)),
                'average_max': int(np.percentile(views, 90)),  # Top 10% average
                'max_views': int(max(views)),
                'sample_size': len(views)
            })
    
    return pd.DataFrame(results)

# Main app
def main():
    st.markdown('<h1 class="header">YouTube Channel Analyzer</h1>', unsafe_allow_html=True)
    
    # Input for channel URL
    channel_url = st.text_input("Enter YouTube Channel URL:", 
                              placeholder="https://www.youtube.com/@ChannelName")
    
    # Days to analyze
    max_days = st.slider("Days to analyze:", min_value=7, max_value=90, value=30)
    
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
            
            # Add video URL
            video_df['video_url'] = video_df['video_id'].apply(lambda x: f"https://www.youtube.com/watch?v={x}")
            
            # Display dataframe
            st.dataframe(
                video_df,
                column_config={
                    "video_id": "Video ID",
                    "video_url": st.column_config.LinkColumn("Video Link"),
                    "title": "Title",
                    "upload_date": "Upload Date",
                    "duration": "Duration",
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
                    "month": "Month"
                }
            )
            
            # Calculate view ranges
            st.subheader("View Performance Ranges")
            view_ranges = calculate_daily_view_ranges(video_df, max_days)
            
            # Display view ranges
            st.write("This shows the cumulative view ranges for videos on each day after publishing:")
            st.write("- **Min Views**: Absolute minimum views any video had by this day")
            st.write("- **Average Min**: Average of bottom 10% performers (VidIQ's typical lower range)")
            st.write("- **Lower Range**: 25th percentile of views")
            st.write("- **Median**: 50th percentile (middle point)")
            st.write("- **Upper Range**: 75th percentile of views")
            st.write("- **Average Max**: Average of top 10% performers (VidIQ's typical upper range)")
            st.write("- **Max Views**: Absolute maximum views any video had by this day")
            
            st.dataframe(
                view_ranges,
                column_config={
                    "day": "Day",
                    "min_views": st.column_config.NumberColumn("Min Views", format="%d"),
                    "average_min": st.column_config.NumberColumn("Average Min", format="%d"),
                    "lower_range": st.column_config.NumberColumn("Lower Range (25%)", format="%d"),
                    "median": st.column_config.NumberColumn("Median (50%)", format="%d"),
                    "upper_range": st.column_config.NumberColumn("Upper Range (75%)", format="%d"),
                    "average_max": st.column_config.NumberColumn("Average Max", format="%d"),
                    "max_views": st.column_config.NumberColumn("Max Views", format="%d"),
                    "sample_size": "Sample Size"
                }
            )
            
            # Create Excel download
            st.subheader("Download Data")
            
            # Create Excel file
            excel_buffer = io.BytesIO()
            
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                video_df.to_excel(writer, sheet_name='Video Data', index=False)
                view_ranges.to_excel(writer, sheet_name='View Ranges', index=False)
            
            excel_buffer.seek(0)
            
            # Download button
            st.download_button(
                label="Download Excel Report",
                data=excel_buffer,
                file_name=f"{channel_data['snippet'].get('title', 'channel')}_youtube_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
