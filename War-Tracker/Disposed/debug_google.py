
import requests
import sys

url = "https://news.google.com/rss/articles/CBMiiwFBVV9nd2ExTEpORjV1aG1yZ05oRHljSUtjRkd3QWdBQ1lDTFZ3S0kyb1hvX1J4d193a0OHowdkx5NEh0bDh4NVVhLVpuUXZ3R2xBMDFwR3dwaG5yVmdWM2dfRFFoRWhKRW53X2dEaW1qQ0tRZ3JzNlE?oc=5&hl=en-US&gl=US&ceid=US:en"

try:
    print(f"Fetching: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    r = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
    print(f"Status: {r.status_code}")
    print("--- HEADERS ---")
    print(r.headers)
    print("--- CONTENT START ---")
    print(r.text[:1000])
    print("--- CONTENT END ---")
except Exception as e:
    print(f"Error: {e}")
