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
        padding: 3rem 0;
        margin-bottom: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(229, 9, 20, 0.3);
        border: 2px solid rgba(255, 255, 255, 0.1);
    }
    
    .logo-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-bottom: 0;
        padding: 1rem 0;
    }
    
    @keyframes logoGlow {
        0% {
            text-shadow: 4px 4px 8px rgba(0,0,0,0.9), 0 0 25px rgba(229, 9, 20, 0.6);
        }
        100% {
            text-shadow: 4px 4px 8px rgba(0,0,0,0.9), 0 0 35px rgba(229, 9, 20, 0.9);
        }
    }
    
    /* Netflix-style font rendering */
    .netflix-logo {
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        font-smooth: always;
        text-rendering: optimizeLegibility;
    }
    
    .logo {
        max-height: 200px;
        width: auto;
        min-height: 120px;
        object-fit: contain;
        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
        transition: transform 0.3s ease;
    }
    
    .logo:hover {
        transform: scale(1.05);
    }
    
    .netflix-red {
        color: #E50914;
    }
    
    .netflix-dark {
        background-color: #E50914;
        color: #FFFFFF;
    }
    
    /* Main page background - Netflix Red instead of black */
    .main .block-container {
        background: linear-gradient(135deg, #E50914 0%, #B81D13 100%);
        padding: 1rem;
        border-radius: 10px;
    }
    
    .stApp {
        background: linear-gradient(135deg, #E50914 0%, #B81D13 100%);
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
    
    /* Left sidebar styling */
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        border-right: 3px solid #E50914;
        padding: 1rem;
    }
    
    .sidebar .stRadio > div {
        background-color: transparent;
    }
    
    .sidebar .stRadio > div > label {
        color: #FFFFFF;
        font-weight: 500;
    }
    
    .sidebar .stRadio > div > label > div[data-testid="stMarkdownContainer"] {
        color: #FFFFFF;
    }
    
    .sidebar .stSelectbox > div > div {
        background-color: #2d2d2d;
        color: #FFFFFF;
    }
    
    .sidebar .stTextInput > div > div > input {
        background-color: #2d2d2d;
        color: #FFFFFF;
        border: 1px solid #555;
    }
    
    .sidebar .stNumberInput > div > div > input {
        background-color: #2d2d2d;
        color: #FFFFFF;
        border: 1px solid #555;
    }
    
    /* Remove empty space in sidebar */
    .sidebar .stRadio > div > div {
        margin: 0.2rem 0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    
    /* Remove empty bars and improve spacing */
    .stApp > div {
        padding-top: 0;
    }
    
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Make the main header more prominent */
    .main-header {
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 50%, rgba(255,255,255,0.1) 100%);
        animation: shimmer 3s ease-in-out infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    /* Improve sidebar spacing */
    .sidebar .element-container {
        margin-bottom: 0.5rem;
    }
    
    /* Remove default Streamlit spacing */
    .stApp > header {
        display: none;
    }
    
    .stApp > div[data-testid="stToolbar"] {
        display: none;
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
    """Display the NextFlix logo using the image file"""
    try:
        if os.path.exists(LOGO_PATH):
            with open(LOGO_PATH, "rb") as f:
                logo_data = f.read()
                logo_base64 = base64.b64encode(logo_data).decode()
                st.markdown(f"""
                <div class="logo-container">
                    <img src="data:image/png;base64,{logo_base64}" class="logo" alt="NextFlix Logo">
                    <p style="
                        color: #FFFFFF;
                        font-size: 1.3rem;
                        margin: 0.5rem 0 0 0;
                        font-weight: 300;
                        text-shadow: 1px 1px 2px rgba(0,0,0,0.7);
                        letter-spacing: 1px;
                    ">Your Personal Movie Database</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Fallback to text logo if image not found
            st.markdown("""
            <div class="logo-container">
                <h1 class="netflix-logo" style="
                    font-size: 5rem; 
                    font-weight: 900; 
                    color: #E50914;
                    text-shadow: 4px 4px 8px rgba(0,0,0,0.9);
                    margin: 0;
                    padding: 0;
                    letter-spacing: -3px;
                    font-family: 'Helvetica Neue', 'Arial Black', 'Impact', 'Franklin Gothic Heavy', Arial, sans-serif;
                    background: linear-gradient(45deg, #E50914, #FF6B6B, #E50914);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    animation: logoGlow 2s ease-in-out infinite alternate;
                    transform: perspective(500px) rotateX(5deg);
                    text-transform: uppercase;
                ">NEXTFLICK</h1>
                <p style="
                    color: #FFFFFF;
                    font-size: 1.3rem;
                    margin: 0.5rem 0 0 0;
                    font-weight: 300;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.7);
                    letter-spacing: 1px;
                ">Your Personal Movie Database</p>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        # Fallback to text logo if any error occurs
        st.markdown("""
        <div class="logo-container">
            <h1 class="netflix-logo" style="
                font-size: 5rem; 
                font-weight: 900; 
                color: #E50914;
                text-shadow: 4px 4px 8px rgba(0,0,0,0.9);
                margin: 0;
                padding: 0;
                letter-spacing: -3px;
                font-family: 'Helvetica Neue', 'Arial Black', 'Impact', 'Franklin Gothic Heavy', Arial, sans-serif;
                background: linear-gradient(45deg, #E50914, #FF6B6B, #E50914);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                animation: logoGlow 2s ease-in-out infinite alternate;
                transform: perspective(500px) rotateX(5deg);
                text-transform: uppercase;
            ">NEXTFLICK</h1>
            <p style="
                color: #FFFFFF;
                font-size: 1.3rem;
                margin: 0.5rem 0 0 0;
                font-weight: 300;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.7);
                letter-spacing: 1px;
            ">Your Personal Movie Database</p>
        </div>
        """, unsafe_allow_html=True)

# Load CSS and display logo
load_css()

# Initialize sidebar state
if 'sidebar_visible' not in st.session_state:
    st.session_state.sidebar_visible = True

# Add sidebar toggle button with better styling
st.markdown("""
<div style="
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    border-radius: 10px;
    padding: 0.5rem;
    margin-bottom: 1rem;
    border: 1px solid #333;
    text-align: center;
">
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("📱 Toggle Sidebar", help="Show/Hide the navigation sidebar", type="primary"):
        st.session_state.sidebar_visible = not st.session_state.sidebar_visible
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

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
    
    # Try multiple search strategies for better partial matching
    search_terms = [name]
    
    # Add individual words for partial matching
    words = name.split()
    if len(words) > 1:
        # Add first name only
        search_terms.append(words[0])
        # Add last name only
        search_terms.append(words[-1])
        # Add first two words if more than 2 words
        if len(words) > 2:
            search_terms.append(' '.join(words[:2]))
    
    search_url = f"{TMDB_BASE_URL}/search/person"
    
    for term in search_terms:
        params = {
            'api_key': TMDB_API_KEY,
            'query': term
        }
        response = requests.get(search_url, params=params)
        if response.status_code == 200:
            results = response.json().get('results', [])
            if results:
                # Try to find the best match using fuzzy matching
                name_lower = name.lower()
                best_match = None
                best_score = 0
                
                for person in results[:10]:  # Check top 10 results
                    person_name = person.get('name', '').lower()
                    # Simple fuzzy matching - check if search term appears in person name
                    if name_lower in person_name or any(word in person_name for word in name_lower.split() if len(word) > 2):
                        # Calculate a simple score based on name similarity
                        score = len(set(name_lower.split()) & set(person_name.split()))
                        if score > best_score:
                            best_score = score
                            best_match = person
                
                if best_match:
                    return best_match['id']
                else:
                    # Fallback to first result if no good match found
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
    
    # For text-based searches, use search endpoint with improved partial matching
    if query or plot_keywords:
        search_url = f"{TMDB_BASE_URL}/search/movie"
        # Create comprehensive search terms for partial matching
        search_terms = []
        
        # Add original terms
        if query:
            search_terms.append(query)
        if plot_keywords:
            search_terms.append(plot_keywords)
        
        # Add individual words for partial matching
        all_text = f"{query or ''} {plot_keywords or ''}".strip()
        if all_text:
            words = all_text.split()
            # Add each word individually for partial matching
            for word in words:
                if len(word) > 1:  # Include words longer than 1 character for better partial matching
                    search_terms.append(word)
            
            # Add partial word combinations (for cases like "Father" finding "Father of the Bride")
            for i in range(len(words)):
                for j in range(i+1, min(i+4, len(words)+1)):  # 2-4 word combinations
                    partial_phrase = ' '.join(words[i:j])
                    if len(partial_phrase) > 2:
                        search_terms.append(partial_phrase)
            
            # Add partial word matches (for cases like "Spiel" finding "Spielberg")
            for word in words:
                if len(word) > 3:
                    # Add first 3-4 characters for partial matching
                    for i in range(3, min(len(word), 5)):
                        partial_word = word[:i]
                        search_terms.append(partial_word)
        
        all_results = []
        # Search for each term separately to get better partial matches
        for term in search_terms:
            search_params = {
                'api_key': TMDB_API_KEY,
                'query': term,
                'page': 1
            }
            response = requests.get(search_url, params=search_params)
            if response.status_code == 200:
                term_results = response.json().get('results', [])
                all_results.extend(term_results)
        
        # Remove duplicates and apply client-side partial matching
        seen_ids = set()
        results = []
        search_text_lower = all_text.lower()
        
        for movie in all_results:
            if movie['id'] not in seen_ids:
                # Check if the search terms appear in title or overview (case-insensitive)
                title_lower = movie.get('title', '').lower()
                overview_lower = movie.get('overview', '').lower()
                
                # Check if any search term appears in title or overview
                matches = False
                for word in search_text_lower.split():
                    if len(word) > 1:  # Check words longer than 1 character
                        if word in title_lower or word in overview_lower:
                            matches = True
                            break
                
                # Also check if the full search text appears as a substring
                if not matches and len(search_text_lower) > 2:
                    if search_text_lower in title_lower or search_text_lower in overview_lower:
                        matches = True
                
                # Check for partial word matches (e.g., "Spiel" matches "Spielberg")
                if not matches:
                    for word in search_text_lower.split():
                        if len(word) > 3:
                            # Check if any word in title/overview starts with our search word
                            for title_word in title_lower.split():
                                if title_word.startswith(word):
                                    matches = True
                                    break
                            if matches:
                                break
                
                # Include the movie if it matches or if we don't have specific search terms
                if matches or not search_text_lower.strip():
                    seen_ids.add(movie['id'])
                    results.append(movie)
        
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
            
            # Check role-specific filters (director, actor, composer, writer)
            if director or actor or composer or writer:
                credits_response = requests.get(f"{TMDB_BASE_URL}/movie/{movie['id']}/credits", params={'api_key': TMDB_API_KEY})
                if credits_response.status_code == 200:
                    credits = credits_response.json()
                    
                    # Check director
                    if director:
                        dir_id = get_person_id(director, 'director')
                        if dir_id:
                            directors = [crew['id'] for crew in credits.get('crew', []) if crew.get('job') == 'Director']
                            if dir_id not in directors:
                                continue
                    
                    # Check actor
                    if actor:
                        act_id = get_person_id(actor, 'actor')
                        if act_id:
                            actors = [cast['id'] for cast in credits.get('cast', [])]
                            if act_id not in actors:
                                continue
                    
                    # Check composer
                    if composer:
                        comp_id = get_person_id(composer, 'composer')
                        if comp_id:
                            composers = [crew['id'] for crew in credits.get('crew', []) if crew.get('job') in ['Original Music Composer', 'Music', 'Composer']]
                            if comp_id not in composers:
                                continue
                    
                    # Check writer
                    if writer:
                        writ_id = get_person_id(writer, 'writer')
                        if writ_id:
                            writers = [crew['id'] for crew in credits.get('crew', []) if crew.get('job') in ['Writer', 'Screenplay', 'Story', 'Novel']]
                            if writ_id not in writers:
                                continue
                else:
                    # If we can't fetch credits, skip this movie for role-based searches
                    if director or actor or composer or writer:
                        continue
            
            filtered_results.append(movie)
        results = filtered_results
    else:
        # Use discover endpoint for non-text searches
        response = requests.get(discover_url, params=discover_params)
        if response.status_code == 200:
            results = response.json().get('results', [])
            
            # Apply role-specific filtering for discover endpoint results
            if director or actor or composer or writer:
                filtered_results = []
                for movie in results:
                    credits_response = requests.get(f"{TMDB_BASE_URL}/movie/{movie['id']}/credits", params={'api_key': TMDB_API_KEY})
                    if credits_response.status_code == 200:
                        credits = credits_response.json()
                        
                        # Check director
                        if director:
                            dir_id = get_person_id(director, 'director')
                            if dir_id:
                                directors = [crew['id'] for crew in credits.get('crew', []) if crew.get('job') == 'Director']
                                if dir_id not in directors:
                                    continue
                        
                        # Check actor
                        if actor:
                            act_id = get_person_id(actor, 'actor')
                            if act_id:
                                actors = [cast['id'] for cast in credits.get('cast', [])]
                                if act_id not in actors:
                                    continue
                        
                        # Check composer
                        if composer:
                            comp_id = get_person_id(composer, 'composer')
                            if comp_id:
                                composers = [crew['id'] for crew in credits.get('crew', []) if crew.get('job') in ['Original Music Composer', 'Music', 'Composer']]
                                if comp_id not in composers:
                                    continue
                        
                        # Check writer
                        if writer:
                            writ_id = get_person_id(writer, 'writer')
                            if writ_id:
                                writers = [crew['id'] for crew in credits.get('crew', []) if crew.get('job') in ['Writer', 'Screenplay', 'Story', 'Novel']]
                                if writ_id not in writers:
                                    continue
                        
                        filtered_results.append(movie)
                results = filtered_results
    
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
            imdb_id = omdb_data.get('imdbID', '')
            rt_rating = next((r['Value'] for r in omdb_data.get('Ratings', []) if r['Source'] == 'Rotten Tomatoes'), None)
            metacritic_val = next((r['Value'] for r in omdb_data.get('Ratings', []) if r['Source'] == 'Metacritic'), 'N/A')
            metacritic = int(metacritic_val.replace('/100', '')) if metacritic_val != 'N/A' and metacritic_val is not None else None
        else:
            imdb_rating = None
            imdb_id = ''
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
            'IMDb ID': imdb_id,
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
                if base_link:
                    providers.append(f'<a href="{base_link}" target="_blank" style="color: #E50914; text-decoration: none;">{name}</a>')
                else:
                    providers.append(name)
            return ' | '.join(providers)
        return 'Not available in selected region'
    return 'N/A'

# ENHANCED: More filters for movie recommendations
def get_tmdb_similar_movies(movie_id, num_recs=5):
    """Get similar movies from TMDB API"""
    similar_url = f"{TMDB_BASE_URL}/movie/{movie_id}/similar"
    params = {
        'api_key': TMDB_API_KEY,
        'page': 1
    }
    response = requests.get(similar_url, params=params)
    if response.status_code == 200:
        results = response.json().get('results', [])[:num_recs]
        return results
    return []

def get_tmdb_recommendations(movie_id, num_recs=5):
    """Get recommendations from TMDB API"""
    rec_url = f"{TMDB_BASE_URL}/movie/{movie_id}/recommendations"
    params = {
        'api_key': TMDB_API_KEY,
        'page': 1
    }
    response = requests.get(rec_url, params=params)
    if response.status_code == 200:
        results = response.json().get('results', [])[:num_recs]
        return results
    return []

def get_content_based_recommendations(liked_movies, num_recs=10):
    """Get content-based recommendations based on genre, director, cast similarity"""
    all_recommendations = []
    
    for name, year, rating, genre in liked_movies:
        # Search for the movie to get its details
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
                
                # Get movie details for content-based filtering
                details_url = f"{TMDB_BASE_URL}/movie/{movie_id}"
                details_response = requests.get(details_url, params={'api_key': TMDB_API_KEY})
                if details_response.status_code == 200:
                    movie_details = details_response.json()
                    
                    # Search for movies with similar genres
                    if movie_details.get('genres'):
                        genre_ids = [g['id'] for g in movie_details['genres']]
                        discover_url = f"{TMDB_BASE_URL}/discover/movie"
                        discover_params = {
                            'api_key': TMDB_API_KEY,
                            'with_genres': ','.join(map(str, genre_ids)),
                            'sort_by': 'popularity.desc',
                            'page': 1
                        }
                        discover_response = requests.get(discover_url, params=discover_params)
                        if discover_response.status_code == 200:
                            similar_movies = discover_response.json().get('results', [])[:num_recs]
                            for movie in similar_movies:
                                all_recommendations.append({
                                    'Title': movie['title'],
                                    'Year': movie['release_date'][:4] if movie['release_date'] else 'N/A',
                                    'Overview': movie['overview'],
                                    'TMDB Rating': movie['vote_average'],
                                    'Genres': ', '.join([GENRE_MAP.get(g, 'Unknown') for g in movie.get('genre_ids', [])]),
                                    'Based On': name,
                                    'Method': 'Content-Based (Genre)'
                                })
    
    return all_recommendations

def get_collaborative_recommendations(liked_movies, num_recs=10):
    """Get collaborative filtering recommendations based on popular movies in similar genres"""
    all_recommendations = []
    
    # Get popular movies in genres that user likes
    liked_genres = set()
    for name, year, rating, genre in liked_movies:
        if genre:
            liked_genres.update([g.strip() for g in genre.split(',')])
    
    for genre in liked_genres:
        # Map genre name to TMDB genre ID
        genre_id = None
        for gid, gname in GENRE_MAP.items():
            if gname.lower() == genre.lower():
                genre_id = gid
                break
        
        if genre_id:
            # Get popular movies in this genre
            discover_url = f"{TMDB_BASE_URL}/discover/movie"
            discover_params = {
                'api_key': TMDB_API_KEY,
                'with_genres': str(genre_id),
                'sort_by': 'popularity.desc',
                'vote_count.gte': 100,  # Only popular movies
                'page': 1
            }
            discover_response = requests.get(discover_url, params=discover_params)
            if discover_response.status_code == 200:
                popular_movies = discover_response.json().get('results', [])[:num_recs//len(liked_genres)]
                for movie in popular_movies:
                    all_recommendations.append({
                        'Title': movie['title'],
                        'Year': movie['release_date'][:4] if movie['release_date'] else 'N/A',
                        'Overview': movie['overview'],
                        'TMDB Rating': movie['vote_average'],
                        'Genres': ', '.join([GENRE_MAP.get(g, 'Unknown') for g in movie.get('genre_ids', [])]),
                        'Based On': f'Popular in {genre}',
                        'Method': 'Collaborative (Popular)'
                    })
    
    return all_recommendations

def get_enhanced_recommendations(min_rating=3.5, num_recs=5, genre_filter=None, year_filter=None, min_tmdb_rating=None, recommendation_methods=None):
    """Enhanced recommendation system combining multiple approaches like Likewise"""
    if recommendation_methods is None:
        recommendation_methods = ['tmdb_similar', 'tmdb_recommendations', 'content_based', 'collaborative']
    
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
        # Search for the movie to get its TMDB ID
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
                
                # Get recommendations using different methods
                if 'tmdb_similar' in recommendation_methods:
                    similar_movies = get_tmdb_similar_movies(movie_id, num_recs)
                    for movie in similar_movies:
                        rec_title = movie['title'].lower()
                        if rec_title not in watched_titles:
                            if min_tmdb_rating and movie['vote_average'] < min_tmdb_rating:
                                continue
                            all_recommendations.append({
                                'Title': movie['title'],
                                'Year': movie['release_date'][:4] if movie['release_date'] else 'N/A',
                                'Overview': movie['overview'],
                                'TMDB Rating': movie['vote_average'],
                                'Genres': ', '.join([GENRE_MAP.get(g, 'Unknown') for g in movie.get('genre_ids', [])]),
                                'Based On': name,
                                'Method': 'TMDB Similar'
                            })
                
                if 'tmdb_recommendations' in recommendation_methods:
                    rec_movies = get_tmdb_recommendations(movie_id, num_recs)
                    for movie in rec_movies:
                        rec_title = movie['title'].lower()
                        if rec_title not in watched_titles:
                            if min_tmdb_rating and movie['vote_average'] < min_tmdb_rating:
                                continue
                            all_recommendations.append({
                                'Title': movie['title'],
                                'Year': movie['release_date'][:4] if movie['release_date'] else 'N/A',
                                'Overview': movie['overview'],
                                'TMDB Rating': movie['vote_average'],
                                'Genres': ', '.join([GENRE_MAP.get(g, 'Unknown') for g in movie.get('genre_ids', [])]),
                                'Based On': name,
                                'Method': 'TMDB Recommendations'
                            })
    
    # Add content-based and collaborative recommendations
    if 'content_based' in recommendation_methods:
        content_recs = get_content_based_recommendations(liked_movies, num_recs)
        all_recommendations.extend(content_recs)
    
    if 'collaborative' in recommendation_methods:
        collab_recs = get_collaborative_recommendations(liked_movies, num_recs)
        all_recommendations.extend(collab_recs)
    
    # Remove duplicates and filter out watched movies
    unique_recs = {}
    for rec in all_recommendations:
        rec_title = rec['Title'].lower()
        if rec_title not in watched_titles and rec_title not in unique_recs:
            unique_recs[rec_title] = rec
    
    return pd.DataFrame(list(unique_recs.values())[:20])  # Return more diverse recommendations

def get_recommended_movies(min_rating=3.5, num_recs=5, genre_filter=None, year_filter=None, min_tmdb_rating=None):
    """Original recommendation function - now uses enhanced system"""
    return get_enhanced_recommendations(min_rating, num_recs, genre_filter, year_filter, min_tmdb_rating)
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
# Initialize database if needed
init_database()

# Sidebar for navigation - always show sidebar but conditionally hide with CSS
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1rem;">
        <h2 style="
            color: #E50914; 
            margin: 0; 
            font-size: 1.8rem; 
            font-weight: 900;
            font-family: 'Helvetica Neue', 'Arial Black', 'Impact', Arial, sans-serif;
            letter-spacing: -1px;
            text-transform: uppercase;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        ">🎬 NEXTFLICK</h2>
        <p style="color: #FFFFFF; margin: 0.2rem 0; font-size: 0.9rem;">Movie Database</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation menu
    page = st.radio(
        "Navigate to:",
        ["🎬 My Collection", "🔍 Search My Movies", "📊 Rating Analysis", "🌐 Discover Movies", "💡 Recommendations", "➕ Add Movie", "✏️ Edit Movies", "📄 CSV Management"],
        key="navigation"
    )
    
    st.markdown("---")
    
    # Global region selection for watch providers
    st.markdown("**🌍 Watch Region:**")
    watch_region_name = st.selectbox("Watch Region", list(COUNTRY_MAP.values()), index=0, key="watch_region_select", label_visibility="collapsed")
    watch_region_code = next((code for code, name in COUNTRY_MAP.items() if name == watch_region_name), 'US')
    st.session_state['watch_region'] = watch_region_code
    WATCH_PROVIDERS = get_watch_providers(watch_region_code)

# Add CSS to hide sidebar when needed
if not st.session_state.sidebar_visible:
    st.markdown("""
    <style>
    .sidebar {
        display: none !important;
    }
    .main {
        margin-left: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Show navigation in main area when sidebar is hidden
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #333;
    ">
        <h3 style="
            color: #E50914; 
            margin: 0 0 1rem 0; 
            font-size: 1.5rem; 
            font-weight: 900;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        ">🎬 NEXTFLICK - Movie Database</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation menu in main area
    page = st.radio(
        "Navigate to:",
        ["🎬 My Collection", "🔍 Search My Movies", "📊 Rating Analysis", "🌐 Discover Movies", "💡 Recommendations", "➕ Add Movie", "✏️ Edit Movies", "📄 CSV Management"],
        key="navigation_main",
        horizontal=True
    )
    
    # Global region selection for watch providers
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("**🌍 Watch Region:**")
    with col2:
        watch_region_name = st.selectbox("Watch Region", list(COUNTRY_MAP.values()), index=0, key="watch_region_select_main", label_visibility="collapsed")
    watch_region_code = next((code for code, name in COUNTRY_MAP.items() if name == watch_region_name), 'US')
    st.session_state['watch_region'] = watch_region_code
    WATCH_PROVIDERS = get_watch_providers(watch_region_code)
    
    st.markdown("---")

# Main content area
if page == "🎬 My Collection":
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

elif page == "🔍 Search My Movies":
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

elif page == "📊 Rating Analysis":
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

elif page == "🌐 Discover Movies":
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
        with st.spinner("🔍 Searching external movie databases..."):
            ext_df = search_external_movies(ext_query, ext_min_year, ext_max_year, ext_genre_id, ext_plot, ext_director, ext_actor, ext_composer, ext_writer, ext_watch_provider_id, ext_country_code)
        
        if not ext_df.empty:
            st.success(f"✅ Found {len(ext_df)} movies!")
            
            # Display results with proper hyperlinks
            for idx, row in ext_df.iterrows():
                with st.expander(f"🎬 {row['Title']} ({row['Year']}) - ⭐ {row['TMDB Rating']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**📅 Year:** {row['Year']}")
                        st.write(f"**🎭 Genres:** {row['Genres']}")
                        st.write(f"**🎬 Director:** {row['Director']}")
                        st.write(f"**👤 Cast:** {row['Cast']}")
                        st.write(f"**🎵 Composer:** {row['Composer']}")
                        st.write(f"**✍️ Writer:** {row['Writer']}")
                        st.write(f"**🎬 Producer:** {row['Producer']}")
                        st.write(f"**🏢 Studio:** {row['Studio']}")
                    
                    with col2:
                        st.write(f"**💰 Budget:** {row['Budget']}")
                        st.write(f"**📈 Box Office:** {row['Box Office']}")
                        st.write(f"**⏱️ Duration:** {row['Duration']}")
                        st.write(f"**⭐ My Rating:** {row['My Rating']}")
                        st.write(f"**⭐ TMDB Rating:** {row['TMDB Rating']}")
                        st.write(f"**⭐ IMDb Rating:** {row['IMDb Rating']}")
                        st.write(f"**🍅 RT Rating:** {row['RT Rating']}")
                        st.write(f"**📊 Metacritic:** {row['Metacritic']}")
                    
                    st.write(f"**📝 Overview:** {row['Overview']}")
                    
                    # Hyperlinks
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if row['TMDB Link'] != 'N/A':
                            st.markdown(f"[🔗 View on TMDB]({row['TMDB Link']})")
                    with col2:
                        if row['Where to Watch'] != 'N/A' and row['Where to Watch'] != 'Not available in selected region':
                            st.markdown(f"**📺 Where to Watch:** {row['Where to Watch']}", unsafe_allow_html=True)
                        else:
                            st.write(f"**📺 Where to Watch:** {row['Where to Watch']}")
                    with col3:
                        if row.get('IMDb ID') and row['IMDb ID'] != '':
                            imdb_url = f"https://www.imdb.com/title/{row['IMDb ID']}"
                            st.markdown(f"[🔗 View on IMDb]({imdb_url})")
            
            csv = ext_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download External Results", csv, "external_movies.csv", "text/csv")
        else:
            st.info("No results found. Try adjusting your search criteria.")
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "💡 Recommendations":
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.header("💡 Enhanced Movie Recommendations")
    st.write("Get personalized recommendations using multiple algorithms like Likewise, TMDB, and collaborative filtering")
    
    # Recommendation method selection
    st.subheader("🎯 Recommendation Methods")
    col1, col2 = st.columns(2)
    
    with col1:
        use_tmdb_similar = st.checkbox("🔗 TMDB Similar Movies", value=True, help="Movies similar to your favorites")
        use_tmdb_recommendations = st.checkbox("⭐ TMDB Recommendations", value=True, help="TMDB's algorithm recommendations")
    
    with col2:
        use_content_based = st.checkbox("🎭 Content-Based Filtering", value=True, help="Based on genre, director, cast similarity")
        use_collaborative = st.checkbox("👥 Collaborative Filtering", value=True, help="Popular movies in your favorite genres")
    
    # Build recommendation methods list
    recommendation_methods = []
    if use_tmdb_similar:
        recommendation_methods.append('tmdb_similar')
    if use_tmdb_recommendations:
        recommendation_methods.append('tmdb_recommendations')
    if use_content_based:
        recommendation_methods.append('content_based')
    if use_collaborative:
        recommendation_methods.append('collaborative')
    
    st.markdown("---")
    
    # Filter options
    col1, col2 = st.columns(2)
    rec_min_rating = col1.number_input("⭐ Min Rating for Liked Movies", value=3.5, min_value=0.0, max_value=5.0, step=0.5)
    rec_num = col2.number_input("�� Number of Recs per Method", value=5, min_value=1, max_value=10)
    
    col1, col2 = st.columns(2)
    rec_genre_filter = col1.text_input("🎭 Genre Filter", placeholder="e.g., Action, Drama...")
    rec_year_filter = col2.number_input("📅 Min Year Filter", value=None, min_value=1900, max_value=2030)
    
    rec_min_tmdb_rating = st.number_input("⭐ Min TMDB Rating", value=None, min_value=0.0, max_value=10.0, step=0.1, help="Filter recommendations by minimum TMDB rating")
    
    if st.button("🎯 Generate Enhanced Recommendations", type="primary"):
        if not recommendation_methods:
            st.warning("⚠️ Please select at least one recommendation method.")
        else:
            with st.spinner("🎯 Analyzing your preferences with multiple algorithms..."):
                rec_df = get_enhanced_recommendations(
                    rec_min_rating, rec_num, rec_genre_filter, rec_year_filter, 
                    rec_min_tmdb_rating, recommendation_methods
                )
            
            if not rec_df.empty:
                st.success(f"✅ Generated {len(rec_df)} personalized recommendations using {len(recommendation_methods)} methods!")
                
                # Show method breakdown (Algorithm transparency)
                if 'Method' in rec_df.columns:
                    method_counts = rec_df['Method'].value_counts()
                    st.write("**📊 Recommendation Methods Used:**")
                    for method, count in method_counts.items():
                        st.write(f"• {method}: {count} movies")
                
                st.dataframe(rec_df, use_container_width=True)
                csv = rec_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Enhanced Recommendations", csv, "enhanced_recommendations.csv", "text/csv")
            else:
                st.info("ℹ️ No recommendations found. Try adjusting the filters or add more highly rated movies to your collection.")
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "➕ Add Movie":
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

elif page == "✏️ Edit Movies":
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

elif page == "📄 CSV Management":
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
