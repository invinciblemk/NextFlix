import streamlit as st
import sqlite3
import pandas as pd
import requests
from fuzzywuzzy import process  # For fuzzy matching/typo correction
from st_aggrid import AgGrid, GridOptionsBuilder  # For advanced table; ensure latest version
import os
import csv
from datetime import datetime

# Configuration (add your API keys here)
TMDB_API_KEY = '20c5b9eda5be7ed0d6be0d6a62c83683'  # From previous scripts
OMDB_API_KEY = '3822b96e'   # From previous scripts
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
OMDB_BASE_URL = 'http://www.omdbapi.com/'
TMDB_WEB_URL = 'https://www.themoviedb.org/movie/'  # For links
DEFAULT_REGION = 'US'  # Default region for watch providers; overridden by user selection

# Database path - works for both local and cloud
DB_PATH = 'movies.db' if os.path.exists('movies.db') else '/Users/invincibleMK/Documents/cinema/movies.db'
CSV_PATH = 'FavMovies.csv' if os.path.exists('FavMovies.csv') else '/Users/invincibleMK/Documents/cinema/FavMovies.csv'

# Common TMDB genre mapping (ID: name)
GENRE_MAP = {
    28: 'Action',
    12: 'Adventure',
    16: 'Animation',
    35: 'Comedy',
    80: 'Crime',
    99: 'Documentary',
    18: 'Drama',
    10751: 'Family',
    14: 'Fantasy',
    36: 'History',
    27: 'Horror',
    10402: 'Music',
    9648: 'Mystery',
    10749: 'Romance',
    878: 'Science Fiction',
    10770: 'TV Movie',
    53: 'Thriller',
    10752: 'War',
    37: 'Western'
}

# Production country mapping (code: label with industry examples)
COUNTRY_MAP = {
    'US': 'Hollywood/USA',
    'IN': 'Bollywood/India',
    'GB': 'United Kingdom',
    'FR': 'France',
    'DE': 'Germany',
    'IT': 'Italy',
    'CA': 'Canada',
    'JP': 'Japan',
    'AU': 'Australia',
    'CN': 'China',
    # Add more as needed, e.g., 'NG': 'Nollywood/Nigeria'
}

# Initialize database if it doesn't exist
def init_database():
    if not os.path.exists(DB_PATH):
        st.info("Initializing database...")
        try:
            import subprocess
            result = subprocess.run(['python', 'sync_csv_to_db.py'], capture_output=True, text=True)
            if result.returncode == 0:
                st.success("Database initialized!")
                st.rerun()
            else:
                st.error(f"Database initialization failed: {result.stderr}")
        except Exception as e:
            st.error(f"Error initializing database: {e}")

# Fetch available watch providers (cached)
@st.cache_data
def get_watch_providers(region):
    url = f"{TMDB_BASE_URL}/watch/providers/movie"
    params = {'api_key': TMDB_API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json().get('results', [])
        providers = {p['provider_id']: p['provider_name'] for p in results if region in p.get('display_priorities', {})}
        return providers
    return {}

# Connect to the database
def get_connection():
    return sqlite3.connect(DB_PATH)

def fetch_all_movies():
    conn = get_connection()
    query = """
        SELECT m.id, m.name, m.year, m.genre, m.rating, m.mood, m.imdb_rating, m.rt_rating, m.metacritic_rating, 
               m.director, m.actors, m.composer, m.duration,
               GROUP_CONCAT(k.keyword, ', ') AS keywords
        FROM movies m
        LEFT JOIN keywords k ON m.id = k.movie_id
        GROUP BY m.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def search_movies(name=None, min_year=None, max_year=None, genre=None, mood=None, min_rating=None, director=None, keyword=None, country_code=None):
    conn = get_connection()
    query = """
        SELECT m.id, m.name, m.year, m.genre, m.rating, m.mood, m.imdb_rating, m.rt_rating, m.metacritic_rating, 
               m.director, m.actors, m.composer, m.duration,
               GROUP_CONCAT(k.keyword, ', ') AS keywords
        FROM movies m
        LEFT JOIN keywords k ON m.id = k.movie_id
        WHERE 1=1
    """
    params = []
    if name:
        query += " AND LOWER(m.name) LIKE LOWER(?)"
        params.append(f"%{name}%")
    if min_year:
        query += " AND m.year >= ?"
        params.append(min_year)
    if max_year:
        query += " AND m.year <= ?"
        params.append(max_year)
    if genre:
        query += " AND LOWER(m.genre) LIKE LOWER(?)"
        params.append(f"%{genre}%")
    if mood:
        query += " AND LOWER(m.mood) LIKE LOWER(?)"
        params.append(f"%{mood}%")
    if min_rating:
        query += " AND m.rating >= ?"
        params.append(min_rating)
    if director:
        query += " AND LOWER(m.director) LIKE LOWER(?)"
        params.append(f"%{director}%")
    if keyword:
        query += " AND LOWER(k.keyword) LIKE LOWER(?)"
        params.append(f"%{keyword}%")
    query += " GROUP BY m.id"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    # If country filter and results, verify with TMDB if not in DB
    if country_code and not df.empty:
        filtered_df = []
        for _, row in df.iterrows():
            tmdb_id = get_tmdb_id(row['name'], row['year'])
            if tmdb_id:
                details = requests.get(f"{TMDB_BASE_URL}/movie/{tmdb_id}", params={'api_key': TMDB_API_KEY}).json()
                countries = [c['iso_3166_1'] for c in details.get('production_countries', [])]
                if country_code in countries:
                    filtered_df.append(row)
        df = pd.DataFrame(filtered_df)
    
    return df

def get_tmdb_id(title, year):
    search_url = f"{TMDB_BASE_URL}/search/movie"
    params = {
        'api_key': TMDB_API_KEY,
        'query': title,
        'year': year
    }
    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            return results[0]['id']
    return None

def compare_ratings():
    conn = get_connection()
    query = """
        SELECT name, year, rating AS my_rating, imdb_rating, rt_rating, metacritic_rating,
               (rating - imdb_rating) AS diff_imdb
        FROM movies
        WHERE imdb_rating IS NOT NULL
        ORDER BY ABS(rating - imdb_rating) DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_person_id(name, role=None):
    if not name:
        return None
    search_url = f"{TMDB_BASE_URL}/search/person"
    params = {
        'api_key': TMDB_API_KEY,
        'query': name
    }
    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            return results[0]['id']
    return None

def search_external_movies(query, min_year=None, max_year=None, genre_id=None, plot_keywords=None, director=None, actor=None, composer=None, writer=None, watch_provider_id=None, country_code=None):
    if not TMDB_API_KEY or TMDB_API_KEY == 'YOUR_TMDB_API_KEY':
        st.error("TMDB API key is not set. Please update TMDB_API_KEY in the script.")
        return pd.DataFrame()
    
    # Use discover endpoint for advanced filtering
    discover_url = f"{TMDB_BASE_URL}/discover/movie"
    discover_params = {
        'api_key': TMDB_API_KEY,
        'sort_by': 'popularity.desc',
        'page': 1,
        'primary_release_date.gte': f"{min_year}-01-01" if min_year else '',
        'primary_release_date.lte': f"{max_year}-12-31" if max_year else '',
        'with_genres': str(genre_id) if genre_id else None,
        'with_watch_providers': str(watch_provider_id) if watch_provider_id else None,
        'watch_region': st.session_state.get('watch_region', DEFAULT_REGION),
        'with_origin_country': country_code if country_code else None
    }
    
    # Add people filters with proper concatenation
    crew_params = []
    if director:
        dir_id = get_person_id(director, 'director')
        if dir_id:
            crew_params.append(str(dir_id))
    if composer:
        comp_id = get_person_id(composer, 'composer')
        if comp_id:
            crew_params.append(str(comp_id))
    if writer:
        writ_id = get_person_id(writer, 'writer')
        if writ_id:
            crew_params.append(str(writ_id))
    if crew_params:
        discover_params['with_crew'] = ','.join(crew_params)
    if actor:
        act_id = get_person_id(actor, 'actor')
        if act_id:
            discover_params['with_cast'] = str(act_id)
    
    # For query and plot keywords, use search endpoint and apply filters client-side
    if query or plot_keywords:
        search_url = f"{TMDB_BASE_URL}/search/movie"
        search_params = {
            'api_key': TMDB_API_KEY,
            'query': f"{query} {plot_keywords}" if plot_keywords else query,
            'page': 1
        }
        response = requests.get(search_url, params=search_params)
        if response.status_code == 200:
            results = response.json().get('results', [])
            # Client-side filter for year range, watch providers, and country
            filtered_results = []
            for movie in results:
                release_year = int(movie['release_date'][:4]) if movie.get('release_date') and movie['release_date'] else None
                if release_year and ((not min_year or release_year >= min_year) and (not max_year or release_year <= max_year)):
                    watch_info = get_watch_info(movie['id'])
                    if not watch_provider_id or WATCH_PROVIDERS.get(watch_provider_id, '') in watch_info:
                        # Fetch details for country check
                        details_response = requests.get(f"{TMDB_BASE_URL}/movie/{movie['id']}", params={'api_key': TMDB_API_KEY})
                        if details_response.status_code == 200:
                            details = details_response.json()
                            countries = [c['iso_3166_1'] for c in details.get('production_countries', [])]
                            if not country_code or country_code in countries:
                                filtered_results.append(movie)
            results = filtered_results
    else:
        response = requests.get(discover_url, params=discover_params)
        if response.status_code == 200:
            results = response.json().get('results', [])
    
    if response.status_code != 200:
        st.error(f"TMDB API error: {response.status_code} - {response.text}")
        return pd.DataFrame()
    
    if not results:
        st.warning("No results from TMDB.")
        return pd.DataFrame()
    
    external_movies = []
    conn = get_connection()  # For checking local ratings
    c = conn.cursor()
    for movie in results:
        movie_id = movie['id']
        title = movie['title']
        release_year = movie['release_date'][:4] if movie['release_date'] else 'N/A'
        overview = movie['overview']
        tmdb_rating = movie['vote_average']
        
        # Map genres
        genres = ', '.join([GENRE_MAP.get(g, 'Unknown') for g in movie.get('genre_ids', [])])
        
        # Fetch credits for additional fields
        credits_url = f"{TMDB_BASE_URL}/movie/{movie_id}/credits"
        credits_response = requests.get(credits_url, params={'api_key': TMDB_API_KEY})
        credits = credits_response.json() if credits_response.status_code == 200 else {}
        
        directors = ', '.join([p['name'] for p in credits.get('crew', []) if p['job'] == 'Director'])
        cast = ', '.join([p['name'] for p in credits.get('cast', [])[:5]])
        composers = ', '.join([p['name'] for p in credits.get('crew', []) if p['job'] in ['Original Music Composer', 'Music', 'Composer']])
        writers = ', '.join([p['name'] for p in credits.get('crew', []) if p['job'] in ['Writer', 'Screenplay']])
        
        # Fetch details for producer, studio, budget, revenue, and duration
        details_url = f"{TMDB_BASE_URL}/movie/{movie_id}"
        details_response = requests.get(details_url, params={'api_key': TMDB_API_KEY})
        details = details_response.json() if details_response.status_code == 200 else {}
        
        producers = ', '.join([p['name'] for p in credits.get('crew', []) if p['job'] == 'Producer'][:3])
        studios = ', '.join([c['name'] for c in details.get('production_companies', [])])
        budget = details.get('budget', 0)
        revenue = details.get('revenue', 0)
        duration = details.get('runtime', 0)
        budget_str = f"${budget:,}" if budget > 0 else 'N/A'
        revenue_str = f"${revenue:,}" if revenue > 0 else 'N/A'
        duration_str = f"{duration} min" if duration > 0 else 'N/A'
        
        # Fetch ratings from OMDB
        omdb_params = {'apikey': OMDB_API_KEY, 't': title, 'y': release_year}
        omdb_response = requests.get(OMDB_BASE_URL, params=omdb_params)
        if omdb_response.status_code == 200:
            omdb_data = omdb_response.json() if omdb_response.json().get('Response') == 'True' else {}
            imdb_val = omdb_data.get('imdbRating', 'N/A')
            imdb_rating = float(imdb_val) if imdb_val != 'N/A' and imdb_val is not None else None
            rt_rating = next((r['Value'] for r in omdb_data.get('Ratings', []) if r['Source'] == 'Rotten Tomatoes'), None)
            metacritic_val = next((r['Value'] for r in omdb_data.get('Ratings', []) if r['Source'] == 'Metacritic'), 'N/A')
            metacritic = int(metacritic_val.replace('/100', '')) if metacritic_val != 'N/A' and metacritic_val is not None else None
        else:
            imdb_rating = None
            rt_rating = None
            metacritic = None

        # Fetch where to watch with links (as HTML)
        where_to_watch = get_watch_info(movie_id)

        # Check local DB for My Rating
        c.execute("SELECT rating FROM movies WHERE name = ? AND year = ?", (title, int(release_year) if release_year != 'N/A' else None))
        local_rating = c.fetchone()
        my_rating = local_rating[0] if local_rating else 'N/A'

        external_movies.append({
            'Title': title,
            'Year': release_year,
            'Genres': genres,
            'Director': directors,
            'Cast': cast,
            'Composer': composers,
            'Writer': writers,
            'Producer': producers,
            'Studio': studios,
            'Budget': budget_str,
            'Box Office': revenue_str,
            'Overview': overview,
            'My Rating': my_rating,
            'Where to Watch': where_to_watch,
            'TMDB Rating': tmdb_rating,
            'IMDb Rating': imdb_rating,
            'RT Rating': rt_rating,
            'Metacritic': metacritic,
            'Duration': duration_str,
            'TMDB Link': f"{TMDB_WEB_URL}{movie_id}"
        })
    
    conn.close()
    df = pd.DataFrame(external_movies)
    if df.empty:
        st.warning("No enriched results after fetching details.")
    return df

def get_watch_info(movie_id):
    url = f"{TMDB_BASE_URL}/movie/{movie_id}/watch/providers"
    params = {'api_key': TMDB_API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json().get('results', {}).get(st.session_state.get('watch_region', DEFAULT_REGION), {})
        flatrate = data.get('flatrate', [])
        if flatrate:
            providers = []
            base_link = data.get('link', '')
            for p in flatrate:
                name = p['provider_name']
                providers.append(f'<a href="{base_link}" target="_blank">{name}</a>')
            return ' '.join(providers)
        return 'Not available in selected region'
    return 'N/A'

def get_recommended_movies(min_rating=3.5, num_recs=5):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name, year, rating FROM movies WHERE rating >= ?", (min_rating,))
    liked_movies = c.fetchall()
    conn.close()
    
    if not liked_movies:
        return pd.DataFrame()
    
    watched_titles = {row[0].lower() for row in liked_movies}
    all_recommendations = []
    
    for name, year, _ in liked_movies:
        search_url = f"{TMDB_BASE_URL}/search/movie"
        search_params = {
            'api_key': TMDB_API_KEY,
            'query': name,
            'year': year
        }
        response = requests.get(search_url, params=search_params)
        if response.status_code == 200:
            results = response.json().get('results', [])
            if results:
                movie_id = results[0]['id']
                rec_url = f"{TMDB_BASE_URL}/movie/{movie_id}/recommendations"
                rec_params = {
                    'api_key': TMDB_API_KEY,
                    'page': 1
                }
                rec_response = requests.get(rec_url, params=rec_params)
                if rec_response.status_code == 200:
                    recs = rec_response.json().get('results', [])[:num_recs]
                    for rec in recs:
                        rec_title = rec['title'].lower()
                        if rec_title not in watched_titles:
                            all_recommendations.append({
                                'Title': rec['title'],
                                'Year': rec['release_date'][:4] if rec['release_date'] else 'N/A',
                                'Overview': rec['overview'],
                                'TMDB Rating': rec['vote_average'],
                                'Based On': name
                            })
    
    unique_recs = {rec['Title']: rec for rec in all_recommendations}
    return pd.DataFrame(list(unique_recs.values())[:10])

# NEW FUNCTIONS FOR ADDING MOVIES
def search_tmdb_movie(title, year=None):
    """Search TMDB for a movie and return detailed information"""
    search_url = f"{TMDB_BASE_URL}/search/movie"
    params = {
        'api_key': TMDB_API_KEY,
        'query': title,
        'year': year
    }
    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            return results[0]  # Return first result
    return None

def get_movie_details_from_tmdb(tmdb_id):
    """Get comprehensive movie details from TMDB"""
    # Get basic details
    details_url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
    details_response = requests.get(details_url, params={'api_key': TMDB_API_KEY})
    details = details_response.json() if details_response.status_code == 200 else {}
    
    # Get credits
    credits_url = f"{TMDB_BASE_URL}/movie/{tmdb_id}/credits"
    credits_response = requests.get(credits_url, params={'api_key': TMDB_API_KEY})
    credits = credits_response.json() if credits_response.status_code == 200 else {}
    
    # Get ratings from OMDB
    title = details.get('title', '')
    year = details.get('release_date', '')[:4] if details.get('release_date') else None
    omdb_params = {'apikey': OMDB_API_KEY, 't': title, 'y': year}
    omdb_response = requests.get(OMDB_BASE_URL, params=omdb_params)
    omdb_data = {}
    if omdb_response.status_code == 200:
        omdb_data = omdb_response.json() if omdb_response.json().get('Response') == 'True' else {}
    
    # Extract information
    movie_data = {
        'name': details.get('title', ''),
        'year': int(year) if year else None,
        'genre': ', '.join([GENRE_MAP.get(g, 'Unknown') for g in details.get('genre_ids', [])]),
        'plot': details.get('overview', ''),
        'duration': details.get('runtime'),
        'budget': details.get('budget', 0),
        'revenue': details.get('revenue', 0),
        'director': ', '.join([p['name'] for p in credits.get('crew', []) if p['job'] == 'Director']),
        'actors': ', '.join([p['name'] for p in credits.get('cast', [])[:5]]),
        'composer': ', '.join([p['name'] for p in credits.get('crew', []) if p['job'] in ['Original Music Composer', 'Music', 'Composer']]),
        'producer': ', '.join([p['name'] for p in credits.get('crew', []) if p['job'] == 'Producer'][:3]),
        'studio': ', '.join([c['name'] for c in details.get('production_companies', [])]),
        'imdb_rating': float(omdb_data.get('imdbRating', 0)) if omdb_data.get('imdbRating', 'N/A') != 'N/A' else None,
        'rt_rating': next((r['Value'] for r in omdb_data.get('Ratings', []) if r['Source'] == 'Rotten Tomatoes'), None),
        'metacritic_rating': int(next((r['Value'].replace('/100', '') for r in omdb_data.get('Ratings', []) if r['Source'] == 'Metacritic'), '0')) if next((r['Value'] for r in omdb_data.get('Ratings', []) if r['Source'] == 'Metacritic'), 'N/A') != 'N/A' else None
    }
    
    return movie_data



def add_movie_to_database(movie_data, user_rating, mood, keywords):
    """Add a movie to the database"""
    conn = get_connection()
    c = conn.cursor()
    
    try:
        # Insert movie
        c.execute("""
            INSERT OR REPLACE INTO movies 
            (name, year, genre, rating, mood, imdb_rating, rt_rating, metacritic_rating, 
             director, actors, composer, producer, studio, plot, duration) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            movie_data['name'], movie_data['year'], movie_data['genre'], user_rating, mood,
            movie_data['imdb_rating'], movie_data['rt_rating'], movie_data['metacritic_rating'],
            movie_data['director'], movie_data['actors'], movie_data['composer'],
            movie_data['producer'], movie_data['studio'], movie_data['plot'], movie_data['duration']
        ))
        
        # Get movie ID
        movie_id = c.lastrowid
        
        # Add keywords
        if keywords:
            keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
            for keyword in keyword_list:
                c.execute("INSERT INTO keywords (movie_id, keyword) VALUES (?, ?)", (movie_id, keyword))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Error adding movie: {e}")
        return False
    finally:
        conn.close()

def add_movie_to_csv(movie_data, user_rating, mood, keywords):
    """Add a movie to the CSV file using pandas"""
    try:
        # Prepare new row data
        keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()] if keywords else []
        while len(keyword_list) < 4:
            keyword_list.append('')
        
        new_row = {
            '@': '',
            'Movie Name': movie_data['name'],
            'Year of Release': str(movie_data['year']) if movie_data['year'] else '',
            'Genre': movie_data.get('genre', ''),
            'My rating': str(user_rating),
            'producer': movie_data.get('producer', ''),
            'Mood': mood,
            'Keywords': keyword_list[0] if len(keyword_list) > 0 else '',
            '': keyword_list[1] if len(keyword_list) > 1 else '',
            '': keyword_list[2] if len(keyword_list) > 2 else '',
            '': keyword_list[3] if len(keyword_list) > 3 else ''
        }
        
        # Read existing CSV or create new one
        if os.path.exists(CSV_PATH):
            try:
                df = pd.read_csv(CSV_PATH)
            except Exception:
                # If reading fails, create new DataFrame
                df = pd.DataFrame(columns=['@', 'Movie Name', 'Year of Release', 'Genre', 'My rating', 'producer', 'Mood', 'Keywords', '', '', ''])
        else:
            df = pd.DataFrame(columns=['@', 'Movie Name', 'Year of Release', 'Genre', 'My rating', 'producer', 'Mood', 'Keywords', '', '', ''])
        
        # Add new row
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        # Write back to CSV
        df.to_csv(CSV_PATH, index=False)
        
        return True
    except Exception as e:
        st.error(f"Error adding to CSV: {e}")
        import traceback
        st.error(f"Full error: {traceback.format_exc()}")
        return False


# Streamlit app
st.title("Movie Database GUI")
st.write("App loaded successfully! If you see this, the script is running.")

# Initialize database if needed
init_database()

# Global region selection for watch providers
watch_region_name = st.selectbox("Select Region for Watch Providers", list(COUNTRY_MAP.values()), index=0, key="watch_region_select")
watch_region_code = next((code for code, name in COUNTRY_MAP.items() if name == watch_region_name), 'US')
st.session_state['watch_region'] = watch_region_code
WATCH_PROVIDERS = get_watch_providers(watch_region_code)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["View All Movies", "Search Local Movies", "Compare Ratings", "Search External (TMDB/IMDB)", "Recommended Movies", "Add New Movie"])

with tab1:
    st.header("All Movies")
    df = fetch_all_movies()
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download as CSV", csv, "all_movies.csv", "text/csv")

with tab2:
    st.header("Search Local Movies")
    name = st.text_input("Movie Name (partial match)", key="local_name")
    col1, col2 = st.columns(2)
    min_year = col1.number_input("Min Year", value=None, min_value=1900, max_value=2100, key="local_min_year")
    max_year = col2.number_input("Max Year", value=None, min_value=1900, max_value=2100, key="local_max_year")
    genre = st.text_input("Genre (partial match)", key="local_genre")
    mood = st.text_input("Mood (partial match)", key="local_mood")
    min_rating = st.number_input("Minimum My Rating", value=None, min_value=0.0, max_value=5.0, step=0.5, key="local_min_rating")
    director = st.text_input("Director (partial match)", key="local_director")
    keyword = st.text_input("Keyword (partial match)", key="local_keyword")
    local_country_name = st.selectbox("Production Country (optional, e.g., Hollywood/USA)", [''] + list(COUNTRY_MAP.values()), key="local_country_select")
    local_country_code = next((code for code, name in COUNTRY_MAP.items() if name == local_country_name), None)
    if st.button("Search Local"):
        df = search_movies(name, min_year, max_year, genre, mood, min_rating, director, keyword, local_country_code)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Results as CSV", csv, "search_results.csv", "text/csv")

with tab3:
    st.header("Compare My Ratings to External Ratings")
    df = compare_ratings()
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Comparisons as CSV", csv, "ratings_comparison.csv", "text/csv")

with tab4:
    st.header("Search External Movies (TMDB/IMDB)")
    ext_query = st.text_input("Movie Name or Keyword")
    col3, col4 = st.columns(2)
    ext_min_year = col3.number_input("Min Year (optional)", value=None, min_value=1900, max_value=2100)
    ext_max_year = col4.number_input("Max Year (optional)", value=None, min_value=1900, max_value=2100)
    ext_genre_name = st.selectbox("Genre (optional)", [''] + list(GENRE_MAP.values()), key="ext_genre_select")
    ext_genre_id = next((id for id, name in GENRE_MAP.items() if name == ext_genre_name), None)
    ext_plot = st.text_input("Plot/Overview Keywords (optional)")
    ext_director = st.text_input("Director (optional)")
    ext_actor = st.text_input("Actor/Cast (optional)")
    ext_composer = st.text_input("Music Composer (optional)")
    ext_writer = st.text_input("Writer (optional)")
    ext_watch_provider_name = st.selectbox("Where to Watch (optional)", [''] + sorted(list(WATCH_PROVIDERS.values())), key="ext_watch_select")
    ext_watch_provider_id = next((id for id, name in WATCH_PROVIDERS.items() if name == ext_watch_provider_name), None)
    ext_country_name = st.selectbox("Production Country (optional, e.g., Hollywood/USA)", [''] + list(COUNTRY_MAP.values()), key="ext_country_select")
    ext_country_code = next((code for code, name in COUNTRY_MAP.items() if name == ext_country_name), None)
    if st.button("Search External"):
        if not ext_query and not ext_director and not ext_actor and not ext_composer and not ext_writer and not ext_watch_provider_id and not ext_country_code:
            st.warning("Please enter at least one search criterion.")
        else:
            ext_df = search_external_movies(ext_query, ext_min_year, ext_max_year, ext_genre_id, ext_plot, ext_director, ext_actor, ext_composer, ext_writer, ext_watch_provider_id, ext_country_code)
            if ext_df.empty:
                st.warning("No results found. Check API keys, network, or try different criteria.")
            else:
                # Use AgGrid for clickable links, wrapping, and auto-fit
                gb = GridOptionsBuilder.from_dataframe(ext_df)
                gb.configure_default_column(resizable=True, filterable=True, sortable=True, wrapText=True, autoHeight=True)
                gb.configure_column("Overview", wrapText=True, autoHeight=True, minWidth=300)
                gb.configure_column("TMDB Link", cellRenderer="agLinkCellRenderer")
                gb.configure_column("Where to Watch", wrapText=True, autoHeight=True, minWidth=200, cellRenderer="agRichSelectCellEditor")
                gb.configure_grid_options(autoSizeAllColumns=True)
                grid_options = gb.build()
                AgGrid(ext_df, gridOptions=grid_options, height=400, allow_unsafe_jscode=True, enable_enterprise_modules=False)
                csv = ext_df.to_csv(index=False).encode('utf-8')
                st.download_button("Download External Results as CSV", csv, "external_movies.csv", "text/csv")

with tab5:
    st.header("Recommended Movies")
    st.write("Recommendations based on your highly rated movies (rating >= 3.5).")
    rec_min_rating = st.number_input("Minimum Rating for Liked Movies", value=3.5, min_value=0.0, max_value=5.0, step=0.5)
    rec_num = st.number_input("Number of Recs per Movie", value=5, min_value=1, max_value=10)
    if st.button("Generate Recommendations"):
        rec_df = get_recommended_movies(rec_min_rating, rec_num)
        if rec_df.empty:
            st.warning("No recommendations found. Try adjusting the minimum rating or add more movies to your DB.")
        else:
            st.dataframe(rec_df, use_container_width=True)
            csv = rec_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Recommendations as CSV", csv, "recommended_movies.csv", "text/csv")

with tab6:
    st.header("Add New Movie")
    st.write("Add a movie to your database. Just provide the title and year - we'll fill in the rest!")
    
    # Movie search form
    with st.form("add_movie_form"):
        col1, col2 = st.columns(2)
        movie_title = col1.text_input("Movie Title *", placeholder="e.g., The Godfather")
        movie_year = col2.number_input("Year (optional)", value=None, min_value=1900, max_value=2030, help="Leave empty to search without year filter")
        
        if st.form_submit_button("Search Movie"):
            if movie_title:
                with st.spinner("Searching for movie details..."):
                    # Search TMDB
                    tmdb_result = search_tmdb_movie(movie_title, movie_year)
                    
                    if tmdb_result:
                        st.success(f"Found: {tmdb_result['title']} ({tmdb_result['release_date'][:4] if tmdb_result.get('release_date') else 'N/A'})")
                        
                        # Get detailed information
                        movie_details = get_movie_details_from_tmdb(tmdb_result['id'])
                        
                        # Store in session state for the form below
                        st.session_state['selected_movie'] = movie_details
                        st.session_state['tmdb_id'] = tmdb_result['id']
                    else:
                        st.error("Movie not found. Please check the title and year.")
                        st.session_state['selected_movie'] = None
            else:
                st.warning("Please enter a movie title.")
    
    # Movie details form (appears after search)
    if 'selected_movie' in st.session_state and st.session_state['selected_movie']:
        movie_data = st.session_state['selected_movie']
        
        st.subheader("Movie Details")
        
        # Display auto-filled information
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Title:** {movie_data['name']}")
            st.write(f"**Year:** {movie_data['year']}")
            st.write(f"**Genre:** {movie_data['genre']}")
            st.write(f"**Director:** {movie_data['director']}")
            st.write(f"**Duration:** {movie_data['duration']} min" if movie_data['duration'] else "**Duration:** N/A")
        
        with col2:
            st.write(f"**IMDb Rating:** {movie_data['imdb_rating']}" if movie_data['imdb_rating'] else "**IMDb Rating:** N/A")
            st.write(f"**RT Rating:** {movie_data['rt_rating']}" if movie_data['rt_rating'] else "**RT Rating:** N/A")
            st.write(f"**Metacritic:** {movie_data['metacritic_rating']}" if movie_data['metacritic_rating'] else "**Metacritic:** N/A")
            st.write(f"**Budget:** ${movie_data['budget']:,}" if movie_data['budget'] else "**Budget:** N/A")
            st.write(f"**Box Office:** ${movie_data['revenue']:,}" if movie_data['revenue'] else "**Box Office:** N/A")
        
        if movie_data['plot']:
            st.write(f"**Plot:** {movie_data['plot']}")
        
        # User input form
        with st.form("add_movie_details"):
            st.subheader("Your Rating & Notes")
            
            col1, col2 = st.columns(2)
            user_rating = col1.number_input("Your Rating (0-5)", min_value=0.0, max_value=5.0, step=0.5, value=3.0)
            mood = col2.text_input("Mood when watching", placeholder="e.g., Excited, Relaxed, Bored")
            
            keywords = st.text_input("Keywords (comma-separated)", placeholder="e.g., Action, Thriller, Classic")
            
            col1, col2 = st.columns(2)
            add_to_db = col1.checkbox("Add to Database", value=True)
            add_to_csv = col2.checkbox("Add to CSV", value=True)
            
            if st.form_submit_button("Add Movie"):
                success_db = True
                success_csv = True
                
                if add_to_db:
                    success_db = add_movie_to_database(movie_data, user_rating, mood, keywords)
                
                if add_to_csv:
                    success_csv = add_movie_to_csv(movie_data, user_rating, mood, keywords)
                
                if success_db and success_csv:
                    st.success("Movie added successfully!")
                    # Clear session state
                    st.session_state['selected_movie'] = None
                    st.session_state['tmdb_id'] = None
                    st.rerun()
                elif success_db or success_csv:
                    st.warning("Movie added partially. Check the error messages above.")
                else:
                    st.error("Failed to add movie. Please try again.")
    
    # Manual entry option
    st.subheader("Manual Entry (if movie not found)")
    with st.expander("Add Movie Manually"):
        with st.form("manual_movie_form"):
            col1, col2 = st.columns(2)
            manual_title = col1.text_input("Title *")
            manual_year = col2.number_input("Year *", min_value=1900, max_value=2030)
            manual_genre = st.text_input("Genre")
            manual_rating = st.number_input("Your Rating (0-5)", min_value=0.0, max_value=5.0, step=0.5, value=3.0)
            manual_mood = st.text_input("Mood")
            manual_keywords = st.text_input("Keywords (comma-separated)")
            
            if st.form_submit_button("Add Manual Entry"):
                if manual_title and manual_year:
                    manual_movie_data = {
                        'name': manual_title,
                        'year': manual_year,
                        'genre': manual_genre,
                        'plot': '',
                        'duration': None,
                        'director': '',
                        'actors': '',
                        'composer': '',
                        'producer': '',
                        'studio': '',
                        'imdb_rating': None,
                        'rt_rating': None,
                        'metacritic_rating': None
                    }
                    
                    success_db = add_movie_to_database(manual_movie_data, manual_rating, manual_mood, manual_keywords)
                    success_csv = add_movie_to_csv(manual_movie_data, manual_rating, manual_mood, manual_keywords)
                    
                    if success_db and success_csv:
                        st.success("Manual entry added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add manual entry.")
                else:
                    st.warning("Please fill in at least title and year.")