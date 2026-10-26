import numpy as np

from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler


class MovieFeatureProcessor:
    """
    Converts TMDB movie metadata into numerical features for AUREX Movie Intelligence V8.
    
    Features:
        - Plot embeddings: 384 dimensions
        - Genres: Multi-hot encoded
        - Keyword embeddings: 384 dimensions
        - TMDB audeince rating: 1 dimension
        - Log-transformed vote count: 1 dimension
        - Franchise membership: 1 dimension
    """

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self):
        #Sentence Transformer used for plot and keyword embeddings
        self.embedding_model = SentenceTransformer(self.MODEL_NAME)

        #Encoder for movie genres
        self.genre_encoder = MultiLabelBinarizer()

        #Scaler for audience rating and vote count
        self.numerical_scaler = StandardScaler()

        #Track whether preprocessing has been fitted
        self.is_fitted = False

    def get_numerical_features(self, movie_metadata):
        """
        Extract numerical features from movie metadata.
        
        Returns: 
            NumPy array with three columns:
            [audience_rating, log_vote_count, franchise_membership]
        """

        numerical_features = []

        for movie in movie_metadata:

            vote_average = float(
                movie.get("vote_average") or 0
            )

            vote_count = float(
                movie.get("vote_count") or 0
            )

            is_franchise = int(
                movie.get("is_franchise") or 0
            )

            numerical_features.append([
                vote_average,
                np.log1p(max(0, vote_count)),
                is_franchise
            ])

        return np.array(numerical_features, dtype=float)

    def _prepare_text_features(self, movie_metadata):
        """
        Prepare movie descriptions, genres and keyword text.
        """

        descriptions = [
            movie.get("description") or ""
            for movie in movie_metadata
        ]

        genres = [
            movie.get("genres") or []
            for movie in movie_metadata
        ]

        keyword_lists = [
            movie.get("keywords") or []
            for movie in movie_metadata
        ]

        keyword_texts = [
            ", ".join(keywords)
            for keywords in keyword_lists
        ]

        return descriptions, genres, keyword_lists, keyword_texts

    def _generate_embeddings(self, descriptions, keyword_lists, keyword_texts):
        """
        Generate semantic embeddings for plots and keywords
        """

        plot_embeddings = self.embedding_model.encode(
            descriptions
        )

        keyword_embeddings = self.embedding_model.encode(
            keyword_texts
        )

        #A movie with no keywords does not get a meaningful keyword embedding
        for i, keywords in enumerate(keyword_lists):
            if not keywords:
                keyword_embeddings[i] = 0

        return plot_embeddings, keyword_embeddings

    def fit_transform(self, movie_metadata):
        """
        Used during training.
        
        Fits the genre encoder and numerical scaler,
        then generates the complete feature matrix.
        """

        if not movie_metadata:
            raise ValueError("No movie metadata supplied.")

        descriptions, genres, keyword_lists, keyword_texts = (
            self._prepare_text_features(movie_metadata)
        )

        #Generate semantic features
        plot_embeddings, keyword_embeddings = (
            self._generate_embeddings(
                descriptions,
                keyword_lists,
                keyword_texts
            )
        )

        #Learn genre vocabulary from training movies
        genre_features = self.genre_encoder.fit_transform(genres)

        #Extract and scale numerical features
        numerical_features = self.get_numerical_features(movie_metadata)

        numerical_features[:, :2] = (
            self.numerical_scaler.fit_transform(
                numerical_features[:, :2]
            )
        )

        #Combine all features in a consistent order
        combined_features = np.hstack((
            plot_embeddings,
            genre_features,
            keyword_embeddings,
            numerical_features
        ))

        self.is_fitted = True

        return combined_features

    def transform(self, movie_metadata):
        """
        Used during prediction.
        
        Uses the previously fitted genre encoder
        and numerical scaler
        
        Does NOT refit preprocessing.
        """

        if not self.is_fitted:
            raise ValueError(
                "MovieFeatureProcessor must be fitted before prediction."
            )

        if not movie_metadata:
            raise ValueError("No movie metadata supplied.")

        descriptions, genres, keyword_lists, keyword_texts = (
            self._prepare_text_features(movie_metadata)
        )

        #Generate semantic features
        plot_embeddings, keyword_embeddings = (
            self._generate_embeddings(
                descriptions,
                keyword_lists,
                keyword_texts
            )
        )

        #Use existing genre vocabulary
        genre_features = self.genre_encoder.transform(genres)

        #Extract numerical features
        numerical_features = self.get_numerical_features(movie_metadata)

        #Use existing scaler
        numerical_features[:, :2] = (
            self.numerical_scaler.transform(
                numerical_features[:, :2]
            )
        )

        #Same feature order as training
        combined_features = np.hstack((
            plot_embeddings,
            genre_features,
            keyword_embeddings,
            numerical_features
        ))

        return combined_features