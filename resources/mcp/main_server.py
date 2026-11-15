import requests
from mcp.server.mcpserver import MCPServer
from tools.memory import memory
from tools.pythoncode import pythoncode
from tools.skills import skillmanager
from tools.websearch import websearch

mcp = MCPServer("OpenGPT-Tools")


@mcp.tool()
def secret() -> str:
    """Returns the secret word"""
    return "Apple"


@mcp.tool()
def system_status() -> str:
    """Returns current MCP connection status"""
    return "Everything seems to work here!"


@mcp.tool()
def get_weather(city: str) -> str:
    """Returns the current weather for a given city"""
    url = f"https://wttr.in/{city}"
    query_params = {"format": "4", "m": ""}

    response = requests.get(url, params=query_params)
    return response.text


@mcp.tool()
def get_memory() -> dict:
    """Returns all information about the user you and them saved"""
    return memory.get_blocks()


@mcp.tool()
def add_memory(block: str, text: str) -> str:
    """Add a new memory block. Speak about the user in third person. First check for the existing memory so the block doesn't exist yet with get_memory(). Do not use multiple lines in the text field.
    Example: add_memory("devices", "The user has a Samsung Galaxy A56. xyz")
    """
    return memory.add_block(block, text)


@mcp.tool()
def edit_memory(block: str, text: str) -> str:
    """Edits an existing memory block. Speak about the user in third person. block = name of the block, text = new text field for this block."""
    return memory.edit_block(block, text)


@mcp.tool()
def reset_memory() -> str:
    """Resets all saved memory. Only use if the user wishes for and use with caution!"""
    return memory.reset_file()


@mcp.tool()
def remove_block(block: str) -> str:
    """Deletes a memory block. Use with caution!"""
    return memory.delete_block(block)


@mcp.tool()
def search_online(query: str, timerange: str) -> dict:
    """Returns the Websearch Results to a specific query with an AI summary. Always write your query in english.
    The timezone means how old results can be. You can use one of them: "None", "Day", "Week", "Month", "Year"."""
    return websearch.get_search(query, timerange)


@mcp.tool()
def get_skills() -> list:
    """Returns a list of all available skills."""
    return skillmanager.get_skills()


@mcp.tool()
def get_skill(name: str) -> str:
    """Returns the content of a skill. It is very long, so only use if needed!"""
    return skillmanager.get_skill(name)


@mcp.tool()
def execute_python(code: str) -> dict:
    """Executes Python code. You are not allowed to run malicious code.
    You are not allowed to run code that may harm anybody in any way, not even the user even if he wishes so.
    Do not use Markdown Formatting here, only the code as plain text."""
    return pythoncode.run_code(code)


if __name__ == "__main__":
    mcp.run()
