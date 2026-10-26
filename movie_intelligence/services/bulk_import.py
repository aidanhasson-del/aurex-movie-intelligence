import csv
import sqlite3
from pathlib import Path
from datetime import date

TMDB_OVERRIDES = {
    ("Sing", 2016): 335797,
    ("Ex Machina", 2015): 264660,
    ("AVP: Alien vs. Predator", 2004): 395,
    ("Dune: Part Two", 2024): 693134,
    ("Star Wars: Episode III - Revenge of the Sith", 2005): 1895,
    ("A Silent Voice", 2016): 378064,
    ("Monsters vs. Aliens", 2009): 15512,
    ("Pixels", 2015): 257344,
}


from movie_intelligence.database.db import (
    initialize_database,
    create_movies_table,
    create_viewing_history_table,
    create_unique_tmdb_index,
    get_movie_by_tmdb_id,
    insert_movie,
    insert_review,
    DB_PATH,
)

from movie_intelligence.services.movie_metadata import (
    search_movie,
    get_movie_details,
    extract_movie_metadata,
)


def import_movie_ratings(csv_path, user_id=1):
    """
    Import movie ratings from a CSV file into AUREX Movie Intelligence.

    Expected columns:
        title, release_year, rating, review, date_watched

    Movies are matched against TMDB, then saved to SQLite.
    Existing movie records are reused.

    Exact duplicate reviews from this CSV are skipped.
    """

    csv_path = Path(csv_path)

    if not csv_path.is_file():
        print(f"CSV file not found: {csv_path}")
        return

    conn = initialize_database(DB_PATH)

    if conn is None:
        print("Database connection failed.")
        return

    imported = 0
    skipped = 0
    failed = 0

    



    try:
        create_movies_table(conn)
        create_viewing_history_table(conn)
        create_unique_tmdb_index(conn)

        with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            required_columns = {
                "title",
                "release_year",
                "rating",
                "review",
                "date_watched",
            }

            if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
                raise ValueError(
                    f"CSV must contain these columns: {sorted(required_columns)}"
                )

            for row_number, row in enumerate(reader, start=2):

                try:
                    title = row["title"].strip()
                    release_year = int(row["release_year"])
                    rating = float(row["rating"])
                    review = (row["review"] or "").strip()
                    date_watched = (row["date_watched"] or "").strip() or None

                    if not title:
                        raise ValueError("Movie title is empty.")

                    if not 1 <= rating <= 10:
                        raise ValueError("Rating must be between 1 and 10.")

                    if date_watched:
                        date.fromisoformat(date_watched)

                    # Search TMDB
                    override_id = TMDB_OVERRIDES.get((title, release_year))

                    if override_id is not None:
                        tmdb_id = override_id
                    else:
                        search_data = search_movie(title)
                        results = search_data.get("results", [])

                    # Match title and release year.
                    # Do not silently select the wrong movie.
                        matching_movies = []

                        for movie in results:
                            movie_title = movie.get("title", "")
                            movie_date = movie.get("release_date", "")

                            if (
                                movie_title.casefold() == title.casefold()
                                and movie_date.startswith(str(release_year))
                            ):
                                matching_movies.append(movie)

                        if len(matching_movies) != 1:
                            raise ValueError(
                                f"Expected one TMDB match for "
                                f"{title} ({release_year}), "
                                f"found {len(matching_movies)}."
                            )

                        tmdb_id = matching_movies[0]["id"]

                    # Check local database
                    existing_movie = get_movie_by_tmdb_id(conn, tmdb_id)

                    if existing_movie:
                        movie_id = existing_movie[0]

                    else:
                        details = get_movie_details(tmdb_id)
                        metadata = extract_movie_metadata(details)

                        movie_id = insert_movie(
                            conn,
                            metadata["title"],
                            metadata["release_year"],
                            metadata["director"],
                            metadata["description"],
                            metadata["runtime"],
                            metadata["tmdb_id"],
                        )

                    # Check for an identical existing review.
                    # Intentional rewatches with different dates remain allowed.
                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        SELECT review_id
                        FROM viewing_history
                        WHERE movie_id = ?
                          AND user_id = ?
                          AND rating = ?
                          AND review = ?
                          AND date_watched IS ?;
                        """,
                        (
                            movie_id,
                            user_id,
                            rating,
                            review,
                            date_watched,
                        ),
                    )

                    if cursor.fetchone():
                        skipped += 1
                        print(f"SKIPPED: {title} — review already exists.")
                        continue

                    review_id = insert_review(
                        conn,
                        movie_id,
                        user_id,
                        rating,
                        review,
                        date_watched,
                    )

                    imported += 1

                    print(
                        f"IMPORTED: {title} ({release_year}) "
                        f"| Rating: {rating}/10 "
                        f"| Review ID: {review_id}"
                    )

                except Exception as error:
                    failed += 1
                    print(f"FAILED row {row_number}: {row.get('title')} — {error}")

        print("\n" + "=" * 45)
        print("AUREX MOVIE INTELLIGENCE IMPORT SUMMARY")
        print("=" * 45)
        print(f"Successfully imported: {imported}")
        print(f"Duplicates skipped:    {skipped}")
        print(f"Failed:                {failed}")
        print("=" * 45)

    finally:
        conn.close()


if __name__ == "__main__":

    csv_file = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "movie_ratings.csv"
    )

    import_movie_ratings(csv_file)