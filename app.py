# Calculate daily cumulative lower and upper view ranges (for long-form videos)
if st.button("Analyze Channel") and channel_url:
    # Your video fetching + metrics logic before this block

    videos_long = videos[videos['Duration (sec)'] > 12]
    lifespan_ranges = []
    max_days = videos_long["Days Since Upload"].max()

    for day in range(1, max_days + 1):
        cumulative_views = []
        for _, row in videos_long.iterrows():
            days_since_upload = row['Days Since Upload']
            if days_since_upload >= day:
                cumulative_views.append(row['Views'] * (day / days_since_upload))
        if cumulative_views:
            lower = np.percentile(cumulative_views, 25)
            upper = np.percentile(cumulative_views, 75)
            lifespan_ranges.append({
                "Day": day,
                "Lower Range (25th percentile)": round(lower, 2),
                "Upper Range (75th percentile)": round(upper, 2)
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
