import subprocess

def download_captions(video_url, output_folder="captions"):
    """Downloads captions for a YouTube video using yt-dlp."""
    try:
        # Ensure the output folder exists
        subprocess.run(["mkdir", "-p", output_folder], check=True)

        # yt-dlp command to download captions
        command = [
            "yt-dlp",
            "--cookies", "all_cookies.txt",  # Path to your cookies file
            "--write-auto-sub",                           # Download subtitles
            "--sub-lang", "en",                      # Specify subtitle language
            "--skip-download",                       # Do not download the video
            "--output", f"{output_folder}/%(title)s.%(ext)s",  # Save format
            video_url
        ]

        # Run the command
        subprocess.run(command, check=True)
        print(f"Captions downloaded successfully for {video_url}")

    except subprocess.CalledProcessError as e:
        print(f"Error downloading captions: {e}")

# Test with a specific video URL
video_url = "https://www.youtube.com/watch?v=APP95uJuBcg"
download_captions(video_url)
