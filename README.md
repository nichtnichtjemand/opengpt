# OpenGPT
A custom Chatbot interface, made in Python!
## Features
- Chat with Gemini or Groq API
- Local MCP Servers
- Web search
- Secret (it is "Apple", ask it for it and it will run the MCP Tool to get it from there)
- Memory: Custom File Format `.mstorage`, custom Parser, it can remember things over different sessions
- Run Python code: As safe as possible, it shouldn't be able to write destructive code
- Skills: You can put skills in Anthropic's format in resources/skills and it can use it
## How to run it
```bash
# 1. Install uv (Linux here, ask AI for Windows or macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. Create venv
uv sync
# 3. Duplicate .env.example and fill it with your values
# 4. Build Dockerfile
cd resources/mcp/tools/workspace
sudo docker build -t opengpt-sandbox ./sandbox
# 5. Run it
uv run main.py
```

## Build
```bash
uv run pyinstaller --clean --noconfirm opengpt.spec
./dist/opengpt/opengpt
```

The `dist/opengpt` folder must stay together because it contains the bundled
`resources` files used by the MCP server and the application.

## Why I made this
For fun! I really like AI chatbots like ChatGPT, but I dont like these bad free limits so I made it better.
<img width="1263" height="499" alt="Bildschirmfoto vom 2026-11-15 20-13-36" src="https://github.com/user-attachments/assets/4265f973-d2bd-4aca-9a80-0252c7ef99be" />


## Contributing
Feel free to create a PR if you have things to change! I'm happy for each contribution.
