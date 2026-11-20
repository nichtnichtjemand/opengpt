---
name: workspace
description: Isolated Linux and Python development environment (/workspace) for creating, editing, and executing files, scripts, apps, and games. MANDATORY: Read and use this skill IMMEDIATELY whenever the user asks to create, build, or write code, scripts, HTML pages, games, or applications (e.g., "Create a game", "Write a script"). Never just output full code blocks in the chat when the user asks you to build something; always load this skill first to write the actual files to /workspace.
---

# Workspace Sandbox Skill

You have access to a persistent, isolated Linux container environment rooted at `/workspace`. All files, installed packages, and Git repositories remain intact across tool calls within the current session.

## Available Tools & When to Use Them

1. **`workspace_list_files`**
   - **Purpose:** Displays the current directory and file tree inside `/workspace`.
   - **When to use:** Always run this at the start of a task to inspect existing files and project layout.

2. **`workspace_read_file`**
   - **Purpose:** Reads the complete content of a file.
   - **When to use:** Before editing any existing file, to verify its exact content, indentation, and context.

3. **`workspace_write_file`**
   - **Purpose:** Creates a new file (including any missing parent directories) or completely overwrites an existing file.
   - **When to use:** For new files or full file rewrites. Prefer this over shell commands like `cat << 'EOF'` to avoid shell-escaping bugs.

4. **`workspace_edit_file`**
   - **Purpose:** Replaces a unique block of text (`old_text` -> `new_text`) inside an existing file.
   - **When to use:** For targeted modifications to existing files. Ensure `old_text` matches verbatim (including whitespace/indentation) and occurs strictly once in the file.

5. **`workspace_run_shell`**
   - **Purpose:** Executes arbitrary Bash commands inside `/workspace`.
   - **Pre-installed tools:** `python3`, `pytest`, `uv`, `pip`, `ruff`, `git`, `ripgrep` (`rg`), `jq`, `curl`, `wget`, `tree`, `zip`/`unzip`.

5. **`workspace_export_folder`**
   - **Purpose:** Exports a folder in `/workspace` to a directory the user can access.
   - **When to use:** For giving the user a folder containing files he wished for so he can read and use them.

## Exporting files to the user

The user does not have direct access to the `/workspace` directory. To share files with the user, you must manually export them using the `workspace_export_folder` tool. It exports it to a normal folder, NOT a `zip`!

* **Path requirement:** Provide a folder path relative to `/workspace` (exporting the root `/workspace` folder itself is not allowed).
* **Example:** If the user asks you to code a game, create a dedicated subfolder (e.g., `/workspace/my-game`), save all game files inside it, and then export `my-game`.
* **Answer:** You should include `Created successfully: ` plus the path at the end of your message for a button to open it getting rendered, for example: `Exported successfully: /home/user/OpenGPT/resources/exported/project`. You ALWAYS need to write this at the end of a turn when you exported files.


## Best Practices & Rules

- **Use relative paths only:** Always reference paths relative to `/workspace` (e.g., `src/main.py` instead of `/workspace/src/main.py`). Any path traversal outside `/workspace` is blocked.
- **Respect the read-only root filesystem:** The container's root filesystem is mounted `--read-only`. Store all generated files exclusively inside `/workspace` (or temporarily in `/tmp`).
- **Installing packages:** If you need additional Python libraries, install them normally using `pip install <package>` or `uv pip install <package>`—the environment is pre-configured to install packages automatically into `/workspace/.pip_packages`.
- **Test and verify autonomously:** Whenever you write or modify code, run a verification step via `workspace_run_shell` (e.g., `pytest`, `python3 <file>`, or `ruff check .`) to catch and fix syntax or runtime errors before replying to the user.
- **Keep command output concise:** Avoid commands that dump massive log files or scan the entire root filesystem. Use targeted commands like `rg "pattern"` or `head -n 50`.
- **Do not ask the user for specific file names or paths:** Whenever you think you need one of these tools, do not ask the user if they want a specific file name or path. Since it is only readable for you, it is completly irrelevant for them.
