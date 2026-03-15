import sqlite3

def check_db_stats():
    conn = sqlite3.connect('vs_1919_flat.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM media_resources")
    total = cursor.fetchone()[0]
    print(f"Total records in DB: {total}")
    
    cursor.execute("SELECT category, COUNT(*) FROM media_resources GROUP BY category")
    print("\nBreakdown by category:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
        
    conn.close()

if __name__ == "__main__":
    check_db_stats()
