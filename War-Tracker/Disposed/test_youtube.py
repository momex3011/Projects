"""
Quick test to see if YouTube scraping is working at all.
This mimics what tasks.py does.
"""
import yt_dlp
from datetime import datetime

def test_youtube_scraping():
    # Use one of the trusted sources
    handle = "UgaritNews"  # Ugarit News
    target_date = "2011-03-15"  # A date during the Syrian uprising
    
    # Build URL (same as tasks.py)
    if handle.startswith("@"):
        url = f"https://www.youtube.com/{handle}/videos"
    else:
        url = f"https://www.youtube.com/results?search_query={handle}"
    
    print(f"Testing: {url}")
    print(f"Target Date: {target_date}")
    print("-" * 50)
    
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        # "extract_flat": True,  # COMMENTED OUT - needs full metadata
        "skip_download": True,
        "playlistend": 50,
        "ignoreerrors": True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        # Check what we got
        if isinstance(info, dict):
            if "entries" in info and info["entries"]:
                entries = list(info["entries"])
                print(f"✅ Found {len(entries)} entries")
                
                # Check first 5
                for i, e in enumerate(entries[:5]):
                    if not e:
                        continue
                    title = e.get("title", "No title")[:40]
                    upload_date = e.get("upload_date", "No date")
                    print(f"  {i+1}. {title} | upload_date: {upload_date}")
                    
                if not entries:
                    print("❌ Entries list is empty")
            else:
                print("❌ No 'entries' in response")
                print(f"Keys in response: {info.keys()}")
        else:
            print(f"❌ Unexpected response type: {type(info)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_youtube_scraping()
