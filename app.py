import streamlit as st
import pandas as pd
import numpy as np
import re
import time
from datetime import datetime
import googleapiclient.discovery
import io

st.set_page_config(page_title="YouTube Channel Analyzer", page_icon="📊", layout="wide")

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

def parse_duration(duration):
    hours = minutes = seconds = 0
    hour_match = re.search(r'(\d+)H', duration)
    minute_match = re.search(r'(\d+)M', duration)
    second_match = re.search(r'(\d+)S', duration)
    if hour_match:
        hours = int(hour_match.group(1))
    if minute_match:
        minutes = int(minute_match.group(1))
    if second_match:
        seconds = int(second_match.group(1))
    return hours * 3600 + minutes * 60 + seconds

def format_duration(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}" if hours else f"{int(minutes):02d}:{int(seconds):02d}"

def extract_channel_info(url):
    patterns = [
        (r'youtube\.com/@([^/\s?]+)', '@'),
        (r'youtube\.com/channel/([^/\s?]+)', ''),
        (r'youtube\.com/c/([^/\s?]+)', ''),
        (r'youtube\.com/user/([^/\s?]+)', '')
    ]
    for pattern, prefix in patterns:
        match = re.search(pattern, url)
        if match:
            return prefix + match.group(1)
    return url

def get_youtube_api():
    api_key = st.secrets["youtube_api_key"]
    return googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

def get_channel_data(youtube, identifier):
    try:
        response = youtube.channels().list(
            part="snippet,statistics,contentDetails",
            id=identifier
        ).execute()
        if response.get('items'):
            return response['items'][0]
    except:
        pass

    try:
        response = youtube.channels().list(
            part="snippet,statistics,contentDetails",
            forUsername=identifier.lstrip('@')
        ).execute()
        if response.get('items'):
            return response['items'][0]
    except:
        pass

    try:
        search_response = youtube.search().list(
            part="snippet",
            q=identifier.lstrip('@'),
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
    except:
        pass

    return None

def get_videos(youtube, playlist_id):
    videos, next_page_token = [], None
    while True:
        response = youtube.playlistItems().list(part="snippet,contentDetails", playlistId=playlist_id, maxResults=50, pageToken=next_page_token).execute()
        for item in response.get('items', []):
            videos.append({
                'video_id': item['contentDetails']['videoId'],
                'title': item['snippet'].get('title', ''),
                'upload_date': item['snippet'].get('publishedAt', '')
            })
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    return videos

def get_video_details(youtube, videos):
    video_details = []
    batches = [videos[i:i+50] for i in range(0, len(videos), 50)]
    for batch in batches:
        video_ids = [v['video_id'] for v in batch]
        response = youtube.videos().list(part="snippet,contentDetails,statistics", id=','.join(video_ids)).execute()
        for item in response.get('items', []):
            basic_info = next((v for v in batch if v['video_id'] == item['id']), {})
            duration = parse_duration(item['contentDetails'].get('duration', 'PT0S'))
            is_short = duration <= 60 or '#shorts' in item['snippet'].get('title', '').lower()
            stats = item.get('statistics', {})
            upload_date = datetime.fromisoformat(basic_info.get('upload_date', '').replace('Z', '+00:00'))
            days_since_upload = (datetime.now().astimezone() - upload_date).days
            video_details.append({
                'video_id': item['id'],
                'title': basic_info.get('title', ''),
                'upload_date': basic_info.get('upload_date', ''),
                'duration_seconds': duration,
                'duration': format_duration(duration),
                'is_short': is_short,
                'video_type': 'Short' if is_short else 'Long-form',
                'views': int(stats.get('viewCount', 0)),
                'likes': int(stats.get('likeCount', 0)),
                'comments': int(stats.get('commentCount', 0)),
                'engagement_rate': round((int(stats.get('likeCount', 0)) + int(stats.get('commentCount', 0))) / int(stats.get('viewCount', 1)) * 100, 2),
                'days_since_upload': days_since_upload
            })
    return video_details

def main():
    st.markdown('<h1 class="header">YouTube Channel Analyzer</h1>', unsafe_allow_html=True)
    url = st.text_input("Enter YouTube Channel URL:", placeholder="https://www.youtube.com/@MrBeast")
    filter_type = st.selectbox("Video Type", ["All", "Long-form (>2 min)", "Shorts (<=60 sec)"])

    if st.button("Analyze Channel"):
        if not url:
            st.warning("Please enter a channel URL")
            return

        with st.spinner("Fetching data..."):
            youtube = get_youtube_api()
            identifier = extract_channel_info(url)
            channel_data = get_channel_data(youtube, identifier)
            if not channel_data:
                st.error("Channel not found")
                return

            uploads_playlist = channel_data['contentDetails']['relatedPlaylists']['uploads']
            videos = get_videos(youtube, uploads_playlist)
            details = get_video_details(youtube, videos)

            df = pd.DataFrame(details)
            df['video_url'] = df['video_id'].apply(lambda x: f"https://www.youtube.com/watch?v={x}")

            if filter_type == "Long-form (>2 min)":
                df = df[df['duration_seconds'] > 120]
            elif filter_type == "Shorts (<=60 sec)":
                df = df[df['duration_seconds'] <= 60]

            st.subheader(f"Videos ({filter_type})")
            st.dataframe(df[['title', 'duration', 'views', 'likes', 'comments', 'engagement_rate', 'video_type', 'video_url']])

            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Video Data', index=False)
            excel_buffer.seek(0)
            st.download_button("Download Excel Report", excel_buffer, file_name="youtube_analysis.xlsx")

if __name__ == "__main__":
    main()
