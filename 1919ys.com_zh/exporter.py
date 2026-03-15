import os
import pandas as pd
import time
from database import get_connection

def export_csv():
    conn = get_connection()
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    base_dir = "output"
    
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
            
    filepath = os.path.join(base_dir, f'media_resources_full_{timestamp}.csv')
    
    try:
        print("Starting CSV export (this may take a while for millions of rows)...")
        # Export the single flat table to CSV because it's too large for Excel
        query = '''
        SELECT 
            category, title, episode_name, play_url, detail_url, poster_url,
            year, quality, genre, region, director, actors, status, updated_at
        FROM media_resources
        ORDER BY category, title, id
        '''
        
        # Use chunking to avoid memory issues
        chunksize = 100000
        first_chunk = True
        total_rows = 0
        
        for chunk in pd.read_sql_query(query, conn, chunksize=chunksize):
            if first_chunk:
                chunk.to_csv(filepath, index=False, encoding='utf-8-sig', mode='w')
                first_chunk = False
            else:
                chunk.to_csv(filepath, index=False, encoding='utf-8-sig', mode='a', header=False)
            total_rows += len(chunk)
            print(f"Exported {total_rows} rows...")
            
        print(f"Successfully exported all {total_rows} rows to {filepath}")
        
    except Exception as e:
        print(f"Error exporting {filepath}: {e}")
            
    conn.close()

if __name__ == "__main__":
    export_csv()
