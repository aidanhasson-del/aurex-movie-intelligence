from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from movie_intelligence.ml.dataset import load_training_data

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


#similarity = cos_sim(description1, description2)
#print(similarity)

movie_records = load_training_data()


movie_descriptions = [movie[1] for movie in movie_records]

embeddings = model.encode(movie_descriptions)
ratings = [movie[2] for movie in movie_records]

print(embeddings.shape)
print(len(ratings))
print(ratings[:5])