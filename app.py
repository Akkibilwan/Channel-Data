import streamlit as st
import pandas as pd
import numpy as np
import re
import os
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
        
        info = {
            "Channel Name": channel["snippet"]["title"],
            "Description": channel["snippet"]["description"],
            "Country": channel["snippet"].get("country", "Not specified"),
            "Created Date": datetime.strptime(channel["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d"),
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
        # Split video IDs into batches of 50 (API limit)
        batches = [video_ids[i:i+50] for i in range(0, len(video_ids), 50)]
        all_videos = []
        
        with st.status("Fetching video details..."):
            for i, batch in enumerate(batches):
                st.write(f"Processing batch {i+1} of {len(batches)}...")
                response = youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=','.join(batch)
                ).execute()
                
                all_videos.extend(response.get("items", []))
                
                # Respect API quota by waiting between batches
                if i < len(batches) - 1:  # Don't sleep after the last batch
                    time.sleep(0.5)
        
        videos_data = []
        for video in all_videos:
            # Extract duration in seconds
            duration_str = video["contentDetails"]["duration"]
            duration_sec = parse_duration(duration_str)
            
            # Format upload date
            upload_date = datetime.strptime(
                video["snippet"]["publishedAt"], 
                "%Y-%m-%dT%H:%M:%SZ"
            )
            
            video_data = {
                "Video ID": video["id"],
                "Title": video["snippet"]["title"],
                "Upload Date": upload_date.strftime("%Y-%m-%d"),
                "Duration (sec)": duration_sec,
                "Duration": format_duration(duration_sec),
                "Views": int(video["statistics"].get("viewCount", 0)),
                "Likes": int(video["statistics"].get("likeCount", 0)),
                "Comments": int(video["statistics"].get("commentCount", 0)),
                "Description": video["snippet"]["description"],
                "Thumbnail URL": video["snippet"]["thumbnails"]["high"]["url"] if "high" in video["snippet"]["thumbnails"] else ""
            }
            
            videos_data.append(video_data)
        
        return pd.DataFrame(videos_data)
    except Exception as e:
        st.error(f"Error fetching video details: {str(e)}")
        return pd.DataFrame()

def get_channel_videos(youtube, uploads_playlist_id, max_results=None):
    """Get all videos from a channel's uploads playlist"""
    video_ids = []
    next_page_token = None
    
    with st.status("Fetching channel videos..."):
        while True:
            st.write(f"Found {len(video_ids)} videos so far...")
            
            try:
                response = youtube.playlistItems().list(
                    part="contentDetails",
                    playlistId=uploads_playlist_id,
                    maxResults=50,  # API maximum
                    pageToken=next_page_token
                ).execute()
                
                # Extract video IDs
                for item in response.get("items", []):
                    video_ids.append(item["contentDetails"]["videoId"])
                
                # Check if we should continue fetching
                next_page_token = response.get("nextPageToken")
                
                if not next_page_token or (max_results and len(video_ids) >= max_results):
                    break
                
                # Respect API quota
                time.sleep(0.5)
                
            except Exception as e:
                st.error(f"Error fetching videos: {str(e)}")
                break
    
    # Limit results if specified
    if max_results:
        video_ids = video_ids[:max_results]
    
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
        "Average Comments": round(df['Comments'].mean(), 2),
        "Average Likes": round(df['Likes'].mean(), 2),
        "Average Duration": format_duration(df['Duration (sec)'].mean()),
        "Like-to-View Ratio (%)": round((df['Likes'].sum() / max(df['Views'].sum(), 1)) * 100, 2),
        "Comment-to-View Ratio (%)": round((df['Comments'].sum() / max(df['Views'].sum(), 1)) * 100, 2),
        "Most Viewed Video": df.loc[df['Views'].idxmax(), 'Title'],
        "Most Viewed Video URL": f"https://www.youtube.com/watch?v={df.loc[df['Views'].idxmax(), 'Video ID']}",
        "Most Liked Video": df.loc[df['Likes'].idxmax(), 'Title'],
        "Most Commented Video": df.loc[df['Comments'].idxmax(), 'Title'],
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
    
    # Option to limit number of videos
    col1, col2 = st.columns(2)
    with col1:
        max_videos = st.number_input("Maximum videos to analyze (0 for all)", 
                                    min_value=0, value=0, 
                                    help="Set to 0 to analyze all videos (may take longer)")
    
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
                
                # Get video IDs
                max_to_fetch = max_videos if max_videos > 0 else None
                video_ids = get_channel_videos(youtube, uploads_playlist_id, max_to_fetch)
                
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
                        st.metric("Average Views", f"{metrics['Average Views']:,}")
                        st.metric("Median Views", f"{metrics['Median Views']:,}")
                    
                    with col2:
                        st.metric("Average Likes", f"{metrics['Average Likes']:,}")
                        st.metric("Average Comments", f"{metrics['Average Comments']:,}")
                        st.metric("Like-to-View Ratio", f"{metrics['Like-to-View Ratio (%)']}%")
                        st.metric("Comment-to-View Ratio", f"{metrics['Comment-to-View Ratio (%)']}%")
                    
                    with col3:
                        st.metric("Average Duration", metrics['Average Duration'])
                        if "Upload Frequency (days)" in metrics:
                            st.metric("Upload Frequency", f"{metrics['Upload Frequency (days)']} days")
                        st.metric("Most Viewed Video", metrics['Most Viewed Video'][:20] + "...")
                        st.write(f"[View on YouTube]({metrics['Most Viewed Video URL']})")
                    
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
                    display_df = videos_df[["Title", "Upload Date", "Duration", "Views", "Likes", "Comments"]].copy()
                    
                    # Format numbers
                    display_df["Views"] = display_df["Views"].apply(lambda x: f"{x:,}")
                    display_df["Likes"] = display_df["Likes"].apply(lambda x: f"{x:,}")
                    display_df["Comments"] = display_df["Comments"].apply(lambda x: f"{x:,}")
                    
                    st.dataframe(display_df, use_container_width=True)
                
                # Tab 3: Monthly Performance
                with tab3:
                    st.header("Monthly Performance")
                    
                    # Display monthly data
                    st.dataframe(monthly_data, use_container_width=True)
                    
                    # Create monthly charts
                    monthly_data_sorted = monthly_data.sort_values('Month')
                    
                    # Views chart
                    st.subheader("Monthly Views")
                    st.line_chart(monthly_data_sorted.set_index('Month')['Total Views'])
                    
                    # Videos published chart
                    st.subheader("Videos Published per Month")
                    st.bar_chart(monthly_data_sorted.set_index('Month')['Videos Published'])
                    
                    # Engagement chart
                    st.subheader("Monthly Engagement")
                    engagement_df = monthly_data_sorted.set_index('Month')[['Total Likes', 'Total Comments']]
                    st.line_chart(engagement_df)
                
                # Tab 4: Raw Data
                with tab4:
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
