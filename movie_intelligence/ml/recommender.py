import joblib
import numpy as np

from pathlib import Path

from movie_intelligence.ml.features import MovieFeatureProcessor

from movie_intelligence.services.movie_metadata import (search_movie, get_movie_details, extract_movie_metadata)

from movie_intelligence.database.db import get_watched_movie_ids


MODEL_PATH = (Path(__file__).resolve().parent / "models" / "movie_model_v8.joblib")

class MovieRecommender:
    """
    Loads the trained AUREX Movie Intelligence V8 model
    and predicts personalized movie ratings.
    """

    def __init__(self):

        #Load the trained model and preprocessing components
        artifact = joblib.load(MODEL_PATH)
        self.model = artifact["model"]

        #Recreate the feature processor
        self.feature_processor = MovieFeatureProcessor()

        #Restore fitted preprocessing components
        self.feature_processor.genre_encoder = artifact["genre_encoder"]

        self.feature_processor.numerical_scaler = artifact["numerical_scaler"]

        self.feature_processor.is_fitted = True

        #Validate model compatibility
        self.feature_count = artifact["feature_count"]

        if self.model.n_features_in_ != self.feature_count:
            raise ValueError("Model feature count mismatch.")

        print("AUREX Movie Intelligence V8 loaded successfully!")

    def predict_from_metadata(self, metadata):
        """
        Predict a movie rating using its TMDB metadata.
        """

        features = self.feature_processor.transform([metadata])

        if features.shape[1] != self.feature_count:
            raise ValueError(
                f"Expected {self.feature_count} features, "
                f"received {features.shape[1]}"
            )

        prediction = float(self.model.predict(features)[0])

        #Keep displayed scores between 1 and 10
        prediction = float(np.clip(prediction, 1.0, 10.0))

        return prediction

    def predict_movie_rating(self, title):
        """
        Search TMDB for a movie and predict its rating.
        """

        results = search_movie(title)

        if not results or not results.get("results"):
            raise ValueError(f"Movie not found: {title}")

        #Select the first TMDB search result
        movie = results["results"][0]
        details = get_movie_details(movie["id"])
        metadata = extract_movie_metadata(details)
        predicted_rating = self.predict_from_metadata(metadata)

        return {
            "title": metadata["title"],
            "tmdb_id": metadata["tmdb_id"],
            "predicted_rating": round(predicted_rating, 2),
            "genres": metadata["genres"],
            "description": metadata["description"],
            "director": metadata.get("director"),
            "keywords": metadata.get("keywords", []),
            "vote_average": metadata.get("vote_average")
        }

    def rank_movies(self, movie_titles, top_n=5):
        """
        Predict ratings for candidate movies and return
        the highest-ranked results.
        """

        if not isinstance(movie_titles, list):
            raise ValueError("movie_titles must be a list.")

        if not movie_titles:
            return []

        top_n = max(1, min(int(top_n), 10))

        metadata_records = []
        seen_ids = set()

        watched_ids = {
            int(movie_id)
            for movie_id in get_watched_movie_ids()
            if movie_id is not None
        }

        print(f"Watched movies found in database: {len(watched_ids)}")

        for title in movie_titles:
            try:
                results = search_movie(title)

                if not results.get("results"):
                    print(f"NOT FOUND: {title}")
                    continue

                movie = results["results"][0]
                tmdb_id = movie["id"]

                if tmdb_id in watched_ids:
                    print(f"ALREADY WATCHED: {title}")
                    continue

                if tmdb_id in seen_ids:
                    continue

                details = get_movie_details(tmdb_id)
                metadata = extract_movie_metadata(details)

                seen_ids.add(tmdb_id)
                metadata_records.append(metadata)
            
            except Exception as error:
                print(f"SKIPPED: {title} - {error}")

        if not metadata_records:
            return []

        #Process all candidates in one batch.
        features = self.feature_processor.transform(metadata_records)

        if features.shape[1] != self.feature_count:
            raise ValueError("Model feature count mismatch.")

        predictions = self.model.predict(features)

        ranked_movies = []

        for metadata, prediction in zip(metadata_records, predictions):
            ranked_movies.append({
                "title": metadata["title"],
                "tmdb_id": metadata["tmdb_id"],
                "predicted_rating": round(
                    float(np.clip(prediction, 1.0, 10.0)), 2
                ),
                "genres": metadata["genres"],
                "description": metadata["description"]
            })

        ranked_movies.sort(
            key=lambda movie: movie["predicted_rating"],
            reverse=True
        )

        return ranked_movies[:top_n]

if __name__ == "__main__":
    recommender = MovieRecommender()

    candidates = [
        "Arrival",
        "Ex Machina",
        "Blade Runner 2049",
        "Moon",
        "Her",
        "The Creator",
        "Oblivion",
        "Edge of Tomorrow",
        "Minority Report",
        "Chappie"
    ]

    recommendations = recommender.rank_movies(candidates, top_n=5)

    print("\n==== AUREX MOVIE RECOMMENDATIONS ====")

    for i, movie in enumerate(recommendations, start=1):
        print(
            f"{i}. {movie['title']} - "
            f"{movie['predicted_rating']}/10"
        )

