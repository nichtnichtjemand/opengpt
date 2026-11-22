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
# 1. Install uv (Linux and macOS here, ask AI for Windows)
curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. Create venv
uv sync
# 3. Run it
uv run main.py
```

Beim Start fragt OpenGPT die Google-, Groq- und Tavily-API-Schlüssel über
`input()` ab. Die Schlüssel werden nur zur Laufzeit in der Prozessumgebung
gespeichert und nicht in den Build oder in eine `.env`-Datei geschrieben.

## Standalone-Build erstellen
```bash
uv sync
uv run pyinstaller --clean --noconfirm opengpt.spec
```

Das eigenständige Programm liegt unter:
```text
dist/opengpt/opengpt
```

Beim Start vom Build muss weiterhin der ganze Ordner `dist/opengpt`
mitgeführt werden. Die gebündelten Ressourcen liegen unter
`dist/opengpt/_internal/resources`.

## Contributing
Feel free to create a PR if you have things to change! I'm happy for each contribution.