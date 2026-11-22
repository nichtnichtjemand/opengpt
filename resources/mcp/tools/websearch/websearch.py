from tavily import BadRequestError, TavilyClient
from config import get_api_key


def get_client() -> TavilyClient:
    api_key = get_api_key("TAVILY_API_KEY")
    if not api_key:
        raise BadRequestError("TAVILY_API_KEY is not configured.")
    return TavilyClient(api_key)


def get_search(query, timerange):
    try:
        response = get_client().search(
            query=query,
            include_answer="basic",
            search_depth="basic",
            include_published_date=True,
            include_favicon=False,
            include_usage=False,
            max_results=4,
            time_range=timerange,
        )
        return response
    except BadRequestError as e:
        return f"Bad Request: {e}"
