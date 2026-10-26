from movie_intelligence.services.movie_metadata import (search_movie, get_movie_details, extract_movie_metadata)
from movie_intelligence.database.db import (initialize_database, get_movie_by_tmdb_id, insert_movie, insert_review, DB_PATH)



def save_movie(title):
    
    data = search_movie(title)
    movies = data["results"]

    if movies:
        movie = movies[0]
        movie_id = movie["id"]

        movie_details = get_movie_details(movie_id)
        movie_metadata = extract_movie_metadata(movie_details)
        tmdb_id = movie_details["id"]
        conn = initialize_database(DB_PATH)
        if conn is None: 
            print("Database connection failed")
            return None
        try:
            existing_movie = get_movie_by_tmdb_id(conn, tmdb_id)
            if existing_movie:
                sqlite_id = existing_movie[0]
                return sqlite_id
            else:
                title = movie_metadata["title"]    
                runtime = movie_metadata["runtime"]
                description = movie_metadata["description"]
                tmdb_id = movie_metadata["tmdb_id"]
                release_year = movie_metadata["release_year"]
                director = movie_metadata["director"]

                sqlite_id = insert_movie(conn, title, release_year, director, description, runtime, tmdb_id)
                return sqlite_id
        finally:
            conn.close()
    else:
        print("No movie found on TMDB")
        return None
                

def log_movie_viewing(title, user_id, rating, review, date_watched):
    movie_id = save_movie(title)

    if movie_id is None:
        print("Movie could not be found or saved.")
        return None

    conn = initialize_database(DB_PATH)

    if conn is None:
        print("Database Connection Failed")
        return None

    try:
        review_id = insert_review(conn, movie_id, user_id, rating, review, date_watched)
        print(f"Review successfully saved! Review ID: {review_id}")
        return review_id
    finally:
        conn.close()


