"""SQLite tests use an in-memory database; do not touch your private ratings."""
import sqlite3
import unittest
from movie_intelligence.database.db import (
    create_movies_table, create_viewing_history_table, insert_movie, insert_review, get_movie_by_tmdb_id,
)

class DatabaseTests(unittest.TestCase):
    def test_record_viewing(self):
        con = sqlite3.connect(":memory:")
        con.execute("PRAGMA foreign_keys = ON")
        try:
            create_movies_table(con)
            create_viewing_history_table(con)
            movie_id = insert_movie(con, "Example Film", 2020, "Director", "A synopsis", 90, 12345)
            review_id = insert_review(con, movie_id, 1, 8.5, "Good", "2026-01-01")
            self.assertIsInstance(review_id, int)
            self.assertEqual(get_movie_by_tmdb_id(con, 12345)[0], movie_id)
            self.assertEqual(con.execute("SELECT rating FROM viewing_history").fetchone()[0], 8.5)
        finally:
            con.close()

if __name__ == "__main__":
    unittest.main()
