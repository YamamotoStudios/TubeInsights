import subprocess
from googleapiclient.discovery import build
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# Replace with your YouTube API Key
API_KEY = "AIzaSyC_DfsdQv168YXDN0jffDcOtBroWbA1Loc"
CHANNEL_ID = "UCPpm7NuxCslvKWsF0tTAv-Q"  # Senpai Torpid's channel ID

# Initialize YouTube API client
youtube = build('youtube', 'v3', developerKey=API_KEY)

def get_videos(channel_id, start_date, end_date):
    """Fetch video metadata from a YouTube channel within the date range."""
    videos = []
    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        maxResults=50,
        order="date",
        type="video"
    )

    while request:
        response = request.execute()
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            published_at = item["snippet"]["publishedAt"]
            published_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")

            # Filter videos by date range
            if start_date <= published_date <= end_date:
                videos.append({
                    "video_id": video_id,
                    "title": item["snippet"]["title"].replace("/", "_"),  # Avoid invalid filenames
                    "published_at": published_date.isoformat()
                })

        request = youtube.search().list_next(request, response)

    return videos

def extract_text_from_vtt(vtt_file):
    """Extract plain text from a .vtt subtitle file."""
    transcript_lines = []
    with open(vtt_file, "r", encoding="utf-8") as file:
        for line in file:
            # Skip metadata lines
            if line.strip() and not line.strip().isdigit() and "-->" not in line:
                transcript_lines.append(line.strip())
    return " ".join(transcript_lines)

def download_captions(video, output_folder="captions"):
    """Download auto-generated captions for a video using yt-dlp and extract transcript text."""
    transcript_path = os.path.join(output_folder, f"{video['title']}.en.vtt")
    try:
        # Ensure the output folder exists
        os.makedirs(output_folder, exist_ok=True)

        # Check if the transcript file already exists
        if os.path.exists(transcript_path):
            print(f"Transcript already exists for {video['title']}. Skipping download.")
        else:
            # yt-dlp command to download auto-generated captions
            command = [
                "yt-dlp",
                "--cookies", "all_cookies.txt",  # Path to your cookies file
                "--write-auto-sub",                   # Fetch auto-generated subtitles
                "--sub-lang", "en",                   # Specify subtitle language
                "--skip-download",                    # Do not download the video
                "--output", f"{output_folder}/{video['title']}",  # Save format without doubling
                f"https://www.youtube.com/watch?v={video['video_id']}"  # Video URL
            ]
            # Run the yt-dlp command
            subprocess.run(command, check=True)

        # Extract transcript text from the .vtt file
        transcript_text = extract_text_from_vtt(transcript_path)

        # Return video metadata with transcript text
        return {
            "video_id": video["video_id"],
            "title": video["title"],
            "published_at": video["published_at"],
            "transcript": transcript_text
        }

    except subprocess.CalledProcessError as e:
        # Log error if captions cannot be downloaded
        return {
            "video_id": video["video_id"],
            "title": video["title"],
            "published_at": video["published_at"],
            "error": f"Error: {e}"
        }

def fetch_transcripts_concurrently(videos, max_workers=100):
    """Download captions concurrently for multiple videos."""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks
        future_to_video = {executor.submit(download_captions, video): video for video in videos}
        for future in as_completed(future_to_video):
            try:
                results.append(future.result())
            except Exception as e:
                video = future_to_video[future]
                results.append({
                    "video_id": video["video_id"],
                    "title": video["title"],
                    "published_at": video["published_at"],
                    "error": str(e)
                })
    return results

def save_to_json(data, filename):
    """Save data to a single JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def main():
    # Get start and end dates from user
    start_date_str = input("Enter the start date (YYYY-MM-DD): ")
    end_date_str = input("Enter the end date (YYYY-MM-DD): ")

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        return

    # Fetch video metadata
    print("Fetching videos...")
    videos = get_videos(CHANNEL_ID, start_date, end_date)
    print(f"Found {len(videos)} videos.")

    # Download captions concurrently
    print("Downloading captions...")
    transcripts = fetch_transcripts_concurrently(videos)

    # Save all results to a single JSON file
    print("Saving results to JSON...")
    save_to_json(transcripts, "youtube_transcripts.json")
    print("Done! Results saved to 'youtube_transcripts.json'.")

if __name__ == "__main__":
    main()
