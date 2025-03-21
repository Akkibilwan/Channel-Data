import streamlit as st
import pandas as pd
import numpy as np
import re
import os
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import time
from io import BytesIO

st.set_page_config(
    page_title="YouTube Channel Analyzer",
    page_icon="📊",
    layout="wide"
)

@st.cache_resource
def get_youtube_client(api_key):
    return build('youtube', 'v3', developerKey=api_key)

# Utility functions
def parse_duration(duration_str):
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds

def format_duration(duration_sec):
    hours, remainder = divmod(duration_sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}" if hours > 0 else f"{int(minutes)}:{int(seconds):02d}"

# Extract and resolve channel ID
def extract_channel_id(url):
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/channel\/([a-zA-Z0-9_-]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/c\/([a-zA-Z0-9_-]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/user\/([a-zA-Z0-9_-]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/@([a-zA-Z0-9_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return (match.group(1), None, pattern) if "channel" in pattern else (None, match.group(1), pattern)
    st.error("Invalid YouTube channel URL format.")
    return None, None, None

# Resolve custom URLs or handles
def resolve_channel_id(youtube, identifier, pattern_type):
    try:
        if "user" in pattern_type:
            response = youtube.channels().list(part="id", forUsername=identifier).execute()
        else:
            response = youtube.search().list(part="snippet", q=identifier, type="channel", maxResults=1).execute()
            if response.get("items"):
                return response["items"][0]["id"]["channelId"]
            response = youtube.channels().list(part="id", forUsername=identifier).execute()
        return response["items"][0]["id"] if response.get("items") else None
    except Exception as e:
        st.error(f"Error resolving channel ID: {str(e)}")
        return None

# Fetch channel info
def get_channel_info(youtube, channel_id):
    response = youtube.channels().list(part="snippet,statistics,contentDetails", id=channel_id).execute()
    if not response.get("items"):
        st.error("Channel not found.")
        return None, None
    channel = response["items"][0]
    uploads_playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    publishedAt = channel["snippet"]["publishedAt"]
    try:
        created_date = datetime.strptime(publishedAt, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
    except:
        created_date = "Unknown"
    info = {
        "Channel Name": channel["snippet"]["title"],
        "Subscribers": int(channel["statistics"].get("subscriberCount", 0)),
        "Total Views": int(channel["statistics"].get("viewCount", 0)),
        "Total Videos": int(channel["statistics"].get("videoCount", 0)),
        "Created Date": created_date,
        "Thumbnail URL": channel["snippet"]["thumbnails"]["high"]["url"]
    }
    return info, uploads_playlist_id

# Fetch videos
def get_video_details(youtube, video_ids):
    batches = [video_ids[i:i+50] for i in range(0, len(video_ids), 50)]
    all_videos = []
    for batch in batches:
        response = youtube.videos().list(part="snippet,contentDetails,statistics", id=','.join(batch)).execute()
        all_videos.extend(response.get("items", []))
        time.sleep(0.3)
    videos_data = []
    for video in all_videos:
        duration_sec = parse_duration(video["contentDetails"]["duration"])
        upload_date = datetime.strptime(video["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")
        hours_since_upload = max(1, (datetime.now() - upload_date).total_seconds() / 3600)
        views = int(video["statistics"].get("viewCount", 0))
        vph_24h = round(views / min(hours_since_upload, 24), 2)
        vph_3d = round(views / min(hours_since_upload, 72), 2)
        vph_1w = round(views / min(hours_since_upload, 168), 2)
        vph_1m = round(views / min(hours_since_upload, 720), 2)
        videos_data.append({
            "Video ID": video["id"],
            "Title": video["snippet"]["title"],
            "Upload Date": upload_date.strftime("%Y-%m-%d"),
            "Duration (sec)": duration_sec,
            "Duration": format_duration(duration_sec),
            "Views": views,
            "Views Per Hour": round(views / hours_since_upload, 2),
            "VPH (24h)": vph_24h,
            "VPH (3d)": vph_3d,
            "VPH (1w)": vph_1w,
            "VPH (1m)": vph_1m,
            "Likes": int(video["statistics"].get("likeCount", 0)),
            "Comments": int(video["statistics"].get("commentCount", 0)),
            "Engagement Rate (%)": round(((int(video["statistics"].get("likeCount", 0)) + int(video["statistics"].get("commentCount", 0))) / max(views, 1)) * 100, 2),
            "Description": video["snippet"]["description"],
            "Thumbnail URL": video["snippet"]["thumbnails"].get("high", {}).get("url", "")
        })
    return pd.DataFrame(videos_data)

# Streamlit UI
st.title("📊 YouTube Channel Analyzer")
api_key = st.secrets["youtube_api_key"]
channel_url = st.text_input("Enter YouTube Channel URL")
if st.button("Analyze Channel") and channel_url:
    youtube = get_youtube_client(api_key)
    channel_id, identifier, pattern = extract_channel_id(channel_url)
    if not channel_id and identifier:
        channel_id = resolve_channel_id(youtube, identifier, pattern)
    if channel_id:
        info, playlist_id = get_channel_info(youtube, channel_id)
        st.image(info["Thumbnail URL"], width=200)
        st.subheader(info["Channel Name"])
        st.write(f"Subscribers: {info['Subscribers']:,}")
        st.write(f"Total Views: {info['Total Views']:,}")
        st.write(f"Total Videos: {info['Total Videos']:,}")
        st.write(f"Created: {info['Created Date']}")

        video_ids = []
        next_page_token = None
        while True:
            response = youtube.playlistItems().list(part="contentDetails", playlistId=playlist_id, maxResults=50, pageToken=next_page_token).execute()
            video_ids.extend([item['contentDetails']['videoId'] for item in response['items']])
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        videos = get_video_details(youtube, video_ids)
        videos["Days Since Upload"] = (datetime.now() - pd.to_datetime(videos['Upload Date'])).dt.days
        videos["Days Old"] = (datetime.now() - pd.to_datetime(videos['Upload Date'])).dt.days
        videos["Month"] = pd.to_datetime(videos['Upload Date']).dt.to_period('M').astype(str)

        recent_24h = videos[pd.to_datetime(videos['Upload Date']) >= (datetime.now() - timedelta(hours=24))]
        recent_3d = videos[pd.to_datetime(videos['Upload Date']) >= (datetime.now() - timedelta(days=3))]
        recent_1w = videos[pd.to_datetime(videos['Upload Date']) >= (datetime.now() - timedelta(weeks=1))]
        recent_1m = videos[pd.to_datetime(videos['Upload Date']) >= (datetime.now() - timedelta(days=30))]

        st.subheader("VPH & Engagement based on Recency")
        if not recent_24h.empty:
            st.metric("Avg VPH (Past 24h)", f"{recent_24h['Views Per Hour'].mean():.2f} views/hour")
            st.metric("Engagement Rate (Past 24h)", f"{recent_24h['Engagement Rate (%)'].mean():.2f}%")
        if not recent_3d.empty:
            st.metric("Avg VPH (Past 3 days)", f"{recent_3d['Views Per Hour'].mean():.2f} views/hour")
            st.metric("Engagement Rate (Past 3 days)", f"{recent_3d['Engagement Rate (%)'].mean():.2f}%")
        if not recent_1w.empty:
            st.metric("Avg VPH (Past week)", f"{recent_1w['Views Per Hour'].mean():.2f} views/hour")
            st.metric("Engagement Rate (Past week)", f"{recent_1w['Engagement Rate (%)'].mean():.2f}%")
        if not recent_1m.empty:
            st.metric("Avg VPH (Past month)", f"{recent_1m['Views Per Hour'].mean():.2f} views/hour")
            st.metric("Engagement Rate (Past month)", f"{recent_1m['Engagement Rate (%)'].mean():.2f}%")

        st.subheader("Video Performance Table")

        # Calculate daily lower and upper view ranges
        lifespan_ranges = []
        max_days = videos["Days Since Upload"].max()

        for day in range(1, max_days + 1):
            subset = videos[videos["Days Since Upload"] >= day]
            if not subset.empty:
                lower_range = subset["Views"].quantile(0.25)
                upper_range = subset["Views"].quantile(0.75)
                lifespan_ranges.append({
                    "Day": day,
                    "Lower Range (25th percentile)": round(lower_range, 2),
                    "Upper Range (75th percentile)": round(upper_range, 2)
                })

        lifespan_df = pd.DataFrame(lifespan_ranges)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            videos.to_excel(writer, sheet_name="Video Data", index=False)
            lifespan_df.to_excel(writer, sheet_name="View Ranges", index=False)
        buffer.seek(0)

        b64 = base64.b64encode(buffer.read()).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="channel_analysis.xlsx">📥 Download Excel File</a>'
        st.markdown(href, unsafe_allow_html=True)

        st.subheader("Daily View Ranges Sheet")
        st.dataframe(lifespan_df, use_container_width=True)
        st.dataframe(videos, use_container_width=True)
else:
    st.warning("Please enter the YouTube channel URL")
