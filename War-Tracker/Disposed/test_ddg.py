from duckduckgo_search import DDGS
import time

print("🦆 Testing DuckDuckGo for 2011 Data...")

# Test: Daraa protests (Start of revolution) - March 18, 2011
query = 'site:twitter.com "Syria" "Daraa" after:2011-03-17 before:2011-03-20'

try:
    results = DDGS().text(query, max_results=10)
    print(f"Found {len(results)} results")
    for r in results:
        print(f"- {r['title']}: {r['href']}")
except Exception as e:
    print(f"❌ Error: {e}")
