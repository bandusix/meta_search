import sqlite3
import pandas as pd
import os
from datetime import datetime

class Exporter:
    def __init__(self, db_name="topflix.db"):
        self.db_name = db_name

    def export_data(self):
        conn = sqlite3.connect(self.db_name)
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = f"exports/{datetime.now().strftime('%Y-%m-%d')}"
        os.makedirs(export_dir, exist_ok=True)
        
        try:
            # Export Movies
            print("Exporting Movies...")
            df_movies = pd.read_sql_query("SELECT * FROM movies", conn)
            if not df_movies.empty:
                movies_csv = f"{export_dir}/movies_{date_str}.csv"
                df_movies.to_csv(movies_csv, index=False)
                
                # Excel export
                movies_xlsx = f"{export_dir}/movies_{date_str}.xlsx"
                df_movies.to_excel(movies_xlsx, index=False)
                print(f"Movies exported to {movies_xlsx}")
            else:
                print("No movies found to export.")

            # Export TV Shows with Episodes (Joined)
            print("Exporting TV Series...")
            # First export shows
            df_shows = pd.read_sql_query("SELECT * FROM tv_shows", conn)
            if not df_shows.empty:
                shows_csv = f"{export_dir}/tv_shows_{date_str}.csv"
                df_shows.to_csv(shows_csv, index=False)
                
                shows_xlsx = f"{export_dir}/tv_shows_{date_str}.xlsx"
                df_shows.to_excel(shows_xlsx, index=False)
                print(f"TV Shows exported to {shows_xlsx}")

            # Export Episodes
            df_episodes = pd.read_sql_query("""
                SELECT 
                    e.*, 
                    s.title as show_title 
                FROM tv_episodes e
                JOIN tv_shows s ON e.show_id = s.id
            """, conn)
            if not df_episodes.empty:
                episodes_csv = f"{export_dir}/tv_episodes_{date_str}.csv"
                df_episodes.to_csv(episodes_csv, index=False)
                
                episodes_xlsx = f"{export_dir}/tv_episodes_{date_str}.xlsx"
                df_episodes.to_excel(episodes_xlsx, index=False)
                print(f"TV Episodes exported to {episodes_xlsx}")
                
        except Exception as e:
            print(f"Export error: {e}")
        finally:
            conn.close()
