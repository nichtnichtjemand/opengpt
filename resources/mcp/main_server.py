import traceback

import requests
from mcp.server.mcpserver import MCPServer
from tools.memory import memory
from tools.memory.memory import MStorageParseError
from tools.skills import skillmanager
from tools.websearch import websearch
from tools.workspace.sandbox_manager import sandbox_manager

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
    if city == "":
        return "Bad Request: No city given"
    url = f"https://wttr.in/{city}"
    query_params = {"format": "4", "m": ""}

    response = requests.get(url, params=query_params)
    return response.text


@mcp.tool()
def get_memory() -> dict:
    """Returns all information about the user you and them saved"""
    try:
        return memory.get_blocks()
    except MStorageParseError as e:
        return f"Error: {e}"


@mcp.tool()
def add_memory_block(block: str, text: str) -> str:
    """Add a new memory block. Speak about the user in third person. First check for the existing memory so the block doesn't exist yet with get_memory(). Do not use multiple lines in the text field.
    Example: add_memory("devices", "The user has a Samsung Galaxy A56. xyz")
    """
    try:
        return memory.add_block(block, text)
    except MStorageParseError as e:
        return f"Error: {e}"


@mcp.tool()
def edit_memory(block: str, text: str) -> str:
    """Edits an existing memory block. Speak about the user in third person. block = name of the block, text = new text field for this block."""
    try:
        return memory.edit_block(block, text)
    except MStorageParseError as e:
        return f"Error: {e}"


@mcp.tool()
def reset_memory() -> str:
    """Resets all saved memory. Only use if the user wishes for and use with caution!"""
    return memory.reset_file()


@mcp.tool()
def remove_memory_block(block: str) -> str:
    """Deletes a memory block. Use with caution!"""
    try:
        return memory.delete_block(block)
    except MStorageParseError as e:
        return f"Error: {e}"


@mcp.tool()
def search_online(query: str, timerange: str) -> dict:
    """Returns the Websearch Results to a specific query with an AI summary. Always write your query in english.
    The timezone parameter for this tool means how old results can be. You can use one of them: "None", "Day", "Week", "Month", "Year"."""

    return websearch.get_search(query, timerange)


@mcp.tool()
def get_skill(name: str) -> str:
    """Returns the content of a skill. It is very long, so only use if needed!"""
    return skillmanager.get_skill(name)


@mcp.tool()
def workspace_run_shell(command: str) -> str:
    """Executes a bash command in the shell. You MUST read the 'workspace' skill instructions before calling this tool for the first time."""
    try:
        sb = sandbox_manager.get_or_create()
        res = sb.run_shell(command)
        return f"Exit-Code: {res['exit_code']}\nSTDOUT:\n{res['stdout']}\nSTDERR:\n{res['stderr']}"
    except Exception:  # noqa: BLE001
        return f"Error in workspace_run_shell:\n{traceback.format_exc()}"


@mcp.tool()
def workspace_write_file(path: str, content: str) -> str:
    """Creates or overwrites a whole file. You MUST read the 'workspace' skill instructions before calling this tool for the first time. NEVER run this tool without reading the 'workspace' skill!"""
    sb = sandbox_manager.get_or_create()
    res = sb.write_file(path, content)
    return "File saved." if res["status"] == "ok" else f"Error: {res['detail']}"


@mcp.tool()
def workspace_edit_file(path: str, old_text: str, new_text: str) -> str:
    """Edits an exact text block (old_text -> new_text) in a file. You MUST read the 'workspace' skill instructions before calling this tool for the first time. NEVER run this tool without reading the 'workspace' skill!"""
    sb = sandbox_manager.get_or_create()
    res = sb.edit_file(path, old_text, new_text)
    return "File edited." if res["status"] == "ok" else f"Error: {res['detail']}"


@mcp.tool()
def workspace_read_file(path: str) -> str:
    """Reads the file content of a file in /workspace. You MUST read the 'workspace' skill instructions before calling this tool for the first time. NEVER run this tool without reading the 'workspace' skill!"""
    sb = sandbox_manager.get_or_create()
    res = sb.read_file(path)
    return res["content"] if res["status"] == "ok" else f"Error: {res['message']}"


@mcp.tool()
def workspace_list_files() -> str:
    """Shows the current file structure in /workspace. You MUST read the 'workspace' skill instructions before calling this tool for the first time. NEVER run this tool without reading the 'workspace' skill!"""
    sb = sandbox_manager.get_or_create()
    res = sb.list_files()
    return res["tree"] if res["status"] == "ok" else f"Error: {res['message']}"


@mcp.tool()
def workspace_export_folder() -> str:
    """Exports a folder containing files and/or other folders in /workspace to a place the user can access them. You MUST read the 'workspace' skill instructions before calling this tool for the first time. NEVER run this tool without reading the 'workspace' skill!"""
    sb = sandbox_manager.get_or_create()
    return sb.export_folder()


if __name__ == "__main__":
    mcp.run()
