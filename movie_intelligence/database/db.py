import sqlite3
from sqlite3 import Error
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "app_data.db"

def initialize_database(db_filename):
    """
    Establishes a connection to a SQLite database.
    """

    connection = None


    try:
        connection = sqlite3.connect(db_filename)
        print(f"Successfully Connected to SQLite database: {db_filename}")
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None 



def create_movies_table(connection):

    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            movie_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            release_year INTEGER,
            director TEXT,
            description TEXT,
            runtime INTEGER,
            tmdb_id INTEGER)
        ''')

    connection.commit()




def create_viewing_history_table(connection):

    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS viewing_history (
            review_id INTEGER PRIMARY KEY,
            movie_id INTEGER NOT NULL,
            user_id INTEGER,
            rating REAL CHECK (rating BETWEEN 1 AND 10),
            review TEXT,
            date_watched TEXT,
            FOREIGN KEY (movie_id) REFERENCES movies(movie_id))
        ''')

    connection.commit()




def inspect_table(connection, table_name):

    if table_name not in ("movies", "viewing_history"):
        raise ValueError("Invalid table name")

    cursor = connection.cursor()

    cursor.execute(f"PRAGMA table_info({table_name});")

    columns = cursor.fetchall()

    for column in columns:
        print(f"Column Position: {column[0]}")
        print(f"Column Name: {column[1]}")
        print(f"Data Type: {column[2]}")
        print(f"Not Null Indicator: {column[3]}")
        print(f"Default Value: {column[4]}")
        print(f"Primary Key Position: {column[5]}")
        print("-" * 30)


def insert_movie(connection, title, release_year, director, description, runtime, tmdb_id):

    cursor = connection.cursor()

    insert_query = '''
        INSERT INTO movies (title, release_year, director, description, runtime, tmdb_id)
        VALUES (?, ?, ?, ?, ?, ?);
        '''

    movie_insert = (title, release_year, director, description, runtime, tmdb_id)

    cursor.execute(insert_query, movie_insert)

    connection.commit()

    return cursor.lastrowid

def get_movie(connection, movie_id):

    cursor = connection.cursor()

    get_request = '''
        SELECT * FROM movies
        WHERE movie_id = ?;
        '''

    cursor.execute(get_request, (movie_id,))

    movie = cursor.fetchone()

    return movie

def get_movie_by_tmdb_id(connection, tmdb_id):
    cursor = connection.cursor()

    get_request = '''
        SELECT * FROM movies
        WHERE tmdb_id = ?;
        '''

    cursor.execute(get_request, (tmdb_id,))

    movie = cursor.fetchone()

    return movie

def add_column(connection, table_name, column_name, data_type):
    cursor = connection.cursor()

    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    print(columns)

    

    column_exists = any(column[1] == column_name for column in columns)
    if column_exists == False:
        add_column_request = f'''
            ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type};'''

        cursor.execute(add_column_request)

        connection.commit()
    else:
        print("Column already exists")
      
def create_unique_tmdb_index(connection):
    cursor = connection.cursor()

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_movies_tmdb_id ON movies(tmdb_id);")

    connection.commit()

def insert_review(connection, movie_id, user_id, rating, review, date_watched):
    cursor = connection.cursor()

    movie_review_request = '''
        INSERT INTO viewing_history (movie_id, user_id, rating, review, date_watched)
        VALUES (?, ?, ?, ?, ?);
        '''
    movie_review_data = (movie_id, user_id, rating, review, date_watched)

    cursor.execute(movie_review_request, movie_review_data)



    connection.commit()

    return cursor.lastrowid

def get_reviews_by_movie_id(connection, movie_id):
    cursor = connection.cursor()

    get_review = '''
        SELECT * FROM viewing_history
        WHERE movie_id = ?;
        '''

    cursor.execute(get_review, (movie_id,))

    reviews = cursor.fetchall()
    return reviews

def get_watched_movie_ids():
    """
    Return TMDB IDs of movies already in viewing history.
    """

    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT m.tmdb_id
            FROM movies AS m
            JOIN viewing_history as h
                ON m.movie_id = h.movie_id
            WHERE m.tmdb_id IS NOT NULL
        """)

        return {row[0] for row in cursor.fetchall()}

    finally:
        conn.close()



if __name__ == "__main__":
    conn = initialize_database(DB_PATH)

    print("Database location:", Path(DB_PATH).resolve())

    if conn:
        try:
            create_movies_table(conn)
            create_viewing_history_table(conn)

            table_name = "movies"
            column_name = "tmdb_id"
            data_type = "INTEGER"
            add_column(conn, table_name, column_name, data_type)

            create_unique_tmdb_index(conn)

            inspect_table(conn, "movies")
            inspect_table(conn, "viewing_history")


            movie = get_movie(conn, 1)
            print(f"Retrieved movie: {movie}")

            #review_id = insert_review(conn, 2, 1, 9.0, "Maybe the best animated movie ever other than Kung Fu Panda 2 and Wall-E. Amazing animation and cry its so good story.", "2003-05-16")
            #print(f"Inserted Review ID: {review_id}")

            reviews = get_reviews_by_movie_id(conn, 2)
            print(reviews)

            


        finally:
            conn.close()

    

