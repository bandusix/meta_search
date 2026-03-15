import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_data_structure():
    """Verify that the database schema and data integrity match requirements."""
    db_path = 'vs_1919_flat.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    logger.info(f"Verifying database: {db_path}")
    
    # 1. Check Table Schema
    logger.info("Checking table schema 'media_resources'...")
    cursor.execute("PRAGMA table_info(media_resources)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    expected_columns = {
        'id': 'INTEGER',
        'category': 'TEXT',
        'title': 'TEXT',
        'episode_name': 'TEXT',
        'play_url': 'TEXT',
        'detail_url': 'TEXT',
        'poster_url': 'TEXT',
        'year': 'INTEGER',
        'quality': 'TEXT',
        'genre': 'TEXT',
        'region': 'TEXT',
        'director': 'TEXT',
        'actors': 'TEXT',
        'status': 'TEXT',
        'created_at': 'TIMESTAMP',
        'updated_at': 'TIMESTAMP'
    }
    
    missing_cols = set(expected_columns.keys()) - set(columns.keys())
    if missing_cols:
        logger.error(f"FAIL: Missing columns: {missing_cols}")
        return False
    else:
        logger.info("PASS: Schema matches expected structure.")

    # 2. Check Data Consistency
    logger.info("Checking data consistency...")
    
    # Check total count
    cursor.execute("SELECT COUNT(*) FROM media_resources")
    total_count = cursor.fetchone()[0]
    logger.info(f"Total records: {total_count}")
    if total_count == 0:
        logger.warning("WARNING: Database is empty!")
    
    # Check for NULL crucial fields
    cursor.execute("SELECT COUNT(*) FROM media_resources WHERE title IS NULL OR play_url IS NULL OR category IS NULL")
    invalid_count = cursor.fetchone()[0]
    if invalid_count > 0:
        logger.error(f"FAIL: Found {invalid_count} records with NULL title/play_url/category.")
        return False
    else:
        logger.info("PASS: All records have mandatory fields.")

    # Check play_url format
    cursor.execute("SELECT COUNT(*) FROM media_resources WHERE play_url NOT LIKE '%/vsbspy/%'")
    bad_url_count = cursor.fetchone()[0]
    if bad_url_count > 0:
        logger.error(f"FAIL: Found {bad_url_count} records with invalid play_url format (must contain '/vsbspy/').")
        return False
    else:
        logger.info("PASS: All play_urls have correct format.")

    # Check category distribution
    logger.info("Category distribution:")
    cursor.execute("SELECT category, COUNT(*) FROM media_resources GROUP BY category")
    rows = cursor.fetchall()
    for cat, count in rows:
        logger.info(f"  - {cat}: {count}")
        
    if not rows:
        logger.warning("WARNING: No categories found.")

    conn.close()
    logger.info("Verification completed successfully.")
    return True

if __name__ == "__main__":
    verify_data_structure()
