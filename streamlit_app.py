import os
import pandas as pd
import streamlit as st
from googleapiclient.discovery import build
import re

# Initialize the YouTube Data API client
API_KEY = "AIzaSyA2t7_3fcDsDA00drph9nRERsI-QPnXgrQ"
youtube = build("youtube", "v3", developerKey=API_KEY)

# Streamlit app title
st.title("YouTube Data Extractor")

# Create a folder to save CSV files
output_folder = "output_data"
os.makedirs(output_folder, exist_ok=True)

# Input for YouTube URL
youtube_url = st.text_input("Enter a YouTube URL:")

if st.button("Get Channel Data"):
    if youtube_url:
        # Extract channel ID from the URL
        match = re.search(r"channel/([A-Za-z0-9_-]+)", youtube_url)
        if match:
            channel_id = match.group(1)

            # Create CSV file name based on channel ID
            csv_filename = os.path.join(output_folder, f"{channel_id}_channel_data.csv")

            # Fetch channel data
            channel_request = youtube.channels().list(
                part="snippet,statistics,status",
                id=channel_id,
            )
            channel_response = channel_request.execute()

            if "items" in channel_response:
                channel_data = channel_response["items"][0]

                # Extract channel data
                channel_name = channel_data["snippet"]["title"]
                channel_type = channel_data["snippet"]["customUrl"]
                channel_views = channel_data["statistics"]["viewCount"]
                channel_description = channel_data["snippet"]["description"]
                channel_status = channel_data["status"]["privacyStatus"]

                # Create a DataFrame for channel data
                channel_df = pd.DataFrame({
                    "channel_name": [channel_name],
                    "channel_type": [channel_type],
                    "channel_views": [channel_views],
                    "channel_description": [channel_description],
                    "channel_status": [channel_status],
                })

                # Save channel data to CSV
                channel_df.to_csv(csv_filename, index=False)

                st.success(f"Channel data saved to {csv_filename}")
        else:
            st.error("No channel ID found in the provided URL.")

# Display the list of available CSV files
csv_files = os.listdir(output_folder)
csv_files = [f for f in csv_files if f.endswith("_channel_data.csv")]

if csv_files:
    st.subheader("Available Channel Data CSVs")
    selected_csv = st.selectbox("Select a CSV:", csv_files)

    # Read and display the selected CSV
    selected_csv_path = os.path.join(output_folder, selected_csv)
    selected_data = pd.read_csv(selected_csv_path)
    st.write(selected_data)
else:
    st.warning("No CSV files available.")

# Information about how to use the app
st.markdown(
    """
    **Instructions:**
    1. Enter a valid YouTube URL in the input box above.
    2. Click the 'Get Channel Data' button to fetch channel data and save it to a CSV file.
    3. The saved CSV files can be selected from the dropdown list to view their contents.
    """
)
