import os
import requests
from dotenv import load_dotenv


load_dotenv()

TMDB_READ_ACCESS_KEY = os.getenv("TMDB_READ_ACCESS_KEY")


def _auth_headers():
    if not TMDB_READ_ACCESS_KEY:
        raise RuntimeError("TMDB_READ_ACCESS_KEY is missing. Copy .env.example to .env and set your own token.")
    return {"Authorization": f"Bearer {TMDB_READ_ACCESS_KEY}", "accept": "application/json"}

def search_movie(title):
    url = "https://api.themoviedb.org/3/search/movie"

    headers = _auth_headers()

    response = requests.get(url, headers=headers, params={"query": title}, timeout=20)

    response.raise_for_status()

    return response.json()




def get_movie_details(movie_id):
    '''
    Accesses additional movie metadata from credits and additonal endpoint.
    '''
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"

    headers = _auth_headers()

    response = requests.get(url, headers=headers, params={"append_to_response": "credits,keywords"}, timeout=20)

    response.raise_for_status()

    return response.json()



def extract_movie_metadata(movie_details):
    #Access Director
    director = None

    credits_data = movie_details.get("credits", {}).get("crew", [])

    for person in credits_data:
        if person.get("job") == "Director":
            director = person["name"]
            break

    title = movie_details["title"]    
    runtime = movie_details["runtime"]
    overview = movie_details["overview"]
    tmdb_id = movie_details["id"]
    release_date = movie_details.get("release_date", "")

    if release_date:
        release_year = int(release_date[:4])
    else:
        release_year = None

    genres_data = movie_details.get("genres", [])
    genres = [
        genre["name"]
        for genre in genres_data
        if genre.get("name")
    ]

    keywords_data = movie_details.get("keywords", {}).get("keywords", [])

    keywords = [
        keyword["name"]
        for keyword in keywords_data
        if keyword.get("name")
    ]

    cast_data = movie_details.get("credits", {}).get("cast", [])

    cast = [
        actor["name"]
        for actor in sorted(
            cast_data,
            key=lambda actor: actor.get("order", 999)
        )[:5]
        if actor.get("name")
    ]

    composers = [
        person["name"]
        for person in credits_data
        if person.get("job") == "Original Music Composer"
        and person.get("name")
    ]

    vote_average = movie_details.get("vote_average", 0)
    vote_count = movie_details.get("vote_count", 0)

    collection = movie_details.get("belongs_to_collection")

    is_franchise = 1 if collection else 0

    movie_values = {
        "title": title,
        "release_year": release_year,
        "director": director,
        "description": overview,
        "runtime": runtime,
        "tmdb_id": tmdb_id,
        "genres": genres,
        "keywords": keywords,
        "cast": cast,
        "composers": composers,
        "vote_average": vote_average,
        "vote_count": vote_count,
        "is_franchise": is_franchise
    }

    return movie_values





if __name__ == "__main__":

    details = get_movie_details(157336)

    metadata = extract_movie_metadata(details)

    print("\n===== INTERSTELLAR METADATA =====")
    print("Title:", metadata["title"])
    print("Genres:", metadata["genres"])
    print("Keywords:", metadata["keywords"])
    print("Director:", metadata["director"])
    print("Cast:", metadata["cast"])
    print("Composers:", metadata["composers"])
    print("Audience Rating:", metadata["vote_average"])
    print("Vote Count:", metadata["vote_count"])
    print("Franchise:", metadata["is_franchise"])

    title = "Interstellar"
    data = search_movie(title)
    #Check if movies exist
    movies = data["results"]
    if movies:
        movie = data["results"][0]
        first_movie_id = movie["id"]
        
            
        movie_details = get_movie_details(first_movie_id)
        metadata = extract_movie_metadata(movie_details)
        print(metadata)
    else:
        print("No movies found")

    

    

    

    


