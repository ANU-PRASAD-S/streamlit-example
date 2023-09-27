import streamlit as st
from googleapiclient.discovery import build
import json
import csv
import re
import urllib.parse

# Set up the API client
api_key = "AIzaSyA2t7_3fcDsDA00drph9nRERsI-QPnXgrQ"  # Replace with your API key
youtube = build('youtube', 'v3', developerKey=api_key)

# Function to get the channel ID from channel name
def get_channel_id_from_name(channel_name):
    # Perform the necessary API call here to get the channel ID
    # Replace this with your own implementation
    pass

# Streamlit app
st.title("YouTube Channel Data Extraction")

# User input section
channel_url = st.text_input("Enter the YouTube channel URL:")
if channel_url:
    # Extract the channel name from the URL
    parsed_url = urllib.parse.urlparse(channel_url)
    channel_name = parsed_url.path.split('@')[-1]  # Extract letters after '@'

    # Use the function to get the channel ID
    channel_id = get_channel_id_from_name(channel_name)

    if not channel_id:
        st.error("Channel not found.")
    else:
        # Generate a URL-safe slug from the channel name
        slug = re.sub(r'[^a-z0-9]+', '-', channel_name.lower()).strip('-')

        # Define the filename using the slug
        filename = f'{slug}_analytics.csv'

        next_page_token = None
        videos = []

        while True:
            response = youtube.search().list(
                part='snippet',
                channelId=channel_id,
                type='video',
                maxResults=50,  # Adjust the number of results per page as needed
                pageToken=next_page_token
            ).execute()

            # Loop through the items in the API response and extract relevant information
            for item in response['items']:
                video_info = {
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'published_at': item['snippet']['publishedAt']
                }

                # Additional request to get video statistics (likes, comments, view counts)
                video_stats_response = youtube.videos().list(
                    part='statistics',
                    id=item['id']['videoId']
                ).execute()

                video_stats = video_stats_response['items'][0]['statistics']
                video_info['likes'] = video_stats['likeCount']

                # Check if 'commentCount' exists (may not exist if comments are restricted)
                if 'commentCount' in video_stats:
                    video_info['comments'] = video_stats['commentCount']
                else:
                    video_info['comments'] = 'Comments restricted'

                video_info['views'] = video_stats['viewCount']

                videos.append(video_info)

            # Check if there are more pages of results
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        # Save the video data to a CSV file with the generated filename
        with open(filename, 'w', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['video_id', 'title', 'description', 'published_at', 'likes', 'comments', 'views']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()
            for video in videos:
                writer.writerow(video)

        st.success(f"Data saved to '{filename}'.")
