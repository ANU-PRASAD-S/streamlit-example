import streamlit as st
from googleapiclient.discovery import build
import json
import csv
import re
import urllib.parse
import pandas as pd
import sqlite3
import pymongo
import pyodbc 



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
                video_info['dislikes'] = video_stats['dislikeCount']
                video_info['views'] = video_stats['viewCount']
                video_info['favorite_count'] = video_stats.get('favoriteCount', 0)

                # Additional request to get video content details (duration, caption status)
                video_content_response = youtube.videos().list(
                    part='contentDetails',
                    id=item['id']['videoId']
                ).execute()

                content_details = video_content_response['items'][0]['contentDetails']
                video_info['duration'] = content_details['duration']
                video_info['caption_status'] = content_details.get('caption', 'Not available')

                videos.append(video_info)

                # Store video data in MongoDB
                videos_collection.insert_one(video_info)

            # Check if there are more pages of results
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        # Store channel data in MongoDB
        channel_info = {
            'channel_id': channel_id,
            'channel_name': channel_name,
            'channel_type': 'Your Channel Type Here',  # Replace with the actual channel type
            'channel_views': 'Your Channel Views Here',  # Replace with the actual channel views
            'channel_description': 'Your Channel Description Here',  # Replace with the actual description
            'channel_status': 'Your Channel Status Here'  # Replace with the actual channel status
        }
        channels_collection.insert_one(channel_info)

        st.success(f"Data saved to MongoDB.")
           
        # Save the video data to a CSV file with the generated filename
        with open(filename, 'w', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['video_id', 'title', 'description', 'published_at', 'likes', 'comments', 'views']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()
            for video in videos:
                writer.writerow(video)

        st.success(f"Data saved to '{filename}'.")
#########################################################################################

# Function to execute SQL queries and display results
def execute_query(query):
    conn = sqlite3.connect("youtube_data.db")  # Replace with your database connection details
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return data

# Define a Streamlit element for SQL query section
def sql_query_section():
    # Dropdown to select SQL query
    selected_query = st.selectbox("Select a query", [
        "Names of all videos and their corresponding channels",
        "Channels with the most number of videos",
        "Top 10 most viewed videos and their respective channels",
        "Number of comments on each video and their corresponding video names",
        "Videos with the highest number of likes and their corresponding channel names",
        "Total likes and dislikes for each video and their corresponding video names",
        "Total views for each channel and their corresponding channel names",
        "Channels that published videos in 2022",
        "Average duration of videos in each channel",
        "Videos with the highest number of comments and their corresponding channel names"
    ])

    # Execute SQL queries based on selection
    if selected_query == "Names of all videos and their corresponding channels":
        query_result = execute_query("SELECT Video.title, Channel.channel_name FROM Video JOIN Channel ON Video.channel_id = Channel.channel_id;")
    elif selected_query == "Channels with the most number of videos":
        query_result = execute_query("SELECT channel_name, COUNT(*) AS video_count FROM Channel GROUP BY channel_name ORDER BY video_count DESC LIMIT 1;")
    elif selected_query == "Top 10 most viewed videos and their respective channels":
        query_result = execute_query("SELECT Video.title, Channel.channel_name, Video.views FROM Video JOIN Channel ON Video.channel_id = Channel.channel_id ORDER BY Video.views DESC LIMIT 10;")
    elif selected_query == "Number of comments on each video and their corresponding video names":
        query_result = execute_query("SELECT Video.title, Video.comments FROM Video;")
    elif selected_query == "Videos with the highest number of likes and their corresponding channel names":
        query_result = execute_query("SELECT Video.title, Channel.channel_name, Video.likes FROM Video JOIN Channel ON Video.channel_id = Channel.channel_id ORDER BY Video.likes DESC LIMIT 1;")
    elif selected_query == "Total likes and dislikes for each video and their corresponding video names":
        query_result = execute_query("SELECT Video.title, Video.likes, Video.dislikes FROM Video;")
    elif selected_query == "Total views for each channel and their corresponding channel names":
        query_result = execute_query("SELECT Channel.channel_name, SUM(Video.views) AS total_views FROM Video JOIN Channel ON Video.channel_id = Channel.channel_id GROUP BY Channel.channel_name;")
    elif selected_query == "Channels that published videos in 2022":
        query_result = execute_query("SELECT DISTINCT channel_name FROM Channel WHERE channel_id IN (SELECT DISTINCT channel_id FROM Video WHERE strftime('%Y', Video.published_at) = '2022');")
    elif selected_query == "Average duration of videos in each channel":
        query_result = execute_query("SELECT Channel.channel_name, AVG(Video.duration) AS avg_duration FROM Video JOIN Channel ON Video.channel_id = Channel.channel_id GROUP BY Channel.channel_name;")
    elif selected_query == "Videos with the highest number of comments and their corresponding channel names":
        query_result = execute_query("SELECT Video.title, Channel.channel_name, Video.comments FROM Video JOIN Channel ON Video.channel_id = Channel.channel_id ORDER BY Video.comments DESC LIMIT 1;")

    # Display the results as a table
    if selected_query:
        st.write(pd.DataFrame(query_result, columns=[col[0] for col in cursor.description]))

# Call the SQL query section element
sql_query_section()
Now, the SQL query section is encapsulated within the sql_query_section function, making your code more modular and organized. When you run the Streamlit app, you'll see a separate element for SQL queries while keeping the rest of your application code clean.



# Replace the following MongoDB URI with your own
mongo_uri = "mongodb+srv://anuprasad4444:1234567890@cluster0.nw9dkpu.mongodb.net/"

# Connect to MongoDB using the provided URI
client = pymongo.MongoClient(mongo_uri)

# Access a specific database
db = client.my_database  # Replace 'my_database' with your database name

# Define the JSON document containing your data
data = {
    "channels": [
        {
            "channel_name": "Channel 1",
            "channel_type": "Type 1",
            "channel_views": 10000,
            "channel_description": "Description 1",
            "channel_status": "Active"
        },
        {
            "channel_name": "Channel 2",
            "channel_type": "Type 2",
            "channel_views": 20000,
            "channel_description": "Description 2",
            "channel_status": "Inactive"
        }
    ],
    "videos": [
        {
            "video_id": "Video 1",
            "playlist_id": "Playlist 1",
            "video_name": "Video Name 1",
            "video_description": "Video Description 1",
            "published_date": "2023-09-27",
            "view_count": 5000,
            "like_count": 1000,
            "dislike_count": 100,
            "favorite_count": 500,
            "comment_count": 300,
            "duration": "00:05:30",
            "thumbnail": "thumbnail_url_1",
            "caption_status": "Enabled"
        },
        {
            "video_id": "Video 2",
            "playlist_id": "Playlist 2",
            "video_name": "Video Name 2",
            "video_description": "Video Description 2",
            "published_date": "2023-09-28",
            "view_count": 6000,
            "like_count": 1200,
            "dislike_count": 150,
            "favorite_count": 600,
            "comment_count": 350,
            "duration": "00:04:45",
            "thumbnail": "thumbnail_url_2",
            "caption_status": "Disabled"
        }
    ],
    "playlists": [
        {
            "playlist_id": "Playlist 1",
            "channel_id": "Channel 1",
            "playlist_name": "Playlist Name 1"
        },
        {
            "playlist_id": "Playlist 2",
            "channel_id": "Channel 2",
            "playlist_name": "Playlist Name 2"
        }
    ]
}

# Insert the JSON document into the MongoDB collection
collection = db.my_collection  # Replace 'my_collection' with your collection name
collection.insert_one(data)

# Close the MongoDB connection
client.close()



# SQL Server connection parameters
sql_server = "localhost"
sql_database = "mysql_database"
sql_username = "anuprasad"
sql_password = "1234567890"

# Connect to SQL Server
conn = pyodbc.connect(f"DRIVER={{SQL Server}};SERVER={sql_server};DATABASE={sql_database};UID={sql_username};PWD={sql_password}")
cursor = conn.cursor()

# Define the data to be saved
data = (
    "video_id_value",
    "playlist_id_value",
    "video_name_value",
    "video_description_value",
    "2023-09-27",
    1000,  # view_count
    500,  # like_count
    50,  # dislike_count
    200,  # favorite_count
    300,  # comment_count
    "00:05:30",  # duration
    "thumbnail_url",
    "caption_status_value"
)

# SQL Insert statement
insert_query = "INSERT INTO videos (video_id, playlist_id, video_name, video_description, published_date, view_count, like_count, dislike_count, favorite_count, comment_count, duration, thumbnail, caption_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
cursor.execute(insert_query, data)
conn.commit()

# Close the SQL connection
conn.close()










