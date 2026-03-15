import sqlite3
import pandas as pd

def verify_data(db_path='xz8_media_round2.db'):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM media_resources", conn)
    conn.close()
    
    print(f"Total records: {len(df)}")
    
    # Check for empty fields
    empty_fields = df.isnull().sum()
    print("\nEmpty fields count:")
    print(empty_fields[empty_fields > 0])
    
    # Check sample data
    print("\nSample Data (First 3 rows):")
    print(df[['title', 'play_url', 'source_name', 'year', 'region']].head(3))
    
    # Check URL format
    invalid_urls = df[~df['play_url'].str.contains('/play/')]
    if not invalid_urls.empty:
        print(f"\nWARNING: Found {len(invalid_urls)} invalid play URLs!")
        print(invalid_urls['play_url'].head())
    else:
        print("\nAll play URLs seem valid (contain '/play/').")

    # Check Year distribution
    print("\nYear distribution:")
    print(df['year'].value_counts().head())

    # Check for Status/Quality redundancy issue
    # We want to ensure that if status is NOT a quality keyword, quality should NOT be equal to status
    quality_keywords = ['4K', '1080P', '720P', 'HD', 'BD', 'TC', 'TS', 'CAM', '高清', '蓝光', '正片', '抢先版']
    
    def is_quality_keyword(val):
        if not val: return False
        for kw in quality_keywords:
            if kw in str(val).upper():
                return True
        return False
    
    suspicious_quality = df[
        (df['status'] == df['quality']) & 
        (~df['status'].apply(is_quality_keyword)) &
        (df['quality'] != '')
    ]
    
    if not suspicious_quality.empty:
        print(f"\nWARNING: Found {len(suspicious_quality)} records with suspicious Status==Quality!")
        print(suspicious_quality[['title', 'status', 'quality']].head())
    else:
        print("\nQuality/Status redundancy check passed (no '第xx集' in quality field).")

if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'xz8_media_round4_v2.db'
    verify_data(db_path)
