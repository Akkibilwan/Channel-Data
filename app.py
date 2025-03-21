def main():
    st.markdown('<h1 class="header">YouTube Channel Analyzer</h1>', unsafe_allow_html=True)
    
    # Input for channel URL
    channel_url = st.text_input("Enter YouTube Channel URL:", 
                              placeholder="https://www.youtube.com/@ChannelName")
    
    # Days to analyze
    max_days = st.slider("Days to analyze:", min_value=7, max_value=90, value=30)
    
    # Video type filter
    filter_type = st.selectbox("Select video type:", options=["All", "Long Form (>2 mins)", "Shorts (<=60 sec)"])
    
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
                return
            
            # Display channel info
            col1, col2 = st.columns([1, 3])
            with col1:
                if 'thumbnails' in channel_data.get('snippet', {}):
                    st.image(
                        channel_data['snippet']['thumbnails'].get('high', {}).get('url', ''),
                        width=150
                    )
            with col2:
                st.markdown(f"### {channel_data['snippet'].get('title', 'Unknown Channel')}")
                st.write(f"**Subscribers:** {int(channel_data.get('statistics', {}).get('subscriberCount', 0)):,}")
                st.write(f"**Total Videos:** {int(channel_data.get('statistics', {}).get('videoCount', 0)):,}")
                st.write(f"**Total Views:** {int(channel_data.get('statistics', {}).get('viewCount', 0)):,}")
            
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
            video_df['video_url'] = video_df['video_id'].apply(lambda x: f"https://www.youtube.com/watch?v={x}")
            video_df = video_df.sort_values('upload_date', ascending=False).reset_index(drop=True)
            
            # Apply filter
            if filter_type == "Long Form (>2 mins)":
                video_df = video_df[video_df['duration_seconds'] > 120]
            elif filter_type == "Shorts (<=60 sec)":
                video_df = video_df[video_df['duration_seconds'] <= 60]
            # If "All", no filter is applied
            
            if video_df.empty:
                st.warning("No videos matching the selected filter.")
                return

            # Display videos
            st.subheader(f"Filtered Videos ({filter_type})")
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
            
            # Calculate view metrics
            st.subheader("View Performance Metrics")
            view_metrics = calculate_view_metrics(video_df, max_days)
            st.dataframe(view_metrics)
            
            # Excel download
            st.subheader("Download Data")
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                video_df.to_excel(writer, sheet_name='Video Data', index=False)
                view_metrics.to_excel(writer, sheet_name='View Metrics', index=False)
            excel_buffer.seek(0)
            st.download_button(
                label="Download Excel Report",
                data=excel_buffer,
                file_name=f"{channel_data['snippet'].get('title', 'channel')}_{filter_type.replace(' ', '_').lower()}_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
