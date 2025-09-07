import requests
import sqlite3

# Configuration
TMDB_API_KEY = 'YOUR_TMDB_API_KEY'  # Replace with your actual TMDB API key
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
MIN_RATING = 3.5  # Minimum rating to consider a movie "liked"
NUM_RECOMMENDATIONS = 5  # Number of suggestions per liked movie

def read_watched_movies(db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    watched = {}
    c.execute("SELECT name, year, rating FROM movies")
    for name, year, rating in c.fetchall():
        watched[name.lower()] = {'year': year, 'rating': rating}
    conn.close()
    return watched





def get_liked_movies(watched):
    return {name: info for name, info in watched.items() if info['rating'] >= MIN_RATING}


def search_tmdb_movie(title, year):
    url = f"{TMDB_BASE_URL}/search/movie"
    params = {
        'api_key': TMDB_API_KEY,
        'query': title,
        'year': year
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            return results[0]['id']  # Return the first match's ID
    return None

def get_tmdb_recommendations(movie_id):
    url = f"{TMDB_BASE_URL}/movie/{movie_id}/recommendations"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'en-US',
        'page': 1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('results', [])
    return []

def main():
    db_file = '/Users/invincibleMK/Documents/cinema/movies.db'
    watched = read_watched_movies(db_file)
    liked = get_liked_movies(watched)
    
    if not liked:
        print("No highly rated movies found to base recommendations on.")
        return
    
    print(f"Found {len(liked)} highly rated movies to base recommendations on.\n")
    
    all_recommendations = []
    for title, info in liked.items():
        movie_id = search_tmdb_movie(title, info['year'])
        if not movie_id:
            print(f"Could not find '{title}' ({info['year']}) on TMDB. Skipping.")
            continue
        
        recs = get_tmdb_recommendations(movie_id)
        for rec in recs[:NUM_RECOMMENDATIONS]:
            rec_title = rec['title'].lower()
            if rec_title not in watched:
                all_recommendations.append({
                    'title': rec['title'],
                    'year': rec.get('release_date', '')[:4],
                    'overview': rec['overview'],
                    'based_on': title
                })
    
    # Deduplicate and print top unique recommendations
    unique_recs = {rec['title']: rec for rec in all_recommendations}
    print("Top unique movie recommendations:")
    for rec in list(unique_recs.values())[:10]:  # Limit to top 10 overall
        print(f"- {rec['title']} ({rec['year']}): {rec['overview']} (Based on your liking for '{rec['based_on']}')")

if __name__ == "__main__":
    main()