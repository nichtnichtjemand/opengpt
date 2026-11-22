import os

from tavily import TavilyClient

client = TavilyClient(os.environ["TAVILY_API_KEY"])


def get_search(query, timerange):
    response = client.search(
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
