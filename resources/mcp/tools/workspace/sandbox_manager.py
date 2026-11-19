import atexit
import logging
import threading
import time

from .app.sandbox import AgentSandbox

logger = logging.getLogger("openai.sandboxmanager")


class SandboxManager:
    def __init__(self, idle_timeout_seconds: int = 1800):
        self._sessions: dict[str, dict] = {}
        self._lock = threading.Lock()
        self.idle_timeout = idle_timeout_seconds

        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

        atexit.register(self.shutdown_all)

    def get_or_create(self, session_id: str) -> AgentSandbox:
        with self._lock:
            now = time.time()
            if session_id in self._sessions:
                entry = self._sessions[session_id]
                entry["last_used"] = now
                return entry["sandbox"]

            sb = AgentSandbox()
            sb.start()
            self._sessions[session_id] = {"sandbox": sb, "last_used": now}
            return sb

    def stop_session(self, session_id: str):
        with self._lock:
            entry = self._sessions.pop(session_id, None)
        if entry:
            entry["sandbox"].stop()

    def _cleanup_loop(self):
        while True:
            time.sleep(60)
            now = time.time()
            expired_ids = []

            with self._lock:
                for sid, entry in self._sessions.items():
                    if now - entry["last_used"] > self.idle_timeout:
                        expired_ids.append(sid)

            for sid in expired_ids:
                logger.info(f"Clean old session: {sid}")
                self.stop_session(sid)

    def shutdown_all(self):
        with self._lock:
            all_ids = list(self._sessions.keys())
        for sid in all_ids:
            self.stop_session(sid)


sandbox_manager = SandboxManager(idle_timeout_seconds=1800)
