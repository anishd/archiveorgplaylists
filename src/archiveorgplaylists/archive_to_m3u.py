import sys
import os
import re
import urllib.request
from dotenv import load_dotenv

load_dotenv()

def get_m3u_playlist(url):
    if "/details/" in url:
        url = url.replace("/details/", "/download/")
    url = url.rstrip("/") + "/"
    
    print(f"Fetching archive content from: {url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching Archive URL: {e}")
        sys.exit(1)
        
    video_pattern = re.compile(r"""href=["']([^"']+\.(mp4|mkv|avi|ogv|mov|mp3|wav|flac|ogg))["']""", re.IGNORECASE)
    matches = video_pattern.findall(html)
    
    if not matches:
        print("No matching media files found.")
        sys.exit(1)
        
    m3u_lines = ["#EXTM3U"]
    for match in matches:
        filename = match if isinstance(match, str) else match
        m3u_lines.append(f"#EXTINF:-1,{filename}")
        m3u_lines.append(f"{url}{filename}")
        
    return "\n".join(m3u_lines), url.split("/")[-2]

def update_static_dashboard(output_dir):
    """Scans the output directory and updates an iOS 9 compatible index.html."""
    html_path = os.path.join(output_dir, "index.html")
    
    # Locate all generated .m3u files in the folder
    files = [f for f in os.listdir(output_dir) if f.endswith(".m3u")]
    
    # Old-school clean HTML structure safe for iOS 9 Safari (No complex layouts)
    html_start = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Archive Playlists</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #121212; color: #ffffff; padding: 20px; }
        h1 { color: #00ffcc; border-bottom: 2px solid #333; padding-bottom: 10px; font-size: 24px; }
        ul { list-style-type: none; padding: 0; margin: 20px 0; }
        li { margin: 12px 0; background: #1e1e1e; padding: 15px; border-radius: 4px; border: 1px solid #2d2d2d; }
        a { color: #33b5e5; text-decoration: none; font-size: 18px; font-weight: bold; display: block; }
        a:hover { text-decoration: underline; }
        .info { color: #888; font-size: 12px; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>📺 Archive Playlists Dashboard</h1>
    <ul>
"""

    html_end = """    </ul>
</body>
</html>"""

    list_items = []
    for f in sorted(files):
        # Format a clean user-friendly display name
        display_name = f.replace(".m3u", "").replace("_", " ").title()
        list_items.append(f'        <li><a href="{f}">▶ {display_name}</a><div class="info">Format: VLC Playlist File (.m3u)</div></li>')

    full_html = html_start + "\n".join(list_items) + "\n" + html_end

    with open(html_path, "w", encoding="utf-8") as html_file:
        html_file.write(full_html)
    print(f"🖥️  Updated dashboard interface at: {html_path}")

def save_local_playlist(content, filename):
    output_dir = "docs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    file_path = os.path.join(output_dir, filename)
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✨ Success! Playlist saved locally to: {file_path}")
        
        # Build/recompile the HTML dashboard
        update_static_dashboard(output_dir)
        
    except Exception as e:
        print(f"Failed to write file locally: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: parchive <archive_url>")
        sys.exit(1)
        
    # FIX: Add [1] here to grab the actual URL argument string, not the list
    target_url = sys.argv[1] 
    
    m3u_content, identifier = get_m3u_playlist(target_url)
    
    filename = f"{identifier}.m3u"
    save_local_playlist(m3u_content, filename)

if __name__ == "__main__":
    main()
