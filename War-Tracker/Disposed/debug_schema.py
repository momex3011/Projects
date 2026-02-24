import sqlite3

DB_PATH = "wartracker.db"

def inspect():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(events)")
    cols = cursor.fetchall()
    print("Events Table Columns:")
    for c in cols:
        print(c)
    conn.close()

if __name__ == "__main__":
    inspect()
