import streamlit as st
import pandas as pd
from apiclient.discovery import build
from googleapiclient.errors import HttpError

# Set Streamlit title and description
st.title("YouTube Analytics Downloader")
st.write("Select a YouTube channel and download analytics data to CSV.")

# Input field for YouTube API key
api_key = st.text_input("Enter your YouTube Data API Key")

# Function to fetch channel names
def fetch_channel_names(api_key):
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        channels_request = youtube.channels().list(mine=True, part="snippet")
        channels_response = channels_request.execute()

        channel_names = [channel["snippet"]["title"] for channel in channels_response.get("items", [])]
        return channel_names
    except HttpError as e:
        st.error(f"An error occurred: {str(e)}")
        return []

# Dropdown for selecting a YouTube channel
channel_names = fetch_channel_names(api_key)
selected_channel = st.selectbox("Select a YouTube Channel", channel_names)

# Function to download YouTube analytics to CSV
def download_analytics_to_csv(api_key, channel_id):
    try:
        youtube_analytics = build("youtubeAnalytics", "v2", developerKey=api_key)
        analytics_request = youtube_analytics.reports().query(
            ids=f"channel=={channel_id}",
            startDate="2023-01-01",
            endDate="2023-01-31",
            metrics="views,comments,likes,dislikes,shares",
            dimensions="video"
        )

        response = analytics_request.execute()
        data = response.get("rows", [])

        if data:
            df = pd.DataFrame(data, columns=["Video", "Views", "Comments", "Likes", "Dislikes", "Shares"])
            st.dataframe(df)
            st.write(f"Total Results: {len(df)}")
            st.write("Download the data to a CSV file.")
            if st.button("Download CSV"):
                df.to_csv(f"{selected_channel}_analytics.csv", index=False)
                st.success("CSV download complete.")
        else:
            st.warning("No analytics data available for this channel.")
    except HttpError as e:
        st.error(f"An error occurred: {str(e)}")

# Download analytics data button
if st.button("Fetch Analytics Data"):
    if api_key and selected_channel:
        channel_id = fetch_channel_names(api_key)[channel_names.index(selected_channel)]
        download_analytics_to_csv(api_key, channel_id)
    else:
        st.warning("Please enter a valid API key and select a YouTube channel.")
