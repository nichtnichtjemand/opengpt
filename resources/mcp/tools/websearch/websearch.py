import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from tavily import BadRequestError, TavilyClient

for candidate in (
    Path(getattr(sys, "_MEIPASS", "")),
    Path(__file__).resolve().parents[4],
    Path(__file__).resolve().parent,
    Path.cwd(),
):
    env_path = candidate / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
        break

client = TavilyClient(os.getenv("TAVILY_API_KEY"))


def get_search(query, timerange):
    try:
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
    except BadRequestError as e:
        return f"Bad Request: {e}"
