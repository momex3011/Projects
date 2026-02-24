from ingest_wayback import save_event
from datetime import datetime

# Mock data
war_id = 1
text = "مراسل العربية: 6 قتلى وعشرات الجرحى برصاص الأمن في حمص الخالدية"
date_obj = datetime(2011, 4, 20)
url = "http://example.com"
handle = "TestHandle"

print("--- TESTING AI LOGIC ---")
save_event(war_id, text, date_obj, url, handle)
print("--- TEST COMPLETE ---")
