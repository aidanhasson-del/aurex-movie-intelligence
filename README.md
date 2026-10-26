# AUREX Movie Intelligence

**A locally run personalized movie-ranking pipeline** built with SQLite, TMDB metadata, sentence embeddings, and Ridge regression. Developed as a component of the private AUREX AI system; this repository contains **only the independently reusable movie module** and an illustrative tool integration, not ARIA/VERA agent source.

## Architecture

```text
User or LLM supplies candidate movie titles
    -> TMDB search and metadata enrichment
    -> SQLite watched-history exclusion
    -> Sentence Transformer plot and keyword embeddings
    -> Multi-hot genres + scaled TMDB audience metrics + franchise flag
    -> Ridge(alpha=10) personalized score prediction
    -> Top-N unwatched recommendations (structured JSON)
```

The system **ranks candidate titles; it does not autonomously discover an entire film catalog**. A separate agent can generate candidate titles via a tool call (see `examples/agent_tool_example.py`). Direct `movie_pipeline.py` logging enriches movie metadata and stores ratings.

## Model details

- Text encoder: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions each for plot and keywords).
- Genre multi-hot encoding: variable number of columns (18 in the author's private training experiment).
- Numeric features: TMDB vote average, `log1p(vote_count)`, and franchise indicator. First two columns are standardized.
- 789 features in the author's V8 experiment (384 + 18 + 384 + 3). The feature count will vary with the user's genre vocabulary.
- Target: average personal movie rating (1–10), with duplicate viewings averaged per movie.
- Model: `sklearn.linear_model.Ridge(alpha=10.0)`; model and preprocessing are stored locally in a `joblib` artifact. Do not load untrusted `joblib` artifacts.

## Setup (PowerShell / Windows)

Run commands **from the repository root**. Python 3.11–3.13 is recommended; Python 3.14 from the original development environment has not been verified as a clean public setup.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `TMDB_READ_ACCESS_KEY` in `.env` to your **own TMDB API read-access token**. An internet connection is needed for TMDB requests and the first Sentence Transformer model download.

**Initialize an empty database:**

```powershell
python -m movie_intelligence.database.db
```

**Add movie ratings** by importing a CSV with columns `title,release_year,rating,review,date_watched` (one row per viewing). The file `examples/sample_ratings.csv` is fictitious demonstration data; it's not sufficient for a meaningful personalized ML model. Import it as follows:

```powershell
python -c "from movie_intelligence.services.bulk_import import import_movie_ratings; import_movie_ratings('examples/sample_ratings.csv')"
```

Add a larger set of **your own** movie ratings before training. Titles are matched against TMDB; the bulk import checks title plus release year and can reject ambiguous entries.

**Train:**

```powershell
python -m movie_intelligence.ml.train
```

Creates `movie_intelligence/ml/models/movie_model_v8.joblib` locally (ignored by Git). Some TMDB entries can fail or be skipped; training requires enough valid examples and a working network connection.

**Rank unwatched candidate titles:**

```powershell
python -c "from movie_intelligence.services.movie_recommendations import recommend_movies; print(recommend_movies(['Arrival', 'Moon', 'Her', 'Edge of Tomorrow'], top_n=3))"
```

When a model artifact is absent, predictions cannot run until you train a model. The public repository intentionally includes **no private trained model or personal ratings database**.

**Run unit tests:**

```powershell
python -m unittest discover -s tests -v
```

## Experimental evaluation (historical development runs)

| Feature configuration | Exploratory 5-fold MAE |
|---|---:|
| Plot embeddings only | 2.1223 |
| + genre features | 1.9816 |
| + keyword embeddings | 1.9291 |
| + director | 1.9279 |
| + cast | 1.9623 |
| + composer | 1.9566 |
| **V8: plot + genre + keyword + TMDB ratings/votes/franchise** | **1.4808** |
| Median predictor baseline | 2.0714 |

These are **exploratory development results, not independently validated test-set performance**. Feature selection reused validation folds, and the original numeric scaler was fitted before cross-validation. The small private training sample (about 105 usable films) and popularity inputs further limit interpretation. The live TMDB metadata can change over time. Consider nested cross-validation or a dedicated holdout and an audience-rating-only baseline in future work.

## Project layout

- `movie_intelligence/database/db.py`: SQLite schema and helpers.
- `movie_intelligence/services/movie_metadata.py`: TMDB search and enrichment.
- `movie_intelligence/services/bulk_import.py`: ratings CSV import.
- `movie_intelligence/services/movie_pipeline.py`: individual movie logging.
- `movie_intelligence/ml/features.py`: feature extraction and preprocessing.
- `movie_intelligence/ml/train.py`: training and serialization.
- `movie_intelligence/ml/evaluate.py`: original exploratory evaluations.
- `movie_intelligence/ml/recommender.py`: scoring and ranking.
- `movie_intelligence/services/movie_recommendations.py`: validated agent-friendly entry point.
- `examples/agent_tool_example.py`: sanitized function-call example, **not a standalone agent**.

## Limitations

- TMDB title search uses the first matching result for individual logging and ranking; ambiguous titles may resolve incorrectly. Bulk CSV import is stricter.
- Predictions are estimates of individual taste, **not confidence-calibrated probabilities**.
- The recommender evaluates up to 20 supplied titles per `recommend_movies` invocation, returning up to five.
- The notebook-free demo depends on local API access; no full browser interface or independent LLM agent is shipped.
- The movie `joblib` model embeds preprocessing objects, but not original raw rating rows. It remains private by default.

## Attribution

Uses metadata provided by [TMDB](https://www.themoviedb.org/). **This product uses the TMDB API but is not endorsed or certified by TMDB.**

## License

No license selected yet. Code is publicly viewable when posted, but is not automatically licensed for reuse. Add an explicit LICENSE file only after choosing the terms you want.
