from movie_intelligence.ml.dataset import load_training_data
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, cross_val_score
from sklearn.dummy import DummyRegressor
import numpy as np
from movie_intelligence.services.movie_metadata import get_movie_details
from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder, StandardScaler
from movie_intelligence.services.movie_metadata import extract_movie_metadata



kf = KFold(n_splits=5, shuffle=True, random_state=42)
alphas = [0.01, 0.1, 1.0, 10.0, 100.0]

def prepare_features():
    """
    Load training data, retrieve TMDB genres,
    and generate embeddings for valid movies.
    """

    movie_records = load_training_data()

    if not movie_records:
        raise ValueError("No training data found.")

    valid_descriptions = []
    valid_ratings = []
    movie_genres = []
    movie_keywords = []
    movie_directors = []
    movie_cast = []
    movie_composers = []
    movie_numerical_features = []

    

    for movie in movie_records:
        title = movie[0]
        description = movie[1]
        rating = movie[2]
        tmdb_id = movie[3]

        if tmdb_id is None:
            print(f"SKIPPED: {title} — Missing TMDB ID")
            continue

        try:
            details = get_movie_details(tmdb_id)

            if not details:
                print(f"SKIPPED: {title} — No TMDB details")
                continue

            genres = [
                genre["name"]
                for genre in details.get("genres", [])
                if genre.get("name")
            ]

            keywords_data = details.get("keywords", {}).get("keywords", [])

            keywords = [
                keyword["name"]
                for keyword in keywords_data
                if keyword.get("name")
            ]

            metadata = extract_movie_metadata(details)
            director = metadata["director"]
            cast = metadata["cast"]
            composers = metadata["composers"]


        except Exception as error:
            print(f"SKIPPED: {title} — {error}")
            continue

        

        valid_descriptions.append(description)
        valid_ratings.append(rating)
        movie_genres.append(genres)
        movie_keywords.append(keywords)
        movie_directors.append(director if director else "Unknown")
        movie_cast.append(cast)
        movie_composers.append(composers)
        movie_numerical_features.append([
            metadata["vote_average"],
            np.log1p(metadata["vote_count"]),
            metadata["is_franchise"]
        ])

    if not valid_descriptions:
        raise ValueError("No valid movies available for training.")

    numerical_features = np.array(
        movie_numerical_features,
        dtype=float
    )

    scaler = StandardScaler()

    numerical_features[:, :2] = scaler.fit_transform(\
        numerical_features[:, :2])

    print("\n===== DATA VERIFICATION =====")
    print("Original movies:", len(movie_records))
    print("Valid movies:", len(valid_descriptions))
    print("Genre lists:", len(movie_genres))

    keyword_texts = [
        ", ".join(keywords)
        for keywords in movie_keywords
    ]

    director_encoder = OneHotEncoder(
        handle_unknown="ignore",
        sparse_output=False
    )

    director_features = director_encoder.fit_transform(
        np.array(movie_directors).reshape(-1, 1)
    )

    cast_encoder = MultiLabelBinarizer()
    cast_features = cast_encoder.fit_transform(movie_cast)

    composer_encoder = MultiLabelBinarizer()
    composer_features = composer_encoder.fit_transform(movie_composers)



    embedding_model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    embeddings = embedding_model.encode(valid_descriptions)
    keyword_embeddings = embedding_model.encode(keyword_texts)

    for i, keywords in enumerate(movie_keywords):
        if not keywords:
            keyword_embeddings[i] = 0

    genre_encoder = MultiLabelBinarizer()
    genre_features = genre_encoder.fit_transform(movie_genres)

    v3_features = np.hstack((
        embeddings, 
        genre_features
    ))

    v4_features = np.hstack((
        embeddings,
        genre_features,
        keyword_embeddings
    ))

    v5_features = np.hstack((
        v4_features,
        director_features
    ))

    v6_features = np.hstack((
        v5_features,
        cast_features
    ))

    v7_features = np.hstack((
        v6_features,
        composer_features
    ))

    v8_features = np.hstack((
        v4_features,
        numerical_features
    ))

    print("Genre features shape:", genre_features.shape)
    print("Available genres:", genre_encoder.classes_)


    assert len(embeddings) == len(valid_ratings) == len(movie_genres)

    return embeddings, v3_features, v4_features, v5_features, v6_features, v7_features, v8_features, valid_ratings, movie_genres

    

def evaluate_model(alpha, embeddings, ratings, kf):
    '''
    Evaluate Ridge Regression using cross-validation
    '''
    
    #Set Model and Cross Validate Scores
    model=Ridge(alpha=alpha)
    scores = cross_val_score(estimator=model,X=embeddings,y=ratings,cv=kf,scoring="neg_mean_absolute_error")

    #Calculate the average MAE by taking the negative of the mean
    mae = -scores.mean()
    print(f"Alpha {alpha}: MAE = {mae:.4f}")

    return mae

def evaluate_baselines(embeddings, ratings, kf):
    '''
    Evaluate mean and median baseline models
    '''

    #Mean Baseline
    dummy_mean = DummyRegressor(strategy="mean")
    mean_scores = cross_val_score(estimator=dummy_mean,X=embeddings,y=ratings,cv=kf,scoring="neg_mean_absolute_error")
    
    mean_mae = -mean_scores.mean()

    #Median Baseline
    dummy_median = DummyRegressor(strategy="median")

    median_scores = cross_val_score(
        estimator=dummy_median,
        X=embeddings,
        y=ratings,
        cv=kf,
        scoring="neg_mean_absolute_error"
    )

    median_mae = -median_scores.mean()

    print("\n==== BASELINE RESULTS ====")
    print(f"Mean Baseline MAE: {mean_mae:.4f}")
    print(f"Median Baseline MAE: {median_mae:.4f}")

    return mean_mae, median_mae


def loop_alpha(alphas, embeddings, ratings, kf):
    '''
    Evaluate multiple Ridge alpha values. 
    '''
    print("\n===== RIDGE REGRESSION RESULTS =====")

    results = {}

    for alpha in alphas:
        mae = evaluate_model(alpha, embeddings, ratings, kf)
        results[alpha] = mae

    best_alpha = min(results, key=results.get)

    print("\n===== BEST RIDGE MODEL =====")
    print(f"Best alpha: {best_alpha}")
    print(f"Best MAE: {results[best_alpha]:.4f}")

    return results


if __name__ == "__main__":
    embeddings, v3_features, v4_features, v5_features, v6_features, v7_features, v8_features, ratings, movie_genres = prepare_features()

    print("\n==== DESCRIPTION_ONLY MODLE ====")
    loop_alpha(alphas, embeddings, ratings, kf)

    print("\n==== V3: PLOT + GENRES ====")
    loop_alpha(alphas, v3_features, ratings, kf)

    print("\n==== V4: PLOT + GENRES + KEYWORDS ====")
    loop_alpha(alphas, v4_features, ratings, kf)

    #print("\n==== V5: PLOT + GENRES + KEYWORDS + DIRECTORS ====")
    #loop_alpha(alphas, v5_features, ratings, kf)

    #print("\n==== V6: Plot + GENRES + KEYWORDS + DIRECTORS + CAST ===-")
    #loop_alpha(alphas, v6_features, ratings, kf)

    #print("\n==== V7: PLOT + GENRES + KEYWORDS + DIRECTORS + CAST + COMPOSERS ====")
    #loop_alpha(alphas, v7_features, ratings, kf)

    print("\n==== V8: Audience + Votes + Franchises")
    loop_alpha(alphas, v8_features, ratings, kf)

    print("\n==== BASELINES ====")
    evaluate_baselines(embeddings, ratings, kf)




#Results First Set
#===== RIDGE REGRESSION RESULTS =====
#Alpha 0.01: MAE = 2.6801
#Alpha 0.1: MAE = 2.5441
#Alpha 1.0: MAE = 2.2324
#Alpha 10.0: MAE = 2.1223
#Alpha 100.0: MAE = 2.1296

#===== BEST RIDGE MODEL =====
#Best alpha: 10.0
#Best MAE: 2.1223

#==== V3: PLOT + GENRES ====

#===== RIDGE REGRESSION RESULTS =====
#Alpha 0.01: MAE = 2.5900
#Alpha 0.1: MAE = 2.4301
#Alpha 1.0: MAE = 2.0946
#Alpha 10.0: MAE = 1.9816
#Alpha 100.0: MAE = 2.0619

#===== BEST RIDGE MODEL =====
#Best alpha: 10.0
#Best MAE: 1.9816

#==== V4: PLOT + GENRES + KEYWORDS ====

#===== RIDGE REGRESSION RESULTS =====
#Alpha 0.01: MAE = 2.1498
#Alpha 0.1: MAE = 2.0990
#Alpha 1.0: MAE = 1.9524
#Alpha 10.0: MAE = 1.9291
#Alpha 100.0: MAE = 2.0492

#===== BEST RIDGE MODEL =====
#Best alpha: 10.0
#Best MAE: 1.9291

#==== V5: PLOT + GENRES + KEYWORDS + DIRECTORS ====

#===== RIDGE REGRESSION RESULTS =====
#Alpha 0.01: MAE = 2.0788
#Alpha 0.1: MAE = 2.0567
#Alpha 1.0: MAE = 1.9614
#Alpha 10.0: MAE = 1.9279
#Alpha 100.0: MAE = 2.0485

#===== BEST RIDGE MODEL =====
#Best alpha: 10.0
#Best MAE: 1.9279

#==== V6: Plot + GENRES + KEYWORDS + DIRECTORS + CAST ===-

#===== RIDGE REGRESSION RESULTS =====
#Alpha 0.01: MAE = 2.0037
#Alpha 0.1: MAE = 2.0021
#Alpha 1.0: MAE = 1.9908
#Alpha 10.0: MAE = 1.9623
#Alpha 100.0: MAE = 2.0483

#===== BEST RIDGE MODEL =====
#Best alpha: 10.0
#Best MAE: 1.9623

#==== V7: PLOT + GENRES + KEYWORDS + DIRECTORS + CAST + COMPOSERS ====

#===== RIDGE REGRESSION RESULTS =====
#Alpha 0.01: MAE = 2.0029
#Alpha 0.1: MAE = 2.0015
#Alpha 1.0: MAE = 1.9887
#Alpha 10.0: MAE = 1.9566
#Alpha 100.0: MAE = 2.0450

#===== BEST RIDGE MODEL =====
#Best alpha: 10.0
#Best MAE: 1.9566

#==== BASELINES ====

#==== BASELINE RESULTS ====
#Mean Baseline MAE: 2.1311
#Median Baseline MAE: 2.0714