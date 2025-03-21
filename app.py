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

@st.cache_resource
def get_youtube_client(api_key):
    return build('youtube', 'v3', developerKey=api_key)

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
    if hours > 0:
        return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
    else:
        return f"{int(minutes)}:{int(seconds):02d}"

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
            if "channel" in pattern:
                return match.group(1), None, pattern
            else:
                return None, match.group(1), pattern
    st.error("Invalid YouTube channel URL format.")
    return None, None, None

def resolve_channel_id(youtube, identifier, pattern_type):
    try:
        if "user" in pattern_type:
            response = youtube.channels().list(part="id", forUsername=identifier).execute()
        else:
            response = youtube.search().list(part="snippet", q=identifier, type="channel", maxResults=1).execute()
            if response.get("items"):
                return response["items"][0]["id"]["channelId"]
            response = youtube.channels().list(part="id", forUsername=identifier).execute()
        if response.get("items"):
            return response["items"][0]["id"]
        else:
            st.error(f"Could not resolve channel identifier: {identifier}")
            return None
    except Exception as e:
        st.error(f"Error resolving channel ID: {str(e)}")
        return None

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
            "Title": video["snippet"]["title"],
            "Upload Date": upload_date.strftime("%Y-%m-%d"),
            "Duration": format_duration(duration_sec),
            "Views": views,
            "Views Per Hour": round(views / hours_since_upload, 2),
            "VPH (24h)": vph_24h,
            "VPH (3d)": vph_3d,
            "VPH (1w)": vph_1w,
            "VPH (1m)": vph_1m,
            "Likes": int(video["statistics"].get("likeCount", 0)),
            "Comments": int(video["statistics"].get("commentCount", 0)),
            "Engagement Rate (%)": round(((int(video["statistics"].get("likeCount", 0)) + int(video["statistics"].get("commentCount", 0))) / max(views, 1)) * 100, 2)
        })
    return pd.DataFrame(videos_data)

st.title("📊 YouTube Channel Analyzer")
api_key = st.text_input("Enter YouTube Data API Key", type="password")
channel_url = st.text_input("Enter YouTube Channel URL")
if st.button("Analyze Channel"):
    if api_key and channel_url:
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
            videos = get_video_details(youtube, [video['contentDetails']['videoId'] for video in youtube.playlistItems().list(part="contentDetails", playlistId=playlist_id, maxResults=50).execute()['items']])
            avg_metrics = videos[["Views Per Hour", "VPH (24h)", "VPH (3d)", "VPH (1w)", "VPH (1m)", "Engagement Rate (%)", "Likes", "Comments"].copy()].mean().round(2)
            st.metric("Average VPH", f"{avg_metrics['Views Per Hour']} views/hour")
            st.metric("Avg VPH (24h)", f"{avg_metrics['VPH (24h)']} views/hour")
            st.metric("Avg VPH (3d)", f"{avg_metrics['VPH (3d)']} views/hour")
            st.metric("Avg VPH (1w)", f"{avg_metrics['VPH (1w)']} views/hour")
            st.metric("Avg VPH (1m)", f"{avg_metrics['VPH (1m)']} views/hour")
            st.metric("Avg Engagement Rate", f"{avg_metrics['Engagement Rate (%)']}%")
            st.metric("Avg Likes", f"{avg_metrics['Likes']:,}")
            st.metric("Avg Comments", f"{avg_metrics['Comments']:,}")
            st.dataframe(videos, use_container_width=True)
    else:
        st.warning("Please enter API key and channel URL")
