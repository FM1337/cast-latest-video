import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import pychromecast
import time
import logging
from pychromecast.controllers.youtube import YouTubeController
from dotenv import load_dotenv


Playlist = "" # Optional, skips getting the playlist ID if it's not left blank.
scopes = ["https://www.googleapis.com/auth/youtube.readonly"] # Leave this alone.
latest_video = "" # Leave this empty unless you want to not play a video right away when this script starts up.
new_video = False # Leave this alone.
api_service_name = "youtube" # Leave this alone.
api_version = "v3" # Leave this alone.

youtube = None

# Casts the chromecast
def chromecast_stuff():
    chromecasts = pychromecast.get_chromecasts()
    for cc in chromecasts:
        if cc.device.friendly_name ==  os.getenv("CHROMECAST"):
            cc.wait()
            yt = YouTubeController()
            cc.register_handler(yt)
            yt.play_video(latest_video)
            break

# Gets the uploaded videos playlist from the specified channel.
def get_upload_id():
    global Playlist

    if os.getenv("CHANNEL_ID") == "":
        # check to see if the channel_name is not empty
        if os.getenv("CHANNEL_NAME") == "":
            print("You must provide either a channel name or channel ID!")
            exit(1)
        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            forUsername=os.getenv("CHANNEL_NAME")
        )
    else:
        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            id=os.getenv("CHANNEL_ID")
        )
    response = request.execute()
    Playlist = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']



# Gets the latest video from the channel.
def get_latest_video():
    global latest_video
    global new_video

    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        maxResults=1,
        playlistId=Playlist
    )
    response = request.execute()
    temp_video_id = response['items'][0]['contentDetails']['videoId']
    if latest_video != temp_video_id:
        latest_video = temp_video_id
        new_video = True
        print("New video uploaded!")
    else:
        new_video = False
        print("No new videos :(")

def main():
    global youtube
    try:
        # load the environment variables
        load_dotenv()
        # Get credentials and create an API client
        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey=os.getenv("API_KEY"), cache_discovery=False)
    except Exception as e:
        print("Oh no something went wrong!\nDetails: " + e)
        exit(1)
    # Get the uploaded videos ID for the channel if the playlist is empty
    if Playlist == "":
        print("Getting channel's upload list, please wait!")
        get_upload_id()
        print("Done!")
    while True:
        print("Checking for new videos, please wait!")
        # Get the latest video ID
        get_latest_video()
        # don't do anything if there isn't a new video
        if new_video:
            chromecast_stuff()
        # sleep every hour
        print("Sleeping for an hour before checking again!")
        time.sleep(3600)


if __name__ == "__main__":
    main()