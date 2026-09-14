import sys
import os
import re
import urllib.request
import base64
import json
from dotenv import load_dotenv  # <-- Add import

load_dotenv()  # <-- Execute here

def get_m3u_playlist(url):
    # Standardize details URL to download directory URL
    if "/details/" in url:
        url = url.replace("/details/", "/download/")
    url = url.rstrip("/") + "/"
    
    print(f"Fetching archive content from: {url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching URL: {e}")
        sys.exit(1)
        
    # Extracted fix for string quotes in regex pattern
    video_pattern = re.compile(r"""href=["']([^"']+\.(mp4|mkv|avi|ogv|mov|mp3|wav|flac|ogg))["']""", re.IGNORECASE)
    matches = video_pattern.findall(html)
    
    if not matches:
        print("No matching media files found.")
        sys.exit(1)
        
    m3u_lines = ["#EXTM3U"]
    for filename, ext in matches:
        m3u_lines.append(f"#EXTINF:-1,{filename}")
        m3u_lines.append(f"{url}{filename}")
        
    return "\n".join(m3u_lines), url.split("/")[-2]

def upload_to_github(content, filename, repo="anishd/archiveorgplaylists", branch="main"):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set.")
        print("Please verify your .env file exists in the project root directory.")
        sys.exit(1)
        
    url = f"https://github.com{repo}/contents/{filename}"
    
    # 1. Base Headers used for both checking and uploading
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ParchiveApp/1.0"
    }
    
    # Check if file exists to get its SHA (required for file updates)
    sha = None
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            sha = data.get("sha")
    except Exception:
        pass # File doesn't exist yet, which is fine

    # 2. Construct Payload
    payload = {
        "message": f"Automated update for playlist: {filename}",
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    # Encode payload to bytes
    json_data = json.dumps(payload).encode("utf-8")
    
    # 3. Add explicit Content-Length and Content-Type to prevent Windows 10054 drops
    upload_headers = headers.copy()
    upload_headers["Content-Type"] = "application/json"
    upload_headers["Content-Length"] = str(len(json_data))
    upload_headers["Connection"] = "close" # Disables keep-alive to avoid socket reuse drops

    try:
        req = urllib.request.Request(
            url, 
            data=json_data, 
            headers=upload_headers, 
            method="PUT"
        )
        with urllib.request.urlopen(req) as response:
            if response.status in [200, 201]:
                print(f"Successfully uploaded {filename} to GitHub repository {repo}!")
    except Exception as e:
        print(f"Failed to upload to GitHub: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: parchive <archive_url>")
        sys.exit(1)
        
    target_url = sys.argv[1]
    m3u_content, identifier = get_m3u_playlist(target_url)
    
    # Keeping files in root or specific folders for GitHub Pages parsing later
    filename = f"{identifier}.m3u"
    
    print(f"Generating playlist: {filename}...")
    upload_to_github(m3u_content, filename)

if __name__ == "__main__":
    main()
