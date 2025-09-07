import streamlit as st
import sqlite3
import pandas as pd
import requests
from fuzzywuzzy import process
import os
import csv
from datetime import datetime
import base64

# Configuration
TMDB_API_KEY = '20c5b9eda5be7ed0d6be0d6a62c83683'
OMDB_API_KEY = '3822b96e'
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
OMDB_BASE_URL = 'http://www.omdbapi.com/'
TMDB_WEB_URL = 'https://www.themoviedb.org/movie/'
DEFAULT_REGION = 'US'

# Database path - works for both local and cloud
DB_PATH = 'movies.db' if os.path.exists('movies.db') else '/Users/invincibleMK/Documents/cinema/movies.db'
CSV_PATH = 'FavMovies.csv' if os.path.exists('FavMovies.csv') else '/Users/invincibleMK/Documents/cinema/FavMovies.csv'
LOGO_PATH = 'NextFlix_logo.png' if os.path.exists('NextFlix_logo.png') else '/Users/invincibleMK/Documents/cinema/NextFlix_logo.png'

# Netflix-style CSS
def load_css():
    st.markdown("""
    <style>
    /* Netflix-style CSS with Netflix Red theme */
    .main-header {
        background: linear-gradient(135deg, #E50914 0%, #B81D13 100%);
        padding: 1rem 0;
        margin-bottom: 2rem;
        border-radius: 10px;
    }
    
    .logo-container {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1rem;
    }
    
    .logo {
        max-height: 80px;
        width: auto;
    }
    
    .netflix-red {
        color: #E50914;
    }
    
    .netflix-dark {
        background-color: #141414;
        color: #FFFFFF;
    }
    
    .movie-card {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #E50914;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .search-container {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #333;
    }
    
    .tab-container {
        background: #141414;
        border-radius: 10px;
        padding: 1rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #2d2d2d;
        color: #FFFFFF;
        border-radius: 5px 5px 0 0;
        padding: 0.5rem 1rem;
        margin-right: 2px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #E50914;
        color: #FFFFFF;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #E50914 0%, #B81D13 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #B81D13 0%, #E50914 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(229, 9, 20, 0.3);
    }
    
    .stSelectbox > div > div {
        background-color: #2d2d2d;
        color: #FFFFFF;
    }
    
    .stTextInput > div > div > input {
        background-color: #2d2d2d;
        color: #FFFFFF;
        border: 1px solid #555;
    }
    
    .stNumberInput > div > div > input {
        background-color: #2d2d2d;
        color: #FFFFFF;
        border: 1px solid #555;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #E50914;
    }
    
    .success-message {
        background: linear-gradient(135deg, #00C851 0%, #007E33 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .error-message {
        background: linear-gradient(135deg, #FF4444 0%, #CC0000 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .edit-form {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

def display_logo():
    """Display the NextFlix logo"""
    try:
        if os.path.exists(LOGO_PATH):
            with open(LOGO_PATH, "rb") as f:
                logo_data = f.read()
                logo_base64 = base64.b64encode(logo_data).decode()
                st.markdown(f"""
                <div class="logo-container">
                    <img src="data:image/png;base64,{logo_base64}" class="logo" alt="NextFlix Logo">
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="logo-container">
                <h1 class="netflix-red" style="font-size: 3rem; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">NEXTFLIX</h1>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.markdown("""
        <div class="logo-container">
            <h1 class="netflix-red" style="font-size: 3rem; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">NEXTFLIX</h1>
        </div>
        """, unsafe_allow_html=True)

# Load CSS and display logo
load_css()
st.markdown('<div class="main-header">', unsafe_allow_html=True)
display_logo()
st.markdown('</div>', unsafe_allow_html=True)

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

def search_movies(name=None, min_year=None, max_year=None, genre=None, mood=None, min_rating=None, director=None, actor=None, keyword=None, country_code=None):
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
    if actor:  # FIXED: Added actor search
        query += " AND LOWER(m.actors) LIKE LOWER(?)"
        params.append(f"%{actor}%")
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

# FIXED: Enhanced external search with better filtering
def search_external_movies(query=None, min_year=None, max_year=None, genre_id=None, plot_keywords=None, director=None, actor=None, composer=None, writer=None, watch_provider_id=None, country_code=None):
    if not TMDB_API_KEY or TMDB_API_KEY == 'YOUR_TMDB_API_KEY':
        st.error("TMDB API key is not set. Please update TMDB_API_KEY in the script.")
        return pd.DataFrame()
    
    # FIXED: Check if any search criteria is provided
    has_search_criteria = any([
        query, min_year, max_year, genre_id, plot_keywords, 
        director, actor, composer, writer, watch_provider_id, country_code
    ])
    
    if not has_search_criteria:
        st.warning("Please enter at least one search criterion.")
        return pd.DataFrame()
    
    # Use discover endpoint for advanced filtering
    discover_url = f"{TMDB_BASE_URL}/discover/movie"
    discover_params = {
        'api_key': TMDB_API_KEY,
        'sort_by': 'popularity.desc',
        'page': 1,
    }
    
    # Add filters only if they have values
    if min_year:
        discover_params['primary_release_date.gte'] = f"{min_year}-01-01"
    if max_year:
        discover_params['primary_release_date.lte'] = f"{max_year}-12-31"
    if genre_id:
        discover_params['with_genres'] = str(genre_id)
    if watch_provider_id:
        discover_params['with_watch_providers'] = str(watch_provider_id)
    if country_code:
        discover_params['with_origin_country'] = country_code
    
    # Add people filters
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
    
    # For text-based searches, use search endpoint
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
            # Apply additional filters client-side
            filtered_results = []
            for movie in results:
                # Check year range
                release_year = int(movie['release_date'][:4]) if movie.get('release_date') and movie['release_date'] else None
                if release_year:
                    if min_year and release_year < min_year:
                        continue
                    if max_year and release_year > max_year:
                        continue
                
                # Check genre
                if genre_id and genre_id not in movie.get('genre_ids', []):
                    continue
                
                # Check watch provider
                if watch_provider_id:
                    watch_info = get_watch_info(movie['id'])
                    if WATCH_PROVIDERS.get(watch_provider_id, '') not in watch_info:
                        continue
                
                # Check country
                if country_code:
                    details_response = requests.get(f"{TMDB_BASE_URL}/movie/{movie['id']}", params={'api_key': TMDB_API_KEY})
                    if details_response.status_code == 200:
                        details = details_response.json()
                        countries = [c['iso_3166_1'] for c in details.get('production_countries', [])]
                        if country_code not in countries:
                            continue
                
                filtered_results.append(movie)
            results = filtered_results
    else:
        # Use discover endpoint for non-text searches
        response = requests.get(discover_url, params=discover_params)
        if response.status_code == 200:
            results = response.json().get('results', [])
    
    if response.status_code != 200:
        st.error(f"TMDB API error: {response.status_code} - {response.text}")
        return pd.DataFrame()
    
    if not results:
        st.warning("No results found. Try adjusting your search criteria.")
        return pd.DataFrame()
    
    external_movies = []
    conn = get_connection()
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

        # Fetch where to watch with links
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

# ENHANCED: More filters for movie recommendations
def get_recommended_movies(min_rating=3.5, num_recs=5, genre_filter=None, year_filter=None, min_tmdb_rating=None):
    conn = get_connection()
    c = conn.cursor()
    
    # Build query with additional filters
    query = "SELECT name, year, rating, genre FROM movies WHERE rating >= ?"
    params = [min_rating]
    
    if genre_filter:
        query += " AND LOWER(genre) LIKE LOWER(?)"
        params.append(f"%{genre_filter}%")
    
    if year_filter:
        query += " AND year >= ?"
        params.append(year_filter)
    
    c.execute(query, params)
    liked_movies = c.fetchall()
    conn.close()
    
    if not liked_movies:
        return pd.DataFrame()
    
    watched_titles = {row[0].lower() for row in liked_movies}
    all_recommendations = []
    
    for name, year, rating, genre in liked_movies:
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
                            # Apply TMDB rating filter
                            if min_tmdb_rating and rec['vote_average'] < min_tmdb_rating:
                                continue
                            
                            all_recommendations.append({
                                'Title': rec['title'],
                                'Year': rec['release_date'][:4] if rec['release_date'] else 'N/A',
                                'Overview': rec['overview'],
                                'TMDB Rating': rec['vote_average'],
                                'Genres': ', '.join([GENRE_MAP.get(g, 'Unknown') for g in rec.get('genre_ids', [])]),
                                'Based On': name
                            })
    
    unique_recs = {rec['Title']: rec for rec in all_recommendations}
    return pd.DataFrame(list(unique_recs.values())[:15])  # Return more recommendations

# NEW: Functions for adding movies
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
            return results[0]
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

# NEW: Function to edit existing movie entries
def edit_movie_in_database(movie_id, new_data):
    """Edit an existing movie in the database"""
    conn = get_connection()
    c = conn.cursor()
    
    try:
        # Update movie
        c.execute("""
            UPDATE movies SET 
                name = ?, year = ?, genre = ?, rating = ?, mood = ?,
                director = ?, actors = ?, composer = ?, producer = ?, studio = ?, plot = ?, duration = ?
            WHERE id = ?
        """, (
            new_data['name'], new_data['year'], new_data['genre'], new_data['rating'], new_data['mood'],
            new_data['director'], new_data['actors'], new_data['composer'],
            new_data['producer'], new_data['studio'], new_data['plot'], new_data['duration'],
            movie_id
        ))
        
        # Update keywords
        c.execute("DELETE FROM keywords WHERE movie_id = ?", (movie_id,))
        if new_data.get('keywords'):
            keyword_list = [kw.strip() for kw in new_data['keywords'].split(',') if kw.strip()]
            for keyword in keyword_list:
                c.execute("INSERT INTO keywords (movie_id, keyword) VALUES (?, ?)", (movie_id, keyword))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Error updating movie: {e}")
        return False
    finally:
        conn.close()

def edit_movie_in_csv(movie_name, movie_year, new_data):
    """Edit an existing movie in the CSV file"""
    try:
        # Read existing CSV
        df = pd.read_csv(CSV_PATH)
        
        # Find the movie to edit
        mask = (df['Movie Name'] == movie_name) & (df['Year of Release'] == str(movie_year))
        if not mask.any():
            st.error("Movie not found in CSV")
            return False
        
        # Update the row
        df.loc[mask, 'Movie Name'] = new_data['name']
        df.loc[mask, 'Year of Release'] = str(new_data['year'])
        df.loc[mask, 'Genre'] = new_data['genre']
        df.loc[mask, 'My rating'] = str(new_data['rating'])
        df.loc[mask, 'Mood'] = new_data['mood']
        
        # Update keywords (assuming first keyword column)
        if new_data.get('keywords'):
            keyword_list = [kw.strip() for kw in new_data['keywords'].split(',') if kw.strip()]
            for i, keyword in enumerate(keyword_list[:4]):  # Limit to 4 keywords
                col_name = 'Keywords' if i == 0 else ''
                if col_name in df.columns:
                    df.loc[mask, col_name] = keyword
        
        # Write back to CSV
        df.to_csv(CSV_PATH, index=False)
        return True
    except Exception as e:
        st.error(f"Error updating CSV: {e}")
        return False

# Streamlit app
st.markdown('<div class="tab-container">', unsafe_allow_html=True)

# Initialize database if needed
init_database()

# Global region selection for watch providers
st.markdown('<div class="search-container">', unsafe_allow_html=True)
watch_region_name = st.selectbox("🌍 Select Region for Watch Providers", list(COUNTRY_MAP.values()), index=0, key="watch_region_select")
watch_region_code = next((code for code, name in COUNTRY_MAP.items() if name == watch_region_name), 'US')
st.session_state['watch_region'] = watch_region_code
WATCH_PROVIDERS = get_watch_providers(watch_region_code)
st.markdown('</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["🎬 My Collection", "🔍 Search My Movies", "📊 Rating Analysis", "🌐 Discover Movies", "💡 Recommendations", "➕ Add Movie", "✏️ Edit Movies", "📄 CSV Management"])

with tab1:
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.header("🎬 My Movie Collection")
    df = fetch_all_movies()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Collection as CSV", csv, "my_movie_collection.csv", "text/csv")
    else:
        st.info("No movies in your collection yet. Add some movies using the 'Add Movie' tab!")
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.header("🔍 Search My Movies")
    
    col1, col2 = st.columns(2)
    name = col1.text_input("🎬 Movie Name", key="local_name", placeholder="Enter movie title...")
    actor = col2.text_input("👤 Actor/Cast", key="local_actor", placeholder="Enter actor name...")  # FIXED: Added actor field
    
    col1, col2 = st.columns(2)
    min_year = col1.number_input("📅 From Year", value=None, min_value=1900, max_value=2100, key="local_min_year")
    max_year = col2.number_input("📅 To Year", value=None, min_value=1900, max_value=2100, key="local_max_year")
    
    col1, col2 = st.columns(2)
    genre = col1.text_input("🎭 Genre", key="local_genre", placeholder="e.g., Action, Drama...")
    mood = col2.text_input("😊 Mood", key="local_mood", placeholder="e.g., Excited, Relaxed...")
    
    col1, col2 = st.columns(2)
    min_rating = col1.number_input("⭐ Min Rating", value=None, min_value=0.0, max_value=5.0, step=0.5, key="local_min_rating")
    director = col2.text_input("🎬 Director", key="local_director", placeholder="Enter director name...")
    
    keyword = st.text_input("🏷️ Keywords", key="local_keyword", placeholder="Enter keywords...")
    local_country_name = st.selectbox("🌍 Production Country", [''] + list(COUNTRY_MAP.values()), key="local_country_select")
    local_country_code = next((code for code, name in COUNTRY_MAP.items() if name == local_country_name), None)
    
    if st.button("🔍 Search My Movies", type="primary"):
        df = search_movies(name, min_year, max_year, genre, mood, min_rating, director, actor, keyword, local_country_code)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Results", csv, "search_results.csv", "text/csv")
        else:
            st.info("No movies found matching your criteria.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.header("📊 Rating Analysis")
    st.write("Compare your ratings with professional critics")
    df = compare_ratings()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Analysis", csv, "ratings_comparison.csv", "text/csv")
    else:
        st.info("No rating comparisons available. Add more movies with external ratings.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.header("🌐 Discover Movies")
    st.write("Search external movie databases (TMDB/IMDB)")
    
    col1, col2 = st.columns(2)
    ext_query = col1.text_input("🎬 Movie Name or Keyword", placeholder="Enter movie title...")
    ext_plot = col2.text_input("📝 Plot Keywords", placeholder="Enter plot keywords...")
    
    col1, col2 = st.columns(2)
    ext_min_year = col1.number_input("📅 From Year", value=None, min_value=1900, max_value=2100, key="ext_min_year")
    ext_max_year = col2.number_input("📅 To Year", value=None, min_value=1900, max_value=2100, key="ext_max_year")
    
    col1, col2 = st.columns(2)
    ext_genre_name = col1.selectbox("🎭 Genre", [''] + list(GENRE_MAP.values()), key="ext_genre_select")
    ext_country_name = col2.selectbox("🌍 Production Country", [''] + list(COUNTRY_MAP.values()), key="ext_country_select")
    
    col1, col2 = st.columns(2)
    ext_director = col1.text_input("🎬 Director", placeholder="Enter director name...")
    ext_actor = col2.text_input("👤 Actor/Cast", placeholder="Enter actor name...")
    
    col1, col2 = st.columns(2)
    ext_composer = col1.text_input("🎵 Music Composer", placeholder="Enter composer name...")
    ext_writer = col2.text_input("✍️ Writer", placeholder="Enter writer name...")
    
    ext_watch_provider_name = st.selectbox("📺 Where to Watch", [''] + sorted(list(WATCH_PROVIDERS.values())), key="ext_watch_select")
    ext_watch_provider_id = next((id for id, name in WATCH_PROVIDERS.items() if name == ext_watch_provider_name), None)
    ext_genre_id = next((id for id, name in GENRE_MAP.items() if name == ext_genre_name), None)
    ext_country_code = next((code for code, name in COUNTRY_MAP.items() if name == ext_country_name), None)
    
    if st.button("🔍 Search External Movies", type="primary"):
        ext_df = search_external_movies(ext_query, ext_min_year, ext_max_year, ext_genre_id, ext_plot, ext_director, ext_actor, ext_composer, ext_writer, ext_watch_provider_id, ext_country_code)
        if not ext_df.empty:
            st.dataframe(ext_df, use_container_width=True)
            csv = ext_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download External Results", csv, "external_movies.csv", "text/csv")
        else:
            st.info("No results found. Try adjusting your search criteria.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab5:
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.header("💡 Movie Recommendations")
    st.write("Get personalized recommendations based on your highly rated movies")
    
    col1, col2 = st.columns(2)
    rec_min_rating = col1.number_input("⭐ Min Rating for Liked Movies", value=3.5, min_value=0.0, max_value=5.0, step=0.5)
    rec_num = col2.number_input("📊 Number of Recs per Movie", value=5, min_value=1, max_value=10)
    
    col1, col2 = st.columns(2)
    rec_genre_filter = col1.text_input("🎭 Genre Filter", placeholder="e.g., Action, Drama...")
    rec_year_filter = col2.number_input("📅 Min Year Filter", value=None, min_value=1900, max_value=2030)
    
    rec_min_tmdb_rating = st.number_input("⭐ Min TMDB Rating", value=None, min_value=0.0, max_value=10.0, step=0.1, help="Filter recommendations by minimum TMDB rating")
    
    if st.button("🎯 Generate Recommendations", type="primary"):
        rec_df = get_recommended_movies(rec_min_rating, rec_num, rec_genre_filter, rec_year_filter, rec_min_tmdb_rating)
        if not rec_df.empty:
            st.dataframe(rec_df, use_container_width=True)
            csv = rec_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Recommendations", csv, "recommended_movies.csv", "text/csv")
        else:
            st.info("No recommendations found. Try adjusting the filters or add more highly rated movies to your collection.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab6:
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.header("➕ Add New Movie")
    st.write("Add a movie to your database. Just provide the title and year - we'll fill in the rest!")
    
    # Movie search form
    with st.form("add_movie_form"):
        col1, col2 = st.columns(2)
        movie_title = col1.text_input("🎬 Movie Title *", placeholder="e.g., The Godfather")
        movie_year = col2.number_input("📅 Year (optional)", value=None, min_value=1900, max_value=2030, help="Leave empty to search without year filter")
        
        if st.form_submit_button("🔍 Search Movie"):
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
            user_rating = col1.number_input("⭐ Your Rating (0-5)", min_value=0.0, max_value=5.0, step=0.5, value=3.0)
            mood = col2.text_input("😊 Mood when watching", placeholder="e.g., Excited, Relaxed, Bored")
            
            keywords = st.text_input("🏷️ Keywords (comma-separated)", placeholder="e.g., Action, Thriller, Classic")
            
            col1, col2 = st.columns(2)
            add_to_db = col1.checkbox("Add to Database", value=True)
            add_to_csv = col2.checkbox("Add to CSV", value=True)
            
            if st.form_submit_button("➕ Add Movie"):
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
            manual_title = col1.text_input("🎬 Title *")
            manual_year = col2.number_input("📅 Year *", min_value=1900, max_value=2030)
            manual_genre = st.text_input("🎭 Genre")
            manual_rating = st.number_input("⭐ Your Rating (0-5)", min_value=0.0, max_value=5.0, step=0.5, value=3.0)
            manual_mood = st.text_input("😊 Mood")
            manual_keywords = st.text_input("🏷️ Keywords (comma-separated)")
            
            if st.form_submit_button("➕ Add Manual Entry"):
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
    st.markdown('</div>', unsafe_allow_html=True)

with tab7:
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.header("✏️ Edit Existing Movies")
    st.write("Modify existing movie entries in your database and CSV file")
    
    # Get all movies for selection
    all_movies_df = fetch_all_movies()
    
    if not all_movies_df.empty:
        # Movie selection
        movie_options = [f"{row['name']} ({row['year']})" for _, row in all_movies_df.iterrows()]
        selected_movie = st.selectbox("🎬 Select Movie to Edit", movie_options)
        
        if selected_movie:
            # Find the selected movie data
            movie_name, movie_year = selected_movie.rsplit(' (', 1)
            movie_year = int(movie_year.rstrip(')'))
            movie_row = all_movies_df[(all_movies_df['name'] == movie_name) & (all_movies_df['year'] == movie_year)].iloc[0]
            
            st.subheader(f"Editing: {movie_name} ({movie_year})")
            
            # Edit form
            with st.form("edit_movie_form"):
                col1, col2 = st.columns(2)
                new_name = col1.text_input("🎬 Movie Title", value=movie_row['name'])
                new_year = col2.number_input("📅 Year", value=int(movie_row['year']), min_value=1900, max_value=2030)
                
                col1, col2 = st.columns(2)
                new_genre = col1.text_input("🎭 Genre", value=movie_row['genre'] if pd.notna(movie_row['genre']) else '')
                new_rating = col2.number_input("⭐ Your Rating", value=float(movie_row['rating']), min_value=0.0, max_value=5.0, step=0.5)
                
                col1, col2 = st.columns(2)
                new_mood = col1.text_input("😊 Mood", value=movie_row['mood'] if pd.notna(movie_row['mood']) else '')
                new_director = col2.text_input("🎬 Director", value=movie_row['director'] if pd.notna(movie_row['director']) else '')
                
                col1, col2 = st.columns(2)
                new_actors = col1.text_input("👤 Actors", value=movie_row['actors'] if pd.notna(movie_row['actors']) else '')
                new_composer = col2.text_input("🎵 Composer", value=movie_row['composer'] if pd.notna(movie_row['composer']) else '')
                
                new_keywords = st.text_input("🏷️ Keywords (comma-separated)", value=movie_row['keywords'] if pd.notna(movie_row['keywords']) else '')
                
                col1, col2 = st.columns(2)
                update_db = col1.checkbox("Update Database", value=True)
                update_csv = col2.checkbox("Update CSV", value=True)
                
                if st.form_submit_button("💾 Save Changes"):
                    new_data = {
                        'name': new_name,
                        'year': new_year,
                        'genre': new_genre,
                        'rating': new_rating,
                        'mood': new_mood,
                        'director': new_director,
                        'actors': new_actors,
                        'composer': new_composer,
                        'keywords': new_keywords,
                        'producer': '',
                        'studio': '',
                        'plot': '',
                        'duration': None
                    }
                    
                    success_db = True
                    success_csv = True
                    
                    if update_db:
                        success_db = edit_movie_in_database(int(movie_row['id']), new_data)
                    
                    if update_csv:
                        success_csv = edit_movie_in_csv(movie_name, movie_year, new_data)
                    
                    if success_db and success_csv:
                        st.success("Movie updated successfully!")
                        st.rerun()
                    elif success_db or success_csv:
                        st.warning("Movie updated partially. Check the error messages above.")
                    else:
                        st.error("Failed to update movie. Please try again.")
    else:
        st.info("No movies found in your collection. Add some movies first using the 'Add Movie' tab.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab8:
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.header("📄 CSV Management")
    st.write("Manage your CSV file directly - view, add, edit, and sync with database")
    
    # Display current CSV content
    st.subheader("📋 Current CSV Content")
    if os.path.exists(CSV_PATH):
        try:
            csv_df = pd.read_csv(CSV_PATH)
            st.dataframe(csv_df, use_container_width=True)
            
            # CSV operations
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Sync CSV to Database", type="primary"):
                    with st.spinner("Syncing CSV to database..."):
                        try:
                            import subprocess
                            result = subprocess.run(['python', 'sync_csv_to_db.py'], capture_output=True, text=True)
                            if result.returncode == 0:
                                st.success("CSV synced to database successfully!")
                                st.rerun()
                            else:
                                st.error(f"Sync failed: {result.stderr}")
                        except Exception as e:
                            st.error(f"Error syncing: {e}")
            
            with col2:
                csv_download = csv_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CSV", csv_download, "FavMovies.csv", "text/csv")
            
            with col3:
                if st.button("🗑️ Clear CSV", type="secondary"):
                    if st.session_state.get('confirm_clear_csv', False):
                        # Create empty CSV with headers
                        empty_df = pd.DataFrame(columns=['@', 'Movie Name', 'Year of Release', 'Genre', 'My rating', 'producer', 'Mood', 'Keywords', '', '', ''])
                        empty_df.to_csv(CSV_PATH, index=False)
                        st.success("CSV cleared!")
                        st.session_state['confirm_clear_csv'] = False
                        st.rerun()
                    else:
                        st.session_state['confirm_clear_csv'] = True
                        st.warning("Click again to confirm clearing the CSV file")
            
            if st.session_state.get('confirm_clear_csv', False):
                st.error("⚠️ Click 'Clear CSV' again to confirm deletion of all data!")
            
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
    else:
        st.info("CSV file not found. It will be created when you add your first movie.")
    
    # Add new entry to CSV
    st.subheader("➕ Add New Entry to CSV")
    with st.form("csv_add_form"):
        col1, col2 = st.columns(2)
        csv_title = col1.text_input("🎬 Movie Title *")
        csv_year = col2.number_input("📅 Year *", min_value=1900, max_value=2030)
        
        col1, col2 = st.columns(2)
        csv_genre = col1.text_input("🎭 Genre")
        csv_rating = col2.number_input("⭐ Your Rating (0-5)", min_value=0.0, max_value=5.0, step=0.5, value=3.0)
        
        col1, col2 = st.columns(2)
        csv_producer = col1.text_input("🎬 Producer")
        csv_mood = col2.text_input("😊 Mood")
        
        csv_keywords = st.text_input("🏷️ Keywords (comma-separated)", placeholder="e.g., Action, Thriller, Classic")
        
        if st.form_submit_button("➕ Add to CSV"):
            if csv_title and csv_year:
                # Prepare new row data
                keyword_list = [kw.strip() for kw in csv_keywords.split(',') if kw.strip()] if csv_keywords else []
                while len(keyword_list) < 4:
                    keyword_list.append('')
                
                new_row = {
                    '@': '',
                    'Movie Name': csv_title,
                    'Year of Release': str(csv_year),
                    'Genre': csv_genre,
                    'My rating': str(csv_rating),
                    'producer': csv_producer,
                    'Mood': csv_mood,
                    'Keywords': keyword_list[0] if len(keyword_list) > 0 else '',
                    '': keyword_list[1] if len(keyword_list) > 1 else '',
                    '': keyword_list[2] if len(keyword_list) > 2 else '',
                    '': keyword_list[3] if len(keyword_list) > 3 else ''
                }
                
                try:
                    # Read existing CSV or create new one
                    if os.path.exists(CSV_PATH):
                        df = pd.read_csv(CSV_PATH)
                    else:
                        df = pd.DataFrame(columns=['@', 'Movie Name', 'Year of Release', 'Genre', 'My rating', 'producer', 'Mood', 'Keywords', '', '', ''])
                    
                    # Add new row
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    
                    # Write back to CSV
                    df.to_csv(CSV_PATH, index=False)
                    
                    st.success("Entry added to CSV successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding to CSV: {e}")
            else:
                st.warning("Please fill in at least title and year.")
    
    # Edit existing CSV entry
    st.subheader("✏️ Edit CSV Entry")
    if os.path.exists(CSV_PATH):
        try:
            csv_df = pd.read_csv(CSV_PATH)
            if not csv_df.empty:
                # Movie selection for editing
                movie_options = [f"{row['Movie Name']} ({row['Year of Release']})" for _, row in csv_df.iterrows()]
                selected_csv_movie = st.selectbox("🎬 Select Movie to Edit", movie_options, key="csv_edit_select")
                
                if selected_csv_movie:
                    # Find the selected movie data
                    movie_name, movie_year = selected_csv_movie.rsplit(' (', 1)
                    movie_year = movie_year.rstrip(')')
                    movie_row = csv_df[(csv_df['Movie Name'] == movie_name) & (csv_df['Year of Release'] == movie_year)].iloc[0]
                    
                    with st.form("csv_edit_form"):
                        col1, col2 = st.columns(2)
                        edit_title = col1.text_input("🎬 Movie Title", value=movie_row['Movie Name'])
                        edit_year = col2.number_input("📅 Year", value=int(movie_row['Year of Release']), min_value=1900, max_value=2030)
                        
                        col1, col2 = st.columns(2)
                        edit_genre = col1.text_input("🎭 Genre", value=movie_row['Genre'] if pd.notna(movie_row['Genre']) else '')
                        edit_rating = col2.number_input("⭐ Your Rating", value=float(movie_row['My rating']), min_value=0.0, max_value=5.0, step=0.5)
                        
                        col1, col2 = st.columns(2)
                        edit_producer = col1.text_input("🎬 Producer", value=movie_row['producer'] if pd.notna(movie_row['producer']) else '')
                        edit_mood = col2.text_input("😊 Mood", value=movie_row['Mood'] if pd.notna(movie_row['Mood']) else '')
                        
                        edit_keywords = st.text_input("🏷️ Keywords (comma-separated)", value=movie_row['Keywords'] if pd.notna(movie_row['Keywords']) else '')
                        
                        if st.form_submit_button("💾 Update CSV Entry"):
                            try:
                                # Update the row
                                mask = (csv_df['Movie Name'] == movie_name) & (csv_df['Year of Release'] == movie_year)
                                csv_df.loc[mask, 'Movie Name'] = edit_title
                                csv_df.loc[mask, 'Year of Release'] = str(edit_year)
                                csv_df.loc[mask, 'Genre'] = edit_genre
                                csv_df.loc[mask, 'My rating'] = str(edit_rating)
                                csv_df.loc[mask, 'producer'] = edit_producer
                                csv_df.loc[mask, 'Mood'] = edit_mood
                                csv_df.loc[mask, 'Keywords'] = edit_keywords
                                
                                # Write back to CSV
                                csv_df.to_csv(CSV_PATH, index=False)
                                
                                st.success("CSV entry updated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating CSV: {e}")
            else:
                st.info("No entries in CSV to edit.")
        except Exception as e:
            st.error(f"Error reading CSV for editing: {e}")
    else:
        st.info("CSV file not found. Create it first by adding a movie.")
    
    # Upload CSV file
    st.subheader("📤 Upload CSV File")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv", key="csv_upload")
    if uploaded_file is not None:
        try:
            # Read uploaded CSV
            uploaded_df = pd.read_csv(uploaded_file)
            
            # Display preview
            st.write("Preview of uploaded file:")
            st.dataframe(uploaded_df.head(), use_container_width=True)
            
            if st.button("💾 Replace Current CSV", type="primary"):
                # Save uploaded file
                uploaded_df.to_csv(CSV_PATH, index=False)
                st.success("CSV file replaced successfully!")
                st.rerun()
        except Exception as e:
            st.error(f"Error processing uploaded file: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)