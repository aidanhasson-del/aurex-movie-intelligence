from pathlib import Path

import joblib
import numpy as np

from sklearn.linear_model import Ridge

from movie_intelligence.ml.dataset import load_training_data
from movie_intelligence.ml.features import MovieFeatureProcessor

from movie_intelligence.services.movie_metadata import (get_movie_details, extract_movie_metadata)


MODEL_PATH = (Path(__file__).resolve().parent / "models" / "movie_model_v8.joblib")


def prepare_training_data():
    """
    Load personal ratings from SQLite and retrieve 
    the corresponding movie metadata from TMDB.
    """

    movie_records = load_training_data()

    metadata_records = []
    ratings = []

    for movie in movie_records:

        title = movie[0]
        description = movie[1]
        rating = movie[2]
        tmdb_id = movie[3]

        if tmdb_id is None:
            print(f"SKIPPED: {title} - Missing TMDB ID")
            continue

        try:
            details = get_movie_details(tmdb_id)

            if not details:
                print(f"SKIPPED: {title} - No TMDB details")
                continue

            metadata = extract_movie_metadata(details)

            metadata["description"] = description

            metadata_records.append(metadata)
            ratings.append(float(rating))

        except Exception as error:
            print(f"SKIPPED: {title} - {error}")
            continue

    if not metadata_records:
        raise ValueError("No valide movies available for training.")

    print("\n==== TRAINING DATA ====")
    print("Original movies:", len(movie_records))
    print("Valid movies:", len(metadata_records))

    return metadata_records, np.array(ratings, dtype=float)

def train_model():
    """
    Train AUREX Movie Intelligence V8 and save
    its model and fitted preprocessing components.
    """

    metadata_records, ratings = prepare_training_data()

    #Initialize feature processor
    feature_processor = MovieFeatureProcessor()

    #Learn genre vocabulary and numerical scaling
    X = feature_processor.fit_transform(metadata_records)
    y = ratings

    print("\n==== FEATURE VERIFICATION ====")
    print("Feature matrix shape:", X.shape)
    print("Ratings shape:", y.shape)
    print("Genre count:", len(feature_processor.genre_encoder.classes_))

    assert X.shape[0] == len(y)

    #Train Ridge Regression
    model = Ridge(alpha=10.0)
    model.fit(X, y)

    print("\n==== MODEL TRAINED ====")
    print("Model: ", type(model).__name__)
    print("Alpha:", model.alpha)
    print("Model coefficients:", model.coef_.shape)
    print("Intercept:", model.intercept_)

    #Save fitted model + preprocessing components.
    #Load Sentence Transformer separately during
    #prediction using model identifier

    artifact = {
        "model": model,
        "genre_encoder": feature_processor.genre_encoder,
        "numerical_scaler": feature_processor.numerical_scaler,
        "embedding_model_name": MovieFeatureProcessor.MODEL_NAME,
        "feature_version": "v8",
        "feature_count": X.shape[1],
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(artifact, MODEL_PATH)

    print("\n==== MODEL SAVED ====")
    print("Path:", MODEL_PATH)

    return model

if __name__ == "__main__":
    train_model()


