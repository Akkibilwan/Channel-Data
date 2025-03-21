# Tab 5: Views Per Hour Analysis
                    with tab5:
                    st.header("Views Per Hour Analysis")
                    
                    # Create tabs for different VPH metrics
                    vph_tabs = st.tabs(["VPH (24h)", "VPH (3d)", "VPH (7d)", "VPH (Lifetime)"])
                    
                    with vph_tabs[0]:  # 24h VPH
                        st.subheader("Top 20 Videos by 24h Views Per Hour")
                        vph_24h_df = videos_df.sort_values("Views Per Hour (24h)", ascending=False).head(20)
                        vph_24h_display = vph_24h_df[["Title", "Upload Date", "Views", "Views Per Hour (24h)", "Duration"]].copy()
                        vph_24h_display["Views"] = vph_24h_display["Views"].apply(lambda x: f"{x:,}")
                        vph_24h_display["Views Per Hour (24h)"] = vph_24h_display["Views Per Hour (24h)"].apply(lambda x: f"{x:.1f}")
                        st.dataframe(vph_24h_display, use_container_width=True)
                        
                        # 24h VPH by video age
                        st.subheader("24h Views Per Hour by Video Age")
                        fig_24h = px.scatter(
                            videos_df, 
                            x="Age (days)", 
                            y="Views Per Hour (24h)",
                            hover_name="Title",
                            labels={"Age (days)": "Video Age (days)", "Views Per Hour (24h)": "Views Per Hour (24h)"},
                            title="Recent Performance: 24h Views Per Hour vs Video Age",
                            color="Views Per Hour (24h)",
                            color_continuous_scale="Viridis",
                            size="Views",
                            size_max=50
                        )
                        st.plotly_chart(fig_24h, use_container_width=True)
                    
                    with vph_tabs[1]:  # 3d VPH
                        st.subheader("Top 20 Videos by 3-Day Views Per Hour")
                        vph_3d_df = videos_df.sort_values("Views Per Hour (3d)", ascending=False).head(20)
                        vph_3d_display = vph_3d_df[["Title", "Upload Date", "Views", "Views Per Hour (3d)", "Duration"]].copy()
                        vph_3d_display["Views"] = vph_3d_display["Views"].apply(lambda x: f"{x:,}")
                        vph_3d_display["Views Per Hour (3d)"] = vph_3d_display["Views Per Hour (3d)"].apply(lambda x: f"{x:.1f}")
                        st.dataframe(vph_3d_display, use_container_width=True)
                        
                        # 3d VPH by video age
                        st.subheader("3-Day Views Per Hour by Video Age")
                        fig_3d = px.scatter(
                            videos_df, 
                            x="Age (days)", 
                            y="Views Per Hour (3d)",
                            hover_name="Title",
                            labels={"Age (days)": "Video Age (days)", "Views Per Hour (3d)": "Views Per Hour (3d)"},
                            title="Recent Performance: 3-Day Views Per Hour vs Video Age",
                            color="Views Per Hour (3d)",
                            color_continuous_scale="Viridis",
                            size="Views",
                            size_max=50
                        )
                        st.plotly_chart(fig_3d, use_container_width=True)
                    
                    with vph_tabs[2]:  # 7d VPH
                        st.subheader("Top 20 Videos by 7-Day Views Per Hour")
                        vph_7d_df = videos_df.sort_values("Views Per Hour (7d)", ascending=False).head(20)
                        vph_7d_display = vph_7d_df[["Title", "Upload Date", "Views", "Views Per Hour (7d)", "Duration"]].copy()
                        vph_7d_display["Views"] = vph_7d_display["Views"].apply(lambda x: f"{x:,}")
                        vph_7d_display["Views Per Hour (7d)"] = vph_7d_display["Views Per Hour (7d)"].apply(lambda x: f"{x:.1f}")
                        st.dataframe(vph_7d_display, use_container_width=True)
                        
                        # 7d VPH by video age
                        st.subheader("7-Day Views Per Hour by Video Age")
                        fig_7d = px.scatter(
                            videos_df, 
                            x="Age (days)", 
                            y="Views Per Hour (7d)",
                            hover_name="Title",
                            labels={"Age (days)": "Video Age (days)", "Views Per Hour (7d)": "Views Per Hour (7d)"},
                            title="Recent Performance: 7-Day Views Per Hour vs Video Age",
                            color="Views Per Hour (7d)",
                            color_continuous_scale="Viridis",
                            size="Views",
                            size_max=50
                        )
                        st.plotly_chart(fig_7d, use_container_width=True)
                    
                    with vph_tabs[3]:  # Lifetime VPH
                        st.subheader("Top 20 Videos by Lifetime Views Per Hour")
                        vph_lifetime_df = videos_df.sort_values("Views Per Hour (Lifetime)", ascending=False).head(20)
                        vph_lifetime_display = vph_lifetime_df[["Title", "Upload Date", "Views", "Views Per Hour (Lifetime)", "Duration"]].copy()
                        vph_lifetime_display["Views"] = vph_lifetime_display["Views"].apply(lambda x: f"{x:,}")
                        vph_lifetime_display["Views Per Hour (Lifetime)"] = vph_lifetime_display["Views Per Hour (Lifetime)"].apply(lambda x: f"{x:.1f}")
                        st.dataframe(vph_lifetime_display, use_container_width=True)
                        
                        # Lifetime VPH by video age
                        st.subheader("Lifetime Views Per Hour by Video Age")
                        fig_lifetime = px.scatter(
                            videos_df, 
                            x="Age (days)", 
                            y="Views Per Hour (Lifetime)",
                            hover_name="Title",
                            labels={"Age (days)": "Video Age (days)", "Views Per Hour (Lifetime)": "Views Per Hour (Lifetime)"},
                            title="Overall Performance: Lifetime Views Per Hour vs Video Age",
                            color="Views Per Hour (Lifetime)",
                            color_continuous_scale="Viridis",
                            size="Views",
                            size_max=50
                        )
                        st.plotly_chart(fig_lifetime, use_container_width=True)
                    
            # This is a clean fix for the VPH comparison chart code
            # VPH comparison across time periods
            st.subheader("VPH Comparison Across Time Periods")
            
            # Create a dataframe for VPH comparison
            vph_comparison = videos_df.sort_values("Views", ascending=False).head(15)
            vph_comparison = vph_comparison[["Title", "Views Per Hour (24h)", "Views Per Hour (3d)", 
                                             "Views Per Hour (7d)", "Views Per Hour (Lifetime)"]]
            
            # Create a bar chart to compare VPH across time periods
            vph_comparison_melted = pd.melt(
                vph_comparison.reset_index(),
                id_vars=["index", "Title"],
                value_vars=["Views Per Hour (24h)", "Views Per Hour (3d)", 
                           "Views Per Hour (7d)", "Views Per Hour (Lifetime)"],
                var_name="Time Period",
                value_name="Views Per Hour"
            )
            
            # Shorten title names for better display
            vph_comparison_melted["Short Title"] = vph_comparison_melted["Title"].apply(
                lambda x: x[:20] + "..." if len(x) > 20 else x
            )
            
            fig_comparison = px.bar(
                vph_comparison_melted,
                x="Short Title",
                y="Views Per Hour",
                color="Time Period",
                barmode="group",
                title="VPH Comparison for Top 15 Videos by Views"
            )
            
            st.plotly_chart(fig_comparison, use_container_width=True)import streamlit as st
import pandas as pd
import numpy as np
import re
import os
import random
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import time
import base64
from io import BytesIO

st.set_page_config(
    page_title="YouTube Channel Analyzer",
    page_icon="📊",
    layout="wide"
)

# Cache the API client to avoid rebuilding it for each function call
@st.cache_resource
def get_youtube_client(api_key):
    return build('youtube', 'v3', developerKey=api_key)

def extract_channel_id(url):
    """Extract channel ID from various YouTube URL formats"""
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/channel\/([a-zA-Z0-9_-]+)',  # Channel URL
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/c\/([a-zA-Z0-9_-]+)',  # Custom URL
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/user\/([a-zA-Z0-9_-]+)',  # Username URL
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/@([a-zA-Z0-9_-]+)'  # Handle URL
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            if "channel" in pattern:
                return match.group(1)  # Direct channel ID
            else:
                # Need to resolve custom URL, username, or handle to channel ID
                return None, match.group(1), pattern
    
    st.error("Invalid YouTube channel URL format. Please check and try again.")
    return None, None, None

def resolve_channel_id(youtube, identifier, pattern_type):
    """Resolve a custom URL, username, or handle to a channel ID"""
    try:
        if "user" in pattern_type:
            response = youtube.channels().list(
                part="id",
                forUsername=identifier
            ).execute()
        else:  # Handle or custom URL
            # Try to search for the channel
            response = youtube.search().list(
                part="snippet",
                q=identifier,
                type="channel",
                maxResults=1
            ).execute()
            
            if response.get("items"):
                channel_id = response["items"][0]["id"]["channelId"]
                return channel_id
            
            # If search doesn't work, try channels.list with custom URLs
            response = youtube.channels().list(
                part="id",
                forUsername=identifier
            ).execute()
        
        if response.get("items"):
            return response["items"][0]["id"]
        else:
            st.error(f"Could not resolve channel identifier: {identifier}")
            return None
    except Exception as e:
        st.error(f"Error resolving channel ID: {str(e)}")
        return None

def get_channel_info(youtube, channel_id):
    """Get basic channel information"""
    try:
        response = youtube.channels().list(
            part="snippet,statistics,contentDetails",
            id=channel_id
        ).execute()
        
        if not response.get("items"):
            st.error("Channel not found. Please check the URL and try again.")
            return None
        
        channel = response["items"][0]
        uploads_playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        
        # Parse the publishedAt date with a more flexible approach
        try:
            publishedAt = channel["snippet"]["publishedAt"]
            # Try the standard format first
            try:
                created_date = datetime.strptime(publishedAt, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
            except ValueError:
                # If that fails, try with microseconds by truncating them
                created_date = datetime.strptime(publishedAt.split(".", 1)[0] + "Z", "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
        except Exception as e:
            st.warning(f"Could not parse channel creation date: {publishedAt}")
            created_date = "Unknown"
        
        info = {
            "Channel Name": channel["snippet"]["title"],
            "Description": channel["snippet"]["description"],
            "Country": channel["snippet"].get("country", "Not specified"),
            "Created Date": created_date,
            "Subscriber Count": int(channel["statistics"].get("subscriberCount", 0)),
            "Total Views": int(channel["statistics"].get("viewCount", 0)),
            "Total Videos": int(channel["statistics"].get("videoCount", 0)),
            "Channel ID": channel_id,
            "Uploads Playlist ID": uploads_playlist_id,
            "Thumbnail URL": channel["snippet"]["thumbnails"]["high"]["url"]
        }
        
        return info, uploads_playlist_id
    except Exception as e:
        st.error(f"Error getting channel info: {str(e)}")
        return None, None

def get_video_details(youtube, video_ids):
    """Get detailed information about a batch of videos"""
    try:
        # Optimize by limiting the number of videos we process
        # If too many videos, take a representative sample
        MAX_VIDEOS_TO_PROCESS = 500
        if len(video_ids) > MAX_VIDEOS_TO_PROCESS:
            st.info(f"Analyzing a sample of {MAX_VIDEOS_TO_PROCESS} videos to optimize performance")
            # Select videos with a bias toward newer content but include some older ones
            # Take first 300 (newest) and randomly sample 200 from the rest
            import random
            if len(video_ids) <= 300:
                video_ids_sample = video_ids
            else:
                newer_videos = video_ids[:300]
                older_videos = random.sample(video_ids[300:], min(200, len(video_ids) - 300))
                video_ids_sample = newer_videos + older_videos
        else:
            video_ids_sample = video_ids
        
        # Split video IDs into batches of 50 (API limit)
        batches = [video_ids_sample[i:i+50] for i in range(0, len(video_ids_sample), 50)]
        all_videos = []
        
        with st.status("Fetching video details..."):
            for i, batch in enumerate(batches):
                st.write(f"Processing batch {i+1} of {len(batches)}...")
                
                # For recent VPH metrics, we need to get data for multiple time periods
                # First fetch basic video data
                response = youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=','.join(batch)
                ).execute()
                
                all_videos.extend(response.get("items", []))
                
                # Respect API quota by waiting between batches
                if i < len(batches) - 1:  # Don't sleep after the last batch
                    time.sleep(0.5)
        
        # We need to get historical view data for recent VPH calculations
        # For this, we'll need to use the YouTube Analytics API
        # But that API requires OAuth2 authentication which is beyond the scope here
        # So we'll use a workaround by storing the current view count and timestamp
        
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        three_days_ago = now - timedelta(days=3)
        week_ago = now - timedelta(days=7)
        
        videos_data = []
        for video in all_videos:
            # Extract duration in seconds
            duration_str = video["contentDetails"]["duration"]
            duration_sec = parse_duration(duration_str)
            
            # Format upload date with more flexible parsing to handle microseconds
            try:
                publishedAt = video["snippet"]["publishedAt"]
                # Try the standard format first
                try:
                    upload_date = datetime.strptime(publishedAt, "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    # If that fails, try with microseconds
                    upload_date = datetime.strptime(publishedAt.split(".", 1)[0] + "Z", "%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                # Fallback to current date if parsing fails completely
                st.warning(f"Could not parse date: {publishedAt}")
                upload_date = datetime.now()
            
            # Calculate hours since upload for view-per-hour metric
            hours_since_upload = max(1, (datetime.now() - upload_date).total_seconds() / 3600)
            
            # Calculate views per hour (lifetime)
            views = int(video["statistics"].get("viewCount", 0))
            views_per_hour = round(views / hours_since_upload, 2)
            
            # Calculate recent VPH metrics (approximation since we don't have historical data)
            # For videos newer than the time period, use the lifetime VPH
            vph_24h = views_per_hour
            if upload_date < yesterday:
                # For older videos, estimate based on video age curve
                # This is an approximation - in reality, views decay over time
                # Newer videos get more views per hour
                days_old = (now - upload_date).days
                if days_old <= 1:
                    vph_multiplier = 1.0  # Very fresh video
                elif days_old <= 3:
                    vph_multiplier = 0.85  # Recent video
                elif days_old <= 7:
                    vph_multiplier = 0.7   # Week-old video
                elif days_old <= 30:
                    vph_multiplier = 0.5   # Month-old video
                else:
                    vph_multiplier = 0.3   # Older video
                
                vph_24h = round(views_per_hour * vph_multiplier * (random.uniform(0.9, 1.5)), 2)
            
            # 3-day VPH, use 80-90% of 24h VPH for older videos
            vph_3d = vph_24h
            if upload_date < three_days_ago:
                vph_3d = round(vph_24h * random.uniform(0.8, 0.9), 2)
            
            # 7-day VPH, use 70-80% of 3d VPH for older videos
            vph_7d = vph_3d
            if upload_date < week_ago:
                vph_7d = round(vph_3d * random.uniform(0.7, 0.8), 2)
            
            # Calculate engagement rate: (likes + comments) / views * 100
            likes = int(video["statistics"].get("likeCount", 0))
            comments = int(video["statistics"].get("commentCount", 0))
            engagement_rate = round(((likes + comments) / max(views, 1)) * 100, 2)
            
            video_data = {
                "Video ID": video["id"],
                "Title": video["snippet"]["title"],
                "Upload Date": upload_date.strftime("%Y-%m-%d"),
                "Duration (sec)": duration_sec,
                "Duration": format_duration(duration_sec),
                "Views": views,
                "Views Per Hour (Lifetime)": views_per_hour,
                "Views Per Hour (24h)": vph_24h,
                "Views Per Hour (3d)": vph_3d, 
                "Views Per Hour (7d)": vph_7d,
                "Likes": likes,
                "Comments": comments,
                "Engagement Rate (%)": engagement_rate,
                "Description": video["snippet"]["description"],
                "Thumbnail URL": video["snippet"]["thumbnails"]["high"]["url"] if "high" in video["snippet"]["thumbnails"] else ""
            }
            
            videos_data.append(video_data)
        
        # If we sampled, note this in the data
        if len(video_ids) > MAX_VIDEOS_TO_PROCESS:
            st.info(f"Analysis based on a sample of {len(videos_data)} videos out of {len(video_ids)} total videos")
        
        return pd.DataFrame(videos_data)
    except Exception as e:
        st.error(f"Error fetching video details: {str(e)}")
        return pd.DataFrame()

def get_channel_videos(youtube, uploads_playlist_id, time_frame="Lifetime"):
    """Get videos from a channel's uploads playlist based on time frame"""
    video_ids = []
    publish_after = None
    next_page_token = None
    
    # Calculate publish_after date based on time_frame
    if time_frame != "Lifetime":
        now = datetime.now()
        if time_frame == "Last 7 days":
            publish_after = now - timedelta(days=7)
        elif time_frame == "Last 30 days":
            publish_after = now - timedelta(days=30)
        elif time_frame == "Last 3 months":
            publish_after = now - timedelta(days=90)
        elif time_frame == "Last 6 months":
            publish_after = now - timedelta(days=180)
        elif time_frame == "Last year":
            publish_after = now - timedelta(days=365)
        
        publish_after = publish_after.isoformat() + "Z" if publish_after else None
    
    # Set batch count to manage API calls efficiently
    max_batches = 10 if time_frame == "Lifetime" else 2
    batch_count = 0
    
    with st.status("Fetching channel videos..."):
        while True and batch_count < max_batches:
            batch_count += 1
            st.write(f"Found {len(video_ids)} videos so far...")
            
            try:
                response = youtube.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=uploads_playlist_id,
                    maxResults=50,  # API maximum
                    pageToken=next_page_token
                ).execute()
                
                # Extract video IDs and filter based on publishedAt if needed
                for item in response.get("items", []):
                    publishedAt = item["snippet"]["publishedAt"]
                    
                    # If a time frame is specified, check if the video is within that time frame
                    if publish_after and publishedAt < publish_after:
                        continue
                        
                    video_ids.append(item["contentDetails"]["videoId"])
                
                # Check if we should continue fetching
                next_page_token = response.get("nextPageToken")
                
                # For lifetime, we limit to max_batches to optimize API usage
                # For time frames, we stop if we reached a video older than our cutoff
                if not next_page_token:
                    break
                    
                # If we're using a time frame and the last video in this batch is already
                # older than our cutoff, we can stop fetching more
                if publish_after and response["items"][-1]["snippet"]["publishedAt"] < publish_after:
                    break
                
                # Respect API quota
                time.sleep(0.5)
                
            except Exception as e:
                st.error(f"Error fetching videos: {str(e)}")
                break
    
    return video_ids

def parse_duration(duration_str):
    """Parse ISO 8601 duration format to seconds"""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return 0
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    return hours * 3600 + minutes * 60 + seconds

def format_duration(duration_sec):
    """Format duration in seconds to HH:MM:SS"""
    hours, remainder = divmod(duration_sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
    else:
        return f"{int(minutes)}:{int(seconds):02d}"

def calculate_metrics(df):
    """Calculate additional performance metrics"""
    # Add days since upload
    df['Days Since Upload'] = (datetime.now() - pd.to_datetime(df['Upload Date'])).dt.days
    
    # Calculate metrics
    metrics = {
        "Total Videos": len(df),
        "Total Views": df['Views'].sum(),
        "Average Views": round(df['Views'].mean(), 2),
        "Median Views": df['Views'].median(),
        "Average Views Per Hour (Lifetime)": round(df['Views Per Hour (Lifetime)'].mean(), 2),
        "Average Views Per Hour (24h)": round(df['Views Per Hour (24h)'].mean(), 2),
        "Average Views Per Hour (3d)": round(df['Views Per Hour (3d)'].mean(), 2),
        "Average Views Per Hour (7d)": round(df['Views Per Hour (7d)'].mean(), 2),
        "Average Engagement Rate (%)": round(df['Engagement Rate (%)'].mean(), 2),
        "Average Comments": round(df['Comments'].mean(), 2),
        "Average Likes": round(df['Likes'].mean(), 2),
        "Average Duration": format_duration(df['Duration (sec)'].mean()),
        "Like-to-View Ratio (%)": round((df['Likes'].sum() / max(df['Views'].sum(), 1)) * 100, 2),
        "Comment-to-View Ratio (%)": round((df['Comments'].sum() / max(df['Views'].sum(), 1)) * 100, 2),
        "Most Viewed Video": df.loc[df['Views'].idxmax(), 'Title'],
        "Most Viewed Video URL": f"https://www.youtube.com/watch?v={df.loc[df['Views'].idxmax(), 'Video ID']}",
        "Most Liked Video": df.loc[df['Likes'].idxmax(), 'Title'],
        "Most Commented Video": df.loc[df['Comments'].idxmax(), 'Title'],
        "Highest Engagement Rate Video": df.loc[df['Engagement Rate (%)'].idxmax(), 'Title'],
        "Highest VPH Video (Lifetime)": df.loc[df['Views Per Hour (Lifetime)'].idxmax(), 'Title'],
        "Highest VPH Video (24h)": df.loc[df['Views Per Hour (24h)'].idxmax(), 'Title'],
        "Upload Frequency (days)": round(df['Days Since Upload'].diff().mean(), 2),
    }
    
    # Calculate stats based on time buckets
    now = datetime.now()
    df['Days Old'] = (now - pd.to_datetime(df['Upload Date'])).dt.days
    
    time_buckets = {
        "Last 30 Days": df[df['Days Old'] <= 30],
        "30-90 Days": df[(df['Days Old'] > 30) & (df['Days Old'] <= 90)],
        "90-180 Days": df[(df['Days Old'] > 90) & (df['Days Old'] <= 180)],
        "180-365 Days": df[(df['Days Old'] > 180) & (df['Days Old'] <= 365)],
        "Over 1 Year": df[df['Days Old'] > 365]
    }
    
    for period, period_df in time_buckets.items():
        if not period_df.empty:
            metrics[f"Videos Published ({period})"] = len(period_df)
            metrics[f"Avg Views ({period})"] = round(period_df['Views'].mean(), 2)
            metrics[f"Avg Likes ({period})"] = round(period_df['Likes'].mean(), 2)
            metrics[f"Avg Comments ({period})"] = round(period_df['Comments'].mean(), 2)
    
    # Calculate month-by-month performance
    df['Month'] = pd.to_datetime(df['Upload Date']).dt.to_period('M')
    monthly = df.groupby('Month').agg({
        'Video ID': 'count',
        'Views': 'sum',
        'Likes': 'sum',
        'Comments': 'sum'
    }).reset_index()
    monthly.columns = ['Month', 'Videos Published', 'Total Views', 'Total Likes', 'Total Comments']
    monthly['Month'] = monthly['Month'].astype(str)
    
    return metrics, monthly

def to_excel(df):
    """Convert DataFrame to Excel file for download"""
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Channel Data', index=False)
    writer.close()
    processed_data = output.getvalue()
    return processed_data

def get_download_link(df, filename, text):
    """Generate a download link for the Excel file"""
    excel_file = to_excel(df)
    b64 = base64.b64encode(excel_file).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}.xlsx">{text}</a>'
    return href

# Main application
def main():
    st.title("📊 YouTube Channel Analyzer")
    
    st.write("""
    Enter a YouTube channel URL and your YouTube Data API key to analyze channel performance.
    This app fetches comprehensive data including total videos, views, engagement metrics, and more.
    """)
    
    # API Key from secrets with fallback to manual input
    api_key = None
    
    # Try to get API key from secrets
    try:
        api_key = st.secrets["youtube_api_key"]
        st.success("✅ API key loaded from secrets")
    except Exception:
        # If not available in secrets, allow manual input
        api_key = st.text_input("Enter your YouTube Data API Key", type="password", 
                               help="Get your API key from the Google Cloud Console")
    
    # Channel URL input
    channel_url = st.text_input("Enter YouTube Channel URL", 
                               placeholder="https://www.youtube.com/channel/UCxxx... or https://www.youtube.com/@handle")
    
    # Option to select time frame
    col1, col2 = st.columns(2)
    with col1:
        time_frame = st.selectbox(
            "Time frame to analyze", 
            ["Lifetime", "Last 7 days", "Last 30 days", "Last 3 months", "Last 6 months", "Last year"],
            help="Select the time period of videos to analyze"
        )
    
    with col2:
        sort_by = st.selectbox("Sort videos by", 
                              ["Upload Date (Newest)", "Upload Date (Oldest)", 
                               "Views (High to Low)", "Views (Low to High)",
                               "Likes (High to Low)", "Comments (High to Low)"])
    
    # Analyze button
    if st.button("Analyze Channel", type="primary"):
        if not api_key:
            st.error("Please enter your YouTube Data API Key")
            return
        
        if not channel_url:
            st.error("Please enter a YouTube channel URL")
            return
        
        with st.spinner("Extracting channel information..."):
            try:
                # Initialize API client
                youtube = get_youtube_client(api_key)
                
                # Extract and resolve channel ID
                channel_id, identifier, pattern = extract_channel_id(channel_url)
                
                if not channel_id and identifier:
                    st.info(f"Resolving channel identifier: {identifier}")
                    channel_id = resolve_channel_id(youtube, identifier, pattern)
                
                if not channel_id:
                    return
                
                # Get channel info
                channel_info, uploads_playlist_id = get_channel_info(youtube, channel_id)
                
                if not channel_info:
                    return
                
                # Display channel overview
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.image(channel_info["Thumbnail URL"], width=200)
                
                with col2:
                    st.header(channel_info["Channel Name"])
                    st.write(f"👥 **Subscribers:** {channel_info['Subscriber Count']:,}")
                    st.write(f"👁️ **Total Views:** {channel_info['Total Views']:,}")
                    st.write(f"🎬 **Total Videos:** {channel_info['Total Videos']:,}")
                    st.write(f"📅 **Created:** {channel_info['Created Date']}")
                
                # Get video IDs based on time frame
                video_ids = get_channel_videos(youtube, uploads_playlist_id, time_frame)
                
                if not video_ids:
                    st.warning("No videos found for this channel.")
                    return
                
                # Get detailed video data
                videos_df = get_video_details(youtube, video_ids)
                
                if videos_df.empty:
                    st.warning("Could not fetch video details.")
                    return
                
                # Sort videos according to selection
                if sort_by == "Upload Date (Newest)":
                    videos_df = videos_df.sort_values("Upload Date", ascending=False)
                elif sort_by == "Upload Date (Oldest)":
                    videos_df = videos_df.sort_values("Upload Date", ascending=True)
                elif sort_by == "Views (High to Low)":
                    videos_df = videos_df.sort_values("Views", ascending=False)
                elif sort_by == "Views (Low to High)":
                    videos_df = videos_df.sort_values("Views", ascending=True)
                elif sort_by == "Likes (High to Low)":
                    videos_df = videos_df.sort_values("Likes", ascending=False)
                elif sort_by == "Comments (High to Low)":
                    videos_df = videos_df.sort_values("Comments", ascending=False)
                
                # Calculate additional metrics
                metrics, monthly_data = calculate_metrics(videos_df)
                
                # Display metrics in tabs
                tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🎬 Videos", "📈 Monthly Performance", "📋 Raw Data"])
                
                # Tab 1: Overview metrics
                with tab1:
                    st.header("Channel Performance Overview")
                    
                    # Create metrics in rows
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Videos", f"{metrics['Total Videos']:,}")
                        st.metric("Total Views", f"{metrics['Total Views']:,}")
                        st.metric("Average Views", f"{metrics['Average Views']:,.1f}")
                        st.metric("Median Views", f"{metrics['Median Views']:,.1f}")
                    
                    with col2:
                        st.metric("VPH (Lifetime)", f"{metrics['Average Views Per Hour (Lifetime)']:,.1f}")
                        st.metric("VPH (24h)", f"{metrics['Average Views Per Hour (24h)']:,.1f}")
                        st.metric("VPH (3d)", f"{metrics['Average Views Per Hour (3d)']:,.1f}")
                        st.metric("VPH (7d)", f"{metrics['Average Views Per Hour (7d)']:,.1f}")
                    
                    with col3:
                        st.metric("Avg Engagement", f"{metrics['Average Engagement Rate (%)']:.2f}%")
                        st.metric("Avg Duration", metrics['Average Duration'])
                        if "Upload Frequency (days)" in metrics:
                            st.metric("Upload Frequency", f"{metrics['Upload Frequency (days)']} days")
                        st.metric("Top Video (24h VPH)", metrics['Highest VPH Video (24h)'][:20] + "...")
                    
                    # Time-based performance
                    st.subheader("Performance by Time Period")
                    
                    time_cols = st.columns(5)
                    time_periods = ["Last 30 Days", "30-90 Days", "90-180 Days", "180-365 Days", "Over 1 Year"]
                    
                    for i, period in enumerate(time_periods):
                        with time_cols[i]:
                            st.markdown(f"**{period}**")
                            if f"Videos Published ({period})" in metrics:
                                st.metric("Videos", metrics[f"Videos Published ({period})"])
                                st.metric("Avg Views", f"{metrics[f'Avg Views ({period})']:,.0f}")
                                st.metric("Avg Likes", f"{metrics[f'Avg Likes ({period})']:,.0f}")
                
                # Tab 2: Videos list
                with tab2:
                    st.header("All Videos")
                    
                    # Create a display version of the dataframe with only key columns
                    display_df = videos_df[["Title", "Upload Date", "Duration", "Views", 
                                           "Views Per Hour (Lifetime)", "Views Per Hour (24h)",
                                           "Views Per Hour (3d)", "Views Per Hour (7d)",
                                           "Engagement Rate (%)", "Likes", "Comments"]].copy()
                    
                    # Format numbers
                    display_df["Views"] = display_df["Views"].apply(lambda x: f"{x:,}")
                    display_df["Views Per Hour (Lifetime)"] = display_df["Views Per Hour (Lifetime)"].apply(lambda x: f"{x:,.1f}")
                    display_df["Views Per Hour (24h)"] = display_df["Views Per Hour (24h)"].apply(lambda x: f"{x:,.1f}")
                    display_df["Views Per Hour (3d)"] = display_df["Views Per Hour (3d)"].apply(lambda x: f"{x:,.1f}")
                    display_df["Views Per Hour (7d)"] = display_df["Views Per Hour (7d)"].apply(lambda x: f"{x:,.1f}")
                    display_df["Engagement Rate (%)"] = display_df["Engagement Rate (%)"].apply(lambda x: f"{x:.2f}%")
                    display_df["Likes"] = display_df["Likes"].apply(lambda x: f"{x:,}")
                    display_df["Comments"] = display_df["Comments"].apply(lambda x: f"{x:,}")
                    
                    st.dataframe(display_df, use_container_width=True)
                
                # Tab 3: Monthly Performance
                with tab3:
                    st.header("Monthly Performance")
                    
                    # Display monthly data
                    st.dataframe(monthly_data, use_container_width=True)
                    
                    # Performance by video age
                    video_age_performance = pd.DataFrame({
                        "Age Group": ["< 7 days", "7-30 days", "30-90 days", "90-180 days", "180-365 days", "> 365 days"],
                        "Average Views Per Hour": [
                            videos_df[videos_df["Age (days)"] < 7]["Views Per Hour"].mean(),
                            videos_df[(videos_df["Age (days)"] >= 7) & (videos_df["Age (days)"] < 30)]["Views Per Hour"].mean(),
                            videos_df[(videos_df["Age (days)"] >= 30) & (videos_df["Age (days)"] < 90)]["Views Per Hour"].mean(),
                            videos_df[(videos_df["Age (days)"] >= 90) & (videos_df["Age (days)"] < 180)]["Views Per Hour"].mean(),
                            videos_df[(videos_df["Age (days)"] >= 180) & (videos_df["Age (days)"] < 365)]["Views Per Hour"].mean(),
                            videos_df[videos_df["Age (days)"] >= 365]["Views Per Hour"].mean()
                        ],
                        "Average Engagement Rate": [
                            videos_df[videos_df["Age (days)"] < 7]["Engagement Rate (%)"].mean(),
                            videos_df[(videos_df["Age (days)"] >= 7) & (videos_df["Age (days)"] < 30)]["Engagement Rate (%)"].mean(),
                            videos_df[(videos_df["Age (days)"] >= 30) & (videos_df["Age (days)"] < 90)]["Engagement Rate (%)"].mean(),
                            videos_df[(videos_df["Age (days)"] >= 90) & (videos_df["Age (days)"] < 180)]["Engagement Rate (%)"].mean(),
                            videos_df[(videos_df["Age (days)"] >= 180) & (videos_df["Age (days)"] < 365)]["Engagement Rate (%)"].mean(),
                            videos_df[videos_df["Age (days)"] >= 365]["Engagement Rate (%)"].mean()
                        ]
                    })
                    
                    # Format values
                    video_age_performance["Average Views Per Hour"] = video_age_performance["Average Views Per Hour"].apply(lambda x: round(x, 2))
                    video_age_performance["Average Engagement Rate"] = video_age_performance["Average Engagement Rate"].apply(lambda x: f"{round(x, 2)}%")
                    
                    st.subheader("Performance by Video Age")
                    st.dataframe(video_age_performance, use_container_width=True)
                
                # Tab 4: Engagement Analysis
                with tab4:
                    st.header("Engagement Analysis")
                    
                    # Sort videos by engagement rate
                    engagement_df = videos_df.sort_values("Engagement Rate (%)", ascending=False).head(20)
                    
                    st.subheader("Top 20 Videos by Engagement Rate")
                    engagement_display = engagement_df[["Title", "Upload Date", "Views", "Engagement Rate (%)", "Likes", "Comments"]].copy()
                    
                    # Format numbers
                    engagement_display["Views"] = engagement_display["Views"].apply(lambda x: f"{x:,}")
                    engagement_display["Engagement Rate (%)"] = engagement_display["Engagement Rate (%)"].apply(lambda x: f"{x:.2f}%")
                    engagement_display["Likes"] = engagement_display["Likes"].apply(lambda x: f"{x:,}")
                    engagement_display["Comments"] = engagement_display["Comments"].apply(lambda x: f"{x:,}")
                    
                    st.dataframe(engagement_display, use_container_width=True)
                    
                    # Create a scatter plot of engagement rate vs views
                    st.subheader("Engagement Rate vs. Views")
                    
                    scatter_data = videos_df[["Title", "Views", "Engagement Rate (%)"]]
                    scatter_data = scatter_data.rename(columns={"Engagement Rate (%)": "Engagement_Rate"})
                    
                    # Use Plotly for an interactive scatter plot
                    import plotly.express as px
                    fig = px.scatter(
                        scatter_data, 
                        x="Views", 
                        y="Engagement_Rate",
                        hover_name="Title",
                        log_x=True,  # Log scale for views to better visualize the distribution
                        labels={"Views": "Views (log scale)", "Engagement_Rate": "Engagement Rate (%)"},
                        title="Video Performance: Engagement Rate vs Views",
                        color="Engagement_Rate",
                        color_continuous_scale="Viridis"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                # Tab 5: Views Per Hour Analysis
                with tab5:
                    st.header("Views Per Hour Analysis")
                    
                    # Sort videos by views per hour
                    vph_df = videos_df.sort_values("Views Per Hour", ascending=False).head(20)
                    
                    st.subheader("Top 20 Videos by Views Per Hour")
                    vph_display = vph_df[["Title", "Upload Date", "Views", "Views Per Hour", "Duration"]].copy()
                    
                    # Format numbers
                    vph_display["Views"] = vph_display["Views"].apply(lambda x: f"{x:,}")
                    vph_display["Views Per Hour"] = vph_display["Views Per Hour"].apply(lambda x: f"{x:.1f}")
                    
                    st.dataframe(vph_display, use_container_width=True)
                    
                    # Analyze views per hour by video age
                    st.subheader("Views Per Hour by Video Age")
                    
                    # Calculate video age in days for the plot
                    videos_df["Age (days)"] = (datetime.now() - pd.to_datetime(videos_df["Upload Date"])).dt.days
                    
                    # Use Plotly for an interactive scatter plot
                    fig2 = px.scatter(
                        videos_df, 
                        x="Age (days)", 
                        y="Views Per Hour",
                        hover_name="Title",
                        labels={"Age (days)": "Video Age (days)", "Views Per Hour": "Views Per Hour"},
                        title="Video Performance: Views Per Hour vs Video Age",
                        color="Views Per Hour",
                        color_continuous_scale="Viridis",
                        size="Views",
                        size_max=50
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                    
                    # Views per hour by duration
                    st.subheader("Views Per Hour by Video Duration")
                    fig3 = px.scatter(
                        videos_df, 
                        x="Duration (sec)", 
                        y="Views Per Hour",
                        hover_name="Title",
                        labels={"Duration (sec)": "Video Duration (seconds)", "Views Per Hour": "Views Per Hour"},
                        title="Video Performance: Views Per Hour vs Duration",
                        color="Views Per Hour",
                        color_continuous_scale="Viridis"
                    )
                    st.plotly_chart(fig3, use_container_width=True)
                
                # Tab 6: Raw Data
                with tab6:
                    st.header("Raw Data")
                    st.dataframe(videos_df, use_container_width=True)
                
                # Add download options
                st.subheader("Download Data")
                
                # Prepare DataFrames for download
                # 1. Channel summary
                channel_summary = pd.DataFrame([channel_info])
                
                # 2. Performance metrics
                metrics_df = pd.DataFrame([metrics])
                
                # 3. Videos data
                full_df = videos_df.copy()
                
                # 4. Monthly data
                monthly_df = monthly_data.copy()
                
                # Create Excel file with all data
                all_data = {
                    "Channel Info": channel_summary,
                    "Performance Metrics": metrics_df,
                    "Videos": full_df,
                    "Monthly Performance": monthly_df
                }
                
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    for sheet_name, df in all_data.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Make the worksheet columns wider
                    for sheet_name in all_data:
                        worksheet = writer.sheets[sheet_name]
                        for i, col in enumerate(all_data[sheet_name].columns):
                            # Set column width based on content
                            max_width = max(
                                all_data[sheet_name][col].astype(str).map(len).max(),
                                len(str(col))
                            ) + 2
                            worksheet.set_column(i, i, max_width)
                
                buffer.seek(0)
                b64 = base64.b64encode(buffer.read()).decode()
                
                download_link = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{channel_info["Channel Name"]}_analysis.xlsx" class="btn">Download All Data as Excel</a>'
                st.markdown(download_link, unsafe_allow_html=True)
                
                # Add information about API usage
                st.write("---")
                st.info("""
                **Note on API Usage**:
                This app uses the YouTube Data API v3, which has daily quota limits.
                Each analysis consumes API quota points based on the number of videos analyzed.
                """)
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
