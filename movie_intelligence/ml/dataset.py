from movie_intelligence.database.db import initialize_database, DB_PATH


def load_training_data():
    '''
    Function that:
    1. Connects to SQLite
    2. Executes SQL query to join movies and viewing_history using movie_id
    3. Retrieve each movie title, description and average rating
    4. Exclude movies without ratings or descriptions
    5. Return results 
    '''

    conn = initialize_database(DB_PATH)
    if conn is None:
        print("Database connection failed.")
        return None
    try:
        cursor = conn.cursor()
        query = ('''
            SELECT t1.title, t1.description, AVG(t2.rating) AS average_rating, t1.tmdb_id FROM movies as t1 INNER JOIN viewing_history as t2 ON t1.movie_id = t2.movie_id
            WHERE t2.rating IS NOT NULL AND t1.description IS NOT NULL AND TRIM(t1.description) != ''
            GROUP BY t1.movie_id, t1.title, t1.description, t1.tmdb_id;
            ''')
        cursor.execute(query)

        results = cursor.fetchall()
        return results
    finally:
        conn.close()

if __name__ == "__main__":
    data = load_training_data()

    if data is not None:
        for movie in data:
            print(movie)

        print(f"Total training records: {len(data)}")