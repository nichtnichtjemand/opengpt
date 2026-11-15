"""
OpenGPT - Complete local web interface in ONE Python file.
Run:
    python opengpt_all_in_one.py
The browser automatically opens:
    http://127.0.0.1:8000
Requirements:
    pip install fastapi uvicorn
aiapi and mcp_manager must also be available.
The MCP server is expected at:
    resources/mcp/main_server.py
Press Ctrl+C in the terminal to stop the server.
"""

import asyncio
import logging
import threading
import time
import webbrowser
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import aiapi
import mcp_manager

# ============================================================
# CONFIGURATION
# ============================================================
HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"
MODEL = "openai/gpt-oss-120b"
PROVIDER = "groq"
MCP_SERVER = "resources/mcp/main_server.py"
# ============================================================
# LOGGING
# ============================================================
logger = logging.getLogger("opengpt")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
# ============================================================
# GLOBAL STATE
# ============================================================
mcp = None
conversation = None
chat_lock = asyncio.Lock()
# ============================================================
# FRONTEND
# HTML + CSS + JAVASCRIPT
# ============================================================
HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#000000">
<title>OpenGPT</title>
<style>
/* =========================================================
   GENERAL
========================================================= */
* {
    box-sizing: border-box;
}
:root {
    color-scheme: dark;
    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
    background: #000;
    color: #ececec;
}
body {
    margin: 0;
    min-width: 320px;
    min-height: 100vh;
    background: #000;
}
button,
textarea {
    font: inherit;
}
.app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}
/* =========================================================
   HEADER
========================================================= */
.topbar {
    height: 56px;
    flex: 0 0 56px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 25px;
    border-bottom: 1px solid #171717;
    background: #000;
}
.brand {
    font-size: 14px;
    font-weight: 600;
}
.chevron {
    color: #aaa;
    margin-left: 5px;
    font-size: 16px;
}
.header-status {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #999;
    font-size: 12px;
}
.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #777;
}
.status-dot.online {
    background: #20a46b;
}
.status-dot.offline {
    background: #e05252;
}
/* =========================================================
   CHAT
========================================================= */
.chat {
    width: min(768px, calc(100% - 32px));
    margin: 0 auto;
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 34px 0 190px;
}
.welcome {
    margin: auto 0;
    text-align: center;
    transform: translateY(-30px);
}
.welcome h1 {
    font-size: 24px;
    font-weight: 500;
    margin: 0 0 10px;
    letter-spacing: -.5px;
}
.welcome p {
    margin: 0;
    color: #999;
    font-size: 14px;
}
.messages {
    display: flex;
    flex-direction: column;
    gap: 28px;
}
/* =========================================================
   MESSAGES
========================================================= */
.message {
    display: flex;
    flex-direction: column;
    max-width: 100%;
    animation: appear .18s ease-out;
}
.message.user {
    align-items: flex-end;
}
.message.assistant {
    align-items: flex-start;
}
.bubble {
    max-width: 88%;
    padding: 12px 17px;
    border-radius: 22px;
    font-size: 15px;
    line-height: 1.65;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}
.user .bubble {
    background: #2f2f2f;
    color: #f5f5f5;
}
.assistant .bubble {
    padding: 3px 0;
    background: transparent;
    color: #ececec;
    max-width: 100%;
}
.message-meta {
    color: #858585;
    font-size: 11px;
    margin-top: 7px;
    padding: 0 2px;
}
/* =========================================================
   TOOL LOG
========================================================= */
.tool-log {
    width: min(768px, 100%);
    margin: 0 auto 9px;
    max-height: 110px;
    overflow-y: auto;
}
.tool-entry {
    color: #aaa;
    font-size: 12px;
    padding: 7px 10px;
    border-left: 2px solid #555;
    background: #151515;
    border-radius: 0 7px 7px 0;
    margin-bottom: 6px;
    overflow-wrap: anywhere;
}
/* =========================================================
   COMPOSER
========================================================= */
.composer-area {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 14px 20px 24px;
    background: linear-gradient(
        180deg,
        transparent 0%,
        #000 17%
    );
}
.composer {
    width: min(768px, 100%);
    margin: 0 auto;
    background: #212121;
    border: 1px solid #303030;
    border-radius: 27px;
    padding: 14px 14px 10px 20px;
    transition:
        border-color .15s,
        background .15s;
}
.composer:focus-within {
    border-color: #454545;
    background: #232323;
}
textarea {
    display: block;
    width: 100%;
    resize: none;
    max-height: 200px;
    min-height: 28px;
    padding: 3px 0;
    border: 0;
    outline: 0;
    color: #f1f1f1;
    background: transparent;
    font-size: 15px;
    line-height: 1.5;
}
textarea::placeholder {
    color: #a1a1a1;
}
.composer-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    min-height: 35px;
    margin-top: 5px;
}
.hint {
    color: #777;
    font-size: 10px;
}
.send-button {
    display: grid;
    place-items: center;
    width: 36px;
    height: 36px;
    border: 0;
    border-radius: 50%;
    color: #111;
    background: #f5f5f5;
    cursor: pointer;
    transition:
        opacity .15s,
        transform .15s;
}
.send-button:hover {
    transform: scale(1.04);
}
.send-button:disabled {
    opacity: .45;
    cursor: default;
    transform: none;
}
.send-button svg {
    width: 19px;
    height: 19px;
    fill: none;
    stroke: currentColor;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
}
.disclaimer {
    text-align: center;
    color: #858585;
    font-size: 11px;
    margin: 10px 0 0;
}
/* =========================================================
   TYPING ANIMATION
========================================================= */
.typing {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 10px 0;
}
.typing span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #888;
    animation: pulse 1s infinite ease-in-out;
}
.typing span:nth-child(2) {
    animation-delay: .15s;
}
.typing span:nth-child(3) {
    animation-delay: .3s;
}
@keyframes pulse {
    0%, 60%, 100% {
        opacity: .35;
        transform: translateY(0);
    }
    30% {
        opacity: 1;
        transform: translateY(-3px);
    }
}
@keyframes appear {
    from {
        opacity: 0;
        transform: translateY(5px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
/* =========================================================
   RESPONSIVE
========================================================= */
@media (max-width: 600px) {
    .topbar {
        padding: 0 16px;
    }
    .chat {
        width: calc(100% - 28px);
        padding-top: 24px;
    }
    .bubble {
        max-width: 94%;
    }
    .composer-area {
        padding: 10px 10px 16px;
    }
    .hint {
        display: none;
    }
    .welcome h1 {
        font-size: 21px;
    }
}
</style>
</head>
<body>
<main class="app">
    <!-- HEADER -->
    <header class="topbar">
        <div class="brand">
            OpenGPT
            <span class="chevron">⌄</span>
        </div>
        <div class="header-status">
            <span
                class="status-dot"
                id="status-dot">
            </span>
            <span id="connection-label">
                Connecting ...
            </span>
        </div>
    </header>
    <!-- CHAT -->
    <section
        class="chat"
        id="chat"
        aria-live="polite">
        <div
            class="welcome"
            id="welcome">
            <h1>What's on your mind?</h1>
            <p>How can I help you?</p>
        </div>
        <div
            class="messages"
            id="messages">
        </div>
    </section>
    <!-- INPUT -->
    <footer class="composer-area">
        <div
            class="tool-log"
            id="tool-log"
            hidden>
        </div>
        <div class="composer">
            <textarea
                id="prompt"
                rows="1"
                placeholder="Message OpenGPT"
                aria-label="Enter a message">
            </textarea>
            <div class="composer-bottom">
                <span class="hint">
                    Enter to send · Shift + Enter for a new line
                </span>
                <button
                    id="send"
                    class="send-button"
                    aria-label="Send message"
                    title="Send">
                    <svg viewBox="0 0 24 24">
                        <path d="M12 19V5M5 12l7-7 7 7"/>
                    </svg>
                </button>
            </div>
        </div>
        <p class="disclaimer">
            OpenGPT can make mistakes. Check important information.
        </p>
    </footer>
</main>
<script>
/* =========================================================
   ELEMENTS
========================================================= */
const messages = document.getElementById("messages");
const welcome = document.getElementById("welcome");
const input = document.getElementById("prompt");
const send = document.getElementById("send");
const toolLog = document.getElementById("tool-log");
const statusLabel = document.getElementById("connection-label");
const statusDot = document.getElementById("status-dot");
let busy = false;
/* =========================================================
   CONNECTION STATUS
========================================================= */
function connection(online) {
    statusLabel.textContent = online
        ? "Connected locally"
        : "Server unavailable";
    statusDot.classList.toggle("online", online);
    statusDot.classList.toggle("offline", !online);
}
/* =========================================================
   SCROLLING
========================================================= */
function bottom() {
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: "smooth"
    });
}
/* =========================================================
   ADD MESSAGE
========================================================= */
function addMessage(role, text) {
    welcome.hidden = true;
    const article = document.createElement("article");
    article.className = "message " + role;
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;
    article.appendChild(bubble);
    messages.appendChild(article);
    bottom();
    return article;
}
/* =========================================================
   TYPING INDICATOR
========================================================= */
function typing() {
    const article = document.createElement("article");
    article.className = "message assistant";
    const dots = document.createElement("div");
    dots.className = "typing";
    dots.innerHTML = `
        <span></span>
        <span></span>
        <span></span>
    `;
    article.appendChild(dots);
    messages.appendChild(article);
    bottom();
    return article;
}
/* =========================================================
   TOOL EVENTS
========================================================= */
function showTools(items) {
    toolLog.replaceChildren();
    toolLog.hidden = !items.length;
    for (const item of items) {
        const line = document.createElement("div");
        line.className = "tool-entry";
        line.textContent = item;
        toolLog.appendChild(line);
    }
}
/* =========================================================
   INPUT RESIZING
========================================================= */
function resize() {
    input.style.height = "auto";
    input.style.height =
        Math.min(input.scrollHeight, 200) + "px";
}
/* =========================================================
   SEND MESSAGE
========================================================= */
async function sendMessage() {
    const message = input.value.trim();
    if (!message || busy) return;
    busy = true;
    send.disabled = true;
    input.value = "";
    resize();
    addMessage("user", message);
    const loading = typing();
    showTools([]);
    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(
                data.detail || "Unknown server error"
            );
        }
        loading.remove();
        showTools(data.tools || []);
        addMessage(
            "assistant",
            data.reply || "(No response received)"
        );
        connection(true);
    }
    catch (error) {
        loading.remove();
        addMessage(
            "assistant",
            "Error: " + error.message +
            "\n\nCheck whether the Python server is running."
        );
        connection(false);
    }
    finally {
        busy = false;
        send.disabled = false;
        input.focus();
    }
}
/* =========================================================
   EVENT LISTENERS
========================================================= */
send.addEventListener("click", sendMessage);
input.addEventListener("input", resize);
input.addEventListener("keydown", event => {
    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {
        event.preventDefault();
        sendMessage();
    }
});
/* =========================================================
   INITIAL CONNECTION CHECK
========================================================= */
fetch("/api/health")
    .then(response => {
        connection(response.ok);
    })
    .catch(() => {
        connection(false);
    });
</script>
</body>
</html>
"""


# ============================================================
# FASTAPI APPLICATION
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    global mcp, conversation
    logger.info("Connecting to MCP server...")
    mcp = mcp_manager.MCPManager(MCP_SERVER)
    await mcp.connect()
    conversation = aiapi.Conversation(mcp=mcp, provider=PROVIDER, model=MODEL)
    logger.info("OpenGPT Web UI started")
    try:
        yield
    finally:
        if mcp is not None:
            await mcp.close()
            logger.info("MCP connection closed")


app = FastAPI(title="OpenGPT Local", lifespan=lifespan)


# ============================================================
# REQUEST MODEL
# ============================================================
class ChatRequest(BaseModel):
    message: str


# ============================================================
# FRONTEND ROUTE
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def homepage():
    return HTML


# ============================================================
# HEALTH CHECK
# ============================================================
@app.get("/api/health")
async def health():
    return {"ok": conversation is not None}


# ============================================================
# CHAT API
# ============================================================
@app.post("/api/chat")
async def chat(request: ChatRequest):
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    if conversation is None:
        raise HTTPException(
            status_code=503, detail="The Python backend is not ready yet."
        )
    async with chat_lock:
        # Terminal commands from the original script.
        if message.startswith("!"):
            parts = message[1:].split()
            command = parts[0] if parts else ""
            args = parts[1:]
            if command in ("exit", "quit"):
                return {
                    "reply": "Press Ctrl+C in the terminal to stop the server.",
                    "tools": [],
                }
            if command == "model":
                if not args:
                    return {
                        "reply": f"Current model: {conversation.model}",
                        "tools": [],
                    }
                conversation.model = args[0]
                return {"reply": f"Model changed to: {conversation.model}", "tools": []}
            return {"reply": f"Unknown command: !{command}", "tools": []}
        # Collect MCP tool events.
        tool_events = []

        def ui_tool_status(tool_name: str, args: dict):
            entry = f"Tool: {tool_name} | Arguments: {args}"
            tool_events.append(entry)
            logger.info("[MCP-Tool] Execute '%s' (Arguments: %s)...", tool_name, args)

        try:
            reply = await conversation.send_message(
                message=message, on_tool_call=ui_tool_status
            )
            return {"reply": str(reply), "tools": tool_events}
        except Exception as exc:
            logger.exception("Error in conversation.send_message")
            raise HTTPException(status_code=500, detail=str(exc)) from exc


# ============================================================
# BROWSER
# ============================================================
def open_browser():
    time.sleep(1.3)
    webbrowser.open(URL)


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("Starting OpenGPT Web UI ...")
    print(f"Browser address: {URL}")
    print("Press Ctrl+C to stop the server.")
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host=HOST, port=PORT, reload=False, log_level="info")
