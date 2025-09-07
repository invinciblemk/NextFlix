import csv
import sqlite3
import requests

# Configuration
OMDB_API_KEY = '3822b96e'  # Replace with your actual OMDB API key
TMDB_API_KEY = '20c5b9eda5be7ed0d6be0d6a62c83683'  # Replace with your actual TMDB API key
OMDB_BASE_URL = 'http://www.omdbapi.com/'
TMDB_BASE_URL = 'https://api.themoviedb.org/3'

# Connect to (or create) the SQLite database
conn = sqlite3.connect('/Users/invincibleMK/Documents/cinema/movies.db')
c = conn.cursor()

# Create tables if they don't exist
c.execute('''
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY,
        name TEXT,
        year INTEGER,
        genre TEXT,
        rating REAL,
        mood TEXT,
        imdb_rating REAL,
        rt_rating TEXT,
        metacritic_rating INTEGER,
        director TEXT,
        actors TEXT,
        composer TEXT,
        UNIQUE(name, year)
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY,
        movie_id INTEGER,
        keyword TEXT,
        FOREIGN KEY(movie_id) REFERENCES movies(id)
    )
''')

# Add new columns if they don't exist (migration)
def add_column_if_not_exists(table, column, column_type):
    c.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in c.fetchall()]
    if column not in columns:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")

add_column_if_not_exists('movies', 'producer', 'TEXT')
add_column_if_not_exists('movies', 'studio', 'TEXT')
add_column_if_not_exists('movies', 'plot', 'TEXT')
add_column_if_not_exists('movies', 'duration', 'INTEGER')  # New field for movie duration in minutes

def fetch_external_data(title, year):
    # Fetch from OMDB for ratings
    omdb_params = {
        'apikey': OMDB_API_KEY,
        't': title,
        'y': year,
        'plot': 'short',
        'r': 'json'
    }
    omdb_response = requests.get(OMDB_BASE_URL, params=omdb_params)
    omdb_data = {}
    if omdb_response.status_code == 200:
        omdb_data = omdb_response.json()
        if omdb_data.get('Response') != 'True':
            omdb_data = {}

    # Fetch movie ID from TMDB for details and credits
    tmdb_search_url = f"{TMDB_BASE_URL}/search/movie"
    tmdb_search_params = {
        'api_key': TMDB_API_KEY,
        'query': title,
        'year': year
    }
    tmdb_response = requests.get(tmdb_search_url, params=tmdb_search_params)
    tmdb_movie_id = None
    plot = None
    if tmdb_response.status_code == 200:
        results = tmdb_response.json().get('results', [])
        if results:
            tmdb_movie_id = results[0]['id']
            plot = results[0]['overview']  # Get plot/overview

    # Fetch credits and details from TMDB
    director = None
    actors = None
    composer = None
    producer = None
    studio = None
    duration = None  # New variable for duration
    if tmdb_movie_id:
        # Credits
        credits_url = f"{TMDB_BASE_URL}/movie/{tmdb_movie_id}/credits"
        credits_params = {'api_key': TMDB_API_KEY}
        credits_response = requests.get(credits_url, params=credits_params)
        if credits_response.status_code == 200:
            credits = credits_response.json()
            # Director
            directors = [person['name'] for person in credits.get('crew', []) if person['job'] == 'Director']
            director = ', '.join(directors) if directors else None
            # Top 5 actors
            cast_list = [person['name'] for person in credits.get('cast', [])[:5]]
            actors = ', '.join(cast_list) if cast_list else None
            # Composer
            composers = [person['name'] for person in credits.get('crew', []) if person['job'] in ['Original Music Composer', 'Music', 'Composer']]
            composer = ', '.join(composers) if composers else None
            # Producer (top 3)
            producers = [person['name'] for person in credits.get('crew', []) if person['job'] == 'Producer'][:3]
            producer = ', '.join(producers) if producers else None

        # Movie details for studios
        details_url = f"{TMDB_BASE_URL}/movie/{tmdb_movie_id}"
        details_params = {'api_key': TMDB_API_KEY}
        details_response = requests.get(details_url, params=details_params)
        if details_response.status_code == 200:
            details = details_response.json()
            studios = [company['name'] for company in details.get('production_companies', [])]
            studio = ', '.join(studios) if studios else None
            duration = details.get('runtime')  # Duration in minutes (TMDB)
    # Fetch ratings from OMDB
    imdb = None
    rt = None
    metacritic = None
    if omdb_data:
        ratings = {r['Source']: r['Value'] for r in omdb_data.get('Ratings', [])}
        imdb_val = omdb_data.get('imdbRating', 'N/A')
        imdb = float(imdb_val) if imdb_val != 'N/A' else None
        rt = ratings.get('Rotten Tomatoes', None)
        metacritic_val = ratings.get('Metacritic', 'N/A')
        metacritic = int(metacritic_val.replace('/100', '')) if metacritic_val != 'N/A' else None

    # Cross-checks (e.g., director)
    omdb_director = omdb_data.get('Director', None)
    if director and omdb_director and director != omdb_director:
        print(f"Director mismatch for '{title}': TMDB says '{director}', OMDB says '{omdb_director}'. Using TMDB.")
    
    # Cross-check duration with OMDB if TMDB is missing
    if duration is None and omdb_data:
        runtime_str = omdb_data.get('Runtime', 'N/A')
        if runtime_str != 'N/A':
            try:
                duration = int(runtime_str.replace(' min', ''))
            except ValueError:
                duration = None
    
    return imdb, rt, metacritic, director, actors, composer, producer, studio, plot, duration

# Read and sync from CSV
with open('/Users/invincibleMK/Documents/cinema/FavMovies.csv', 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header row
    for row in reader:
        if len(row) < 7:  # Adjusted for extra producer column
            continue
        name = row[1].strip()
        year = int(row[2])
        genre = row[3].strip()
        rating = float(row[4])
        # Skip producer from CSV (fetched from API instead)
        mood = row[6].strip() if len(row) > 6 else ''
        
        # Fetch external data if missing
        c.execute("SELECT imdb_rating, director, composer, producer, studio, plot, duration FROM movies WHERE name = ? AND year = ?", (name, year))  # Added duration
        existing = c.fetchone()
        if existing is None or any(val is None for val in existing):
            imdb_rating, rt_rating, metacritic_rating, director, actors, composer, producer, studio, plot, duration = fetch_external_data(name, year)  # Added duration
        else:
            imdb_rating, rt_rating, metacritic_rating, director, actors, composer, producer, studio, plot, duration = [None] * 10  # Adjusted count
        
        # Upsert movie
        c.execute("""
            INSERT INTO movies (name, year, genre, rating, mood, imdb_rating, rt_rating, metacritic_rating, director, actors, composer, producer, studio, plot, duration) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
            ON CONFLICT(name, year) DO UPDATE SET 
                genre = excluded.genre, 
                rating = excluded.rating,
                mood = excluded.mood,
                imdb_rating = COALESCE(excluded.imdb_rating, movies.imdb_rating),
                rt_rating = COALESCE(excluded.rt_rating, movies.rt_rating),
                metacritic_rating = COALESCE(excluded.metacritic_rating, movies.metacritic_rating),
                director = COALESCE(excluded.director, movies.director),
                actors = COALESCE(excluded.actors, movies.actors),
                composer = COALESCE(excluded.composer, movies.composer),
                producer = COALESCE(excluded.producer, movies.producer),
                studio = COALESCE(excluded.studio, movies.studio),
                plot = COALESCE(excluded.plot, movies.plot),
                duration = COALESCE(excluded.duration, movies.duration)
        """, (name, year, genre, rating, mood, imdb_rating, rt_rating, metacritic_rating, director, actors, composer, producer, studio, plot, duration))
        
        # Get movie ID
        c.execute("SELECT id FROM movies WHERE name = ? AND year = ?", (name, year))
        movie_id = c.fetchone()[0]
        
        # Clear and insert keywords
        c.execute("DELETE FROM keywords WHERE movie_id = ?", (movie_id,))
        for kw in row[7:]:  # Adjusted for extra columns
            kw = kw.strip()
            if kw:
                c.execute("INSERT INTO keywords (movie_id, keyword) VALUES (?, ?)", (movie_id, kw))

# Commit changes and close
conn.commit()
conn.close()

print("Database synced successfully with FavMovies.csv, including additional fields from TMDB/OMDB")