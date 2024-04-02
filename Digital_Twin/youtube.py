import requests
from youtube_transcript_api import YouTubeTranscriptApi
import os

def retrieve_playlist():
    api_key = os.getenv("YOUTUBE_API_KEY")
    playlist_id = os.getenv("PLAYLIST_ID")
    video_ids = []

    # Fetch Playlist Details
    response = requests.get(f'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={playlist_id}&maxResults=25&key={api_key}')
    playlist_items = response.json().get('items', [])

    print(playlist_items)
    # Extract video IDs
    for item in playlist_items:
        video_ids.append(item['snippet']['resourceId']['videoId'])

    # Extract Video Transcripts
    transcripts = []
    for video_id in video_ids:
        try:
            # Fetch and store the transcript for each video ID
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            # Each transcript is a list of dictionaries, I've converted it to a single string for ease of processing data
            transcript_text = '\n'.join([segment['text'] for segment in transcript])
            transcripts.append({'video_id': video_id, 'transcript': transcript_text})
        except Exception as e:
            print(f"Could not retrieve transcript for video {video_id}: {str(e)}")
            # Append an empty transcript for videos where no transcript could be retrieved
            transcripts.append({'video_id': video_id, 'transcript': ''})

    # with open('all_transcripts.txt', 'w', encoding='utf-8') as file:
    #     for video in transcripts:
    #         file.write(f"Video ID: {video['video_id']}\n")
    #         file.write("Transcript:\n")
    #         file.write(video['transcript'])
    #         file.write("\n\n")  # Add extra newlines for readability between transcripts
            
    for video in transcripts:
        filename = f"more-knowledge/{video['video_id']}_transcript.txt"  # Create a unique filename for each video
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(video['transcript'])

retrieve_playlist()