from functools import lru_cache

from movie_intelligence.ml.recommender import MovieRecommender

@lru_cache(maxsize=1)
def get_recommender():
    """
    Load the recommendation model once and reuse it.
    """
    return MovieRecommender()

def recommend_movies(movie_titles, top_n=5):
    """
    Rank candidate movies using AUREX Movie Intelligence V8.
    """

    if not isinstance(movie_titles, list):
        return {
            "success": False,
            "message": "movie_titles must be a list.",
            "recommendations": []
        }

    #Limit the number of candidates and results
    movie_titles = [
        title.strip()
        for title in movie_titles[:20]
        if isinstance(title, str) and title.strip()
    ]

    if not movie_titles:
        return {
            "success": False,
            "message": "No valid movie titles provided.",
            "recommendations": []
        }
    try:
        top_n = max(1, min(int(top_n), 5))

        recommender = get_recommender()

        results = recommender.rank_movies(
            movie_titles=movie_titles,
            top_n=top_n
        )

        return {
            "success": True,
            "message": (
                "Personalized movie recommendations generated."
                if results
                else "No unwatched movies found among the candidates."
            ),
            "recommendations": results
        }
    except Exception as error:
        return {
            "success": False,
            "message": f"Movie recommendation failed: {error}",
            "recommendations": []
        }

if __name__ == "__main__":
    result = recommend_movies(
        [
            "Her",
            "Arrival",
            "Moon",
            "Edge of Tomorrow",
            "minority Report"
        ]
    )

    print(result)