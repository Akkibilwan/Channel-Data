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
    .subheader {
        font-size: 1.8rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .download-btn {
        background-color: #FF0000;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        text-decoration: none;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Function to convert YouTube duration to seconds using regex
def duration_to_seconds(duration_str):
    hours = 0
    minutes = 0
    seconds = 0
    
    hour_match = re.search(r'(\d+)H', duration_str)
    if hour_match:
        hours = int(hour_match.group(1))
    
    minute_match = re.search(r'(\d+)M', duration_str)
    if minute_match:
        minutes = int(minute_match.group(1))
    
    second_match = re.search(r'(\d+)S', duration_str)
    if second_match:
        seconds = int(second_match.group(1))
    
    return hours * 3600 + minutes * 60 + seconds

# Function to format duration from seconds to HH:MM:SS
def format_duration(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
    else:
        return f"{int(minutes):02d}:{int(seconds):02d}"

# Function to format large numbers
def format_number(num):
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(num)

# Function to extract channel ID from different URL formats
def extract_channel_id_from_url(url):
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
    
    return url  # Return the URL as-is if no match found

# Function to get YouTube API client
@st.cache_resource
def get_youtube_api():
    api_key = st.secrets["youtube_api_key"]
    youtube = googleapiclient.discovery.build(
        "youtube", "v3", developerKey=api_key
    )
    return youtube

# Function to resolve channel from different identifiers
def resolve_channel(youtube, channel_identifier):
    # Try direct channel ID first
    try:
        channel_response = youtube.channels().list(
            part="snippet,statistics,contentDetails",
            id=channel_identifier
        ).execute()
        
        if channel_response.get('items'):
            return channel_response['items'][0]
    except:
        pass
    
    # Try as username
    try:
        channel_response = youtube.channels().list(
            part="snippet,statistics,contentDetails",
            forUsername=channel_identifier.lstrip('@')
        ).execute()
        
        if channel_response.get('items'):
            return channel_response['items'][0]
    except:
        pass
    
    # Try searching for the channel
    try:
        search_response = youtube.search().list(
            part="snippet",
            q=channel_identifier,
            type="channel",
            maxResults=1
        ).execute()
        
        if search_response.get('items'):
            channel_id = search_response['items'][0]['id']['channelId']
            channel_response = youtube.channels().list(
                part="snippet,statistics,contentDetails",
                id=channel_id
            ).execute()
            
            if channel_response.get('items'):
                return channel_response['items'][0]
    except:
        pass
    
    # If all methods fail
    return None

# Function to get all videos from a channel (no limit)
def get_all_videos(youtube, uploads_playlist_id, progress_container):
    videos = []
    next_page_token = None
    
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        page_count = 0
        
        try:
            while True:
                page_count += 1
                status_text.text(f"Fetching videos... Page {page_count}")
                
                # Get playlist items (videos)
                request = youtube.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=uploads_playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                
                # Process video data
                for item in response.get('items', []):
                    video_id = item['contentDetails']['videoId']
                    snippet = item['snippet']
                    
                    # Extract basic video info
                    videos.append({
                        'video_id': video_id,
                        'title': snippet.get('title', ''),
                        'upload_date': snippet.get('publishedAt', ''),
                        'description': snippet.get('description', ''),
                        'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', '')
                    })
                
                # Check if there are more pages
                next_page_token = response.get('nextPageToken')
                
                # Update progress (approximate)
                progress = min(0.95, page_count / 20) if next_page_token else 1.0
                progress_bar.progress(progress)
                
                # Break if no more pages
                if not next_page_token:
                    break
                
                # Small delay to avoid API quota issues
                time.sleep(0.2)
            
            status_text.text(f"Found {len(videos)} videos!")
            time.sleep(1)
            
        except Exception as e:
            st.error(f"Error fetching videos: {str(e)}")
        
        progress_bar.empty()
    
    return videos

# Function to get video details in batches
def get_video_details(youtube, videos, progress_container):
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Split videos into batches of 50 (API limit)
        video_batches = [videos[i:i+50] for i in range(0, len(videos), 50)]
        detailed_videos = []
        
        for i, batch in enumerate(video_batches):
            try:
                video_ids = [video['video_id'] for video in batch]
                status_text.text(f"Getting details for batch {i+1}/{len(video_batches)}...")
                
                # Make the API call to get video details
                request = youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=','.join(video_ids)
                )
                response = request.execute()
                
                # Process video details
                for video_item in response.get('items', []):
                    video_id = video_item['id']
                    
                    # Find the basic video info we collected earlier
                    basic_info = next((v for v in batch if v['video_id'] == video_id), {})
                    
                    # Get content details
                    content_details = video_item.get('contentDetails', {})
                    duration_str = content_details.get('duration', 'PT0S')
                    duration_seconds = duration_to_seconds(duration_str)
                    
                    # Get statistics
                    statistics = video_item.get('statistics', {})
                    views = int(statistics.get('viewCount', 0))
                    likes = int(statistics.get('likeCount', 0))
                    comments = int(statistics.get('commentCount', 0))
                    
                    # Calculate engagement rate
                    engagement_rate = ((likes + comments) / views * 100) if views > 0 else 0
                    
                    # Calculate days since upload
                    upload_date_str = basic_info.get('upload_date', '')
                    upload_date = datetime.fromisoformat(upload_date_str.replace('Z', '+00:00'))
                    days_since_upload = (datetime.now().astimezone() - upload_date).days
                    
                    # Determine month in "Month Year" format
                    month = upload_date.strftime("%B %Y")
                    
                    # Create detailed video entry
                    detailed_video = {
                        'video_id': video_id,
                        'title': basic_info.get('title', ''),
                        'upload_date': upload_date_str,
                        'duration_seconds': duration_seconds,
                        'duration': format_duration(duration_seconds),
                        'views': views,
                        'likes': likes,
                        'comments': comments,
                        'engagement_rate': round(engagement_rate, 2),
                        'description': basic_info.get('description', ''),
                        'thumbnail_url': basic_info.get('thumbnail_url', ''),
                        'days_since_upload': days_since_upload,
                        'days_old': days_since_upload,
                        'month': month
                    }
                    
                    detailed_videos.append(detailed_video)
                
                # Update progress
                progress = (i + 1) / len(video_batches)
                progress_bar.progress(progress)
                
                # Small delay to avoid API quota issues
                time.sleep(0.2)
                
            except Exception as e:
                st.error(f"Error processing video batch {i+1}: {str(e)}")
        
        status_text.text(f"Processed details for {len(detailed_videos)} videos!")
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
    
    return detailed_videos

# Function to calculate views per hour metrics
def calculate_vph_metrics(df):
    now = datetime.now().astimezone()
    
    # Calculate VPH metrics for each video
    for index, row in df.iterrows():
        upload_time = datetime.fromisoformat(row['upload_date'].replace('Z', '+00:00'))
        hours_since_upload = max(1, (now - upload_time).total_seconds() / 3600)
        
        # General views per hour
        df.at[index, 'views_per_hour'] = round(row['views'] / hours_since_upload, 2)
        
        # VPH for specific time periods
        # For 24h
        hours_to_use = min(hours_since_upload, 24)
        estimated_views_24h = row['views'] * (24 / hours_since_upload) if hours_since_upload > 24 else row['views']
        df.at[index, 'vph_24h'] = round(estimated_views_24h / 24, 2)
        
        # For 3 days
        hours_to_use = min(hours_since_upload, 72)
        estimated_views_3d = row['views'] * (72 / hours_since_upload) if hours_since_upload > 72 else row['views']
        df.at[index, 'vph_3d'] = round(estimated_views_3d / 72, 2)
        
        # For 1 week
        hours_to_use = min(hours_since_upload, 168)
        estimated_views_1w = row['views'] * (168 / hours_since_upload) if hours_since_upload > 168 else row['views']
        df.at[index, 'vph_1w'] = round(estimated_views_1w / 168, 2)
        
        # For 1 month
        hours_to_use = min(hours_since_upload, 720)
        estimated_views_1m = row['views'] * (720 / hours_since_upload) if hours_since_upload > 720 else row['views']
        df.at[index, 'vph_1m'] = round(estimated_views_1m / 720, 2)
    
    return df

# Function to calculate view ranges for different days
def calculate_view_ranges(df, max_days=30):
    # Initialize ranges dataframe
    ranges_data = []
    
    # Get videos that are at least max_days old
    for day in range(1, max_days + 1):
        # Filter videos that are at least 'day' days old
        videos_for_day = df[df['days_since_upload'] >= day].copy()
        
        if not videos_for_day.empty:
            # Get estimated views at that day point
            videos_for_day['day_views'] = videos_for_day.apply(
                lambda row: min(row['views'], row['views'] * day / max(day, row['days_since_upload'])),
                axis=1
            )
            
            # Calculate percentiles
            q25 = np.percentile(videos_for_day['day_views'], 25)
            q50 = np.percentile(videos_for_day['day_views'], 50)
            q75 = np.percentile(videos_for_day['day_views'], 75)
            q90 = np.percentile(videos_for_day['day_views'], 90)
            
            # Add to ranges data
            ranges_data.append({
                'day': day,
                'lower_range': int(q25),
                'median': int(q50),
                'upper_range': int(q75),
                'max_range': int(q90),
                'sample_size': len(videos_for_day)
            })
    
    return pd.DataFrame(ranges_data)

# Main function
def main():
    st.markdown('<h1 class="header">YouTube Channel Analyzer</h1>', unsafe_allow_html=True)
    
    # Input for channel URL
    channel_url = st.text_input("Enter YouTube Channel URL:", 
                               placeholder="https://www.youtube.com/@ChannelName")
    
    # Analyze button
    if st.button("Analyze Channel", type="primary"):
        if not channel_url:
            st.warning("Please enter a YouTube channel URL")
            return
        
        # Process the URL to extract channel identifier
        channel_identifier = extract_channel_id_from_url(channel_url)
        
        # Set up YouTube API
        youtube = get_youtube_api()
        
        # Create container for progress indicators
        progress_container = st.container()
        
        with st.spinner("Fetching channel information..."):
            # Resolve channel from identifier
            channel_info = resolve_channel(youtube, channel_identifier)
            
            if not channel_info:
                st.error(f"Channel not found! Please check the URL and try again.")
                st.info("Make sure the URL is in one of these formats:\n" +
                       "- https://www.youtube.com/@username\n" +
                       "- https://www.youtube.com/channel/CHANNEL_ID\n" +
                       "- https://www.youtube.com/c/CUSTOM_URL\n" +
                       "- https://www.youtube.com/user/USERNAME")
                return
            
            # Display channel header
            col1, col2 = st.columns([1, 3])
            
            with col1:
                # Channel thumbnail
                if 'thumbnails' in channel_info.get('snippet', {}):
                    st.image(
                        channel_info['snippet']['thumbnails'].get('high', {}).get('url', ''),
                        width=200
                    )
            
            with col2:
                # Channel title and info
                st.markdown(f"### {channel_info['snippet'].get('title', 'Unknown Channel')}")
                st.markdown(f"**Subscribers:** {format_number(int(channel_info.get('statistics', {}).get('subscriberCount', 0)))}")
                st.markdown(f"**Total Videos:** {format_number(int(channel_info.get('statistics', {}).get('videoCount', 0)))}")
                st.markdown(f"**Total Views:** {format_number(int(channel_info.get('statistics', {}).get('viewCount', 0)))}")
                
                # Calculate channel age
                created_date = datetime.fromisoformat(channel_info['snippet'].get('publishedAt', '').replace('Z', '+00:00'))
                channel_age_days = (datetime.now().astimezone() - created_date).days
                st.markdown(f"**Channel Age:** {channel_age_days} days (Created on {created_date.strftime('%b %d, %Y')})")
            
            # Get uploads playlist ID
            uploads_playlist_id = channel_info.get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads')
            
            if not uploads_playlist_id:
                st.error("Could not find uploads for this channel.")
                return
            
            # Divider
            st.markdown("---")
            st.markdown('<h2 class="subheader">Video Analysis</h2>', unsafe_allow_html=True)
            
            # Get all videos
            st.write("Fetching all videos from channel...")
            all_videos = get_all_videos(youtube, uploads_playlist_id, progress_container)
            
            if not all_videos:
                st.warning("No videos found for this channel.")
                return
            
            # Get detailed video information
            st.write(f"Getting detailed information for {len(all_videos)} videos...")
            video_details = get_video_details(youtube, all_videos, progress_container)
            
            if not video_details:
                st.warning("Could not retrieve video details.")
                return
            
            # Create DataFrame
            df = pd.DataFrame(video_details)
            
            # Sort by upload date (newest first)
            df = df.sort_values('upload_date', ascending=False)
            
            # Calculate views per hour metrics
            df = calculate_vph_metrics(df)
            
            # Display video data
            st.markdown("### Channel Videos")
            st.dataframe(
                df,
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
            
            # Calculate view ranges
            st.markdown("---")
            st.markdown('<h2 class="subheader">View Performance Ranges</h2>', unsafe_allow_html=True)
            
            view_ranges_df = calculate_view_ranges(df)
            
            # Display view ranges
            st.markdown("### Video View Performance by Age")
            st.write("This shows the typical view ranges for videos at different points in their lifecycle:")
            
            # Display table
            st.dataframe(
                view_ranges_df,
                column_config={
                    "day": st.column_config.NumberColumn("Day", format="%d"),
                    "lower_range": st.column_config.NumberColumn("Lower Range (25%)", format="%d"),
                    "median": st.column_config.NumberColumn("Median (50%)", format="%d"),
                    "upper_range": st.column_config.NumberColumn("Upper Range (75%)", format="%d"),
                    "max_range": st.column_config.NumberColumn("Top Performers (90%)", format="%d"),
                    "sample_size": "Sample Size"
                },
                hide_index=True
            )
            
            # Create Excel file
            st.markdown("---")
            st.markdown('<h2 class="subheader">Download Data</h2>', unsafe_allow_html=True)
            
            # Create Excel in memory
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Video Data', index=False)
                view_ranges_df.to_excel(writer, sheet_name='View Ranges', index=False)
            
            excel_buffer.seek(0)
            
            # Provide download button
            st.download_button(
                label="Download Excel Report",
                data=excel_buffer,
                file_name=f"{channel_info['snippet'].get('title', 'channel')}_youtube_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel"
            )

if __name__ == "__main__":
    main()
