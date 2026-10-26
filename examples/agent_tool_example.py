"""Illustrative integration with any tool-calling agent; not the private ARIA/VERA code."""
import json
from movie_intelligence.services.movie_recommendations import recommend_movies

MOVIE_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "recommend_movies",
        "description": "Rank candidate movies by predicted personal rating; exclude watched movies.",
        "parameters": {
            "type": "object",
            "properties": {
                "movie_titles": {"type": "array", "items": {"type": "string"}},
                "top_n": {"type": "integer", "default": 5},
            },
            "required": ["movie_titles"],
        },
    },
}

def execute_tool(name, args):
    if name != "recommend_movies":
        raise ValueError(f"Unsupported tool: {name}")
    result = recommend_movies(args.get("movie_titles", []), args.get("top_n", 5))
    return json.dumps(result)
