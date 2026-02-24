
import sqlite3

# Results from browser subagent
results = [
  { "id": 1, "final_url": "https://www.aljazeera.com/news/2011/12/2/ranks-of-free-syrian-army-gaining-strength", "video_found": None },
  { "id": 2, "final_url": "https://www.aljazeera.com/features/2011/11/16/free-syrian-army-grows-in-influence", "video_found": "https://www.youtube.com/embed/QSInr8W4iqo?enablejsapi=1" },
  { "id": 3, "final_url": None, "video_found": None },
  { "id": 4, "final_url": "https://www.youtube.com/watch?v=FJhDls0FHTM", "video_found": "https://www.youtube.com/watch?v=FJhDls0FHTM" },
  { "id": 5, "final_url": "https://www.youtube.com/watch?v=eLQYUTLBcCk", "video_found": "https://www.youtube.com/watch?v=eLQYUTLBcCk" },
  { "id": 6, "final_url": "https://www.youtube.com/watch?v=KEsIc6Q7bTE", "video_found": "https://www.youtube.com/watch?v=KEsIc6Q7bTE" },
  { "id": 8, "final_url": "https://www.aljazeera.com/news/2011/12/2/ranks-of-free-syrian-army-gaining-strength", "video_found": None },
  { "id": 9, "final_url": "https://www.aljazeera.com/features/2011/11/16/free-syrian-army-grows-in-influence", "video_found": "https://www.youtube.com/embed/QSInr8W4iqo?enablejsapi=1" },
  { "id": 10, "final_url": None, "video_found": None },
  { "id": 11, "final_url": "https://www.youtube.com/watch?v=FJhDls0FHTM", "video_found": "https://www.youtube.com/watch?v=FJhDls0FHTM" },
  { "id": 12, "final_url": "https://www.youtube.com/watch?v=eLQYUTLBcCk", "video_found": "https://www.youtube.com/watch?v=eLQYUTLBcCk" },
  { "id": 13, "final_url": "https://www.youtube.com/watch?v=KEsIc6Q7bTE", "video_found": "https://www.youtube.com/watch?v=KEsIc6Q7bTE" }
]

conn = sqlite3.connect('wartracker.db')
cursor = conn.cursor()

count = 0
for item in results:
    if item['final_url']:
        # Update source_url to the final URL
        cursor.execute("UPDATE events SET source_url = ? WHERE id = ?", (item['final_url'], item['id']))
        
        # If video found, update video_url. 
        # If NO video found, but the current video_url is a google link (garbage), NULL it.
        # Check current video_url first
        cursor.execute("SELECT video_url FROM events WHERE id = ?", (item['id'],))
        current_vid = cursor.fetchone()[0]
        
        if item['video_found']:
            cursor.execute("UPDATE events SET video_url = ? WHERE id = ?", (item['video_found'], item['id']))
            print(f"ID {item['id']}: Set VIDEO to {item['video_found']}")
        elif current_vid and 'news.google.com' in current_vid:
            cursor.execute("UPDATE events SET video_url = NULL WHERE id = ?", (item['id'],))
            print(f"ID {item['id']}: Cleared garbage VIDEO URL")
        else:
            print(f"ID {item['id']}: Updated Source URL only")
            
        count += 1

conn.commit()
conn.close()
print(f"Updated {count} events.")
