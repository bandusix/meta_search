import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import DatabaseManager

def check_counts():
    db_path = "data/database.db"
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    db_manager = DatabaseManager(db_path)
    
    movies_count = db_manager.get_movies_count()
    episodes_count = db_manager.get_episodes_count()
    
    print("-" * 30)
    print("Current Database Stats:")
    print(f"Movies: {movies_count}")
    print(f"TV Episodes: {episodes_count}")
    print(f"Total: {movies_count + episodes_count}")
    print("-" * 30)

if __name__ == "__main__":
    check_counts()
