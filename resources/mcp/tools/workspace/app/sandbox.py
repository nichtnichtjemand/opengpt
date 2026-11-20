import base64
import io
import pathlib
import subprocess
import tarfile
import uuid


class AgentSandbox:
    def __init__(self, memory_limit: str = "512m", cpus: str = "1.0"):
        self.container_name = f"ai-sandbox-{uuid.uuid4().hex}"
        self.memory_limit = memory_limit
        self.cpus = cpus

    def start(self):
        cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            self.container_name,
            "--network",
            "none",
            "--read-only",
            "--tmpfs",
            "/workspace:rw,exec,nosuid,size=256m,uid=1000,gid=1000",
            "--tmpfs",
            "/tmp:rw,exec,nosuid,size=64m",
            "--memory",
            self.memory_limit,
            "--memory-swap",
            self.memory_limit,
            "--cpus",
            self.cpus,
            "--pids-limit",
            "128",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "opengpt-sandbox",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"Docker start error:\n{proc.stderr}")

    def run_shell(self, command: str, timeout: float = 10.0) -> dict:
        cmd = [
            "docker",
            "exec",
            "-w",
            "/workspace",
            self.container_name,
            "bash",
            "-c",
            command,
        ]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout, check=False
            )
            return {
                "exit_code": proc.returncode,
                "stdout": proc.stdout[:15000],
                "stderr": proc.stderr[:15000],
            }
        except subprocess.TimeoutExpired:
            subprocess.run(
                ["docker", "exec", self.container_name, "pkill", "-9", "-u", "agent"],
                capture_output=True,
                check=False,
            )
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Timeout after {timeout}s.",
            }

    def write_file(self, rel_path: str, content: str) -> dict:
        b64_data = base64.b64encode(content.encode("utf-8")).decode("ascii")
        py_script = (
            "import base64, pathlib; "
            "ws = pathlib.Path('/workspace').resolve(); "
            f"target = (ws / {rel_path!r}).resolve(); "
            "assert str(target).startswith(str(ws)), 'Path traversal verboten'; "
            "target.parent.mkdir(parents=True, exist_ok=True); "
            f"target.write_bytes(base64.b64decode({b64_data!r}))"
        )
        res = self.run_shell(f"python3 -c {py_script!r}")
        return {
            "status": "ok" if res["exit_code"] == 0 else "error",
            "detail": res["stderr"],
        }

    def read_file(self, rel_path: str) -> dict:
        py_script = (
            "import pathlib; "
            "ws = pathlib.Path('/workspace').resolve(); "
            f"target = (ws / {rel_path!r}).resolve(); "
            "assert str(target).startswith(str(ws)) and target.is_file(), 'File not found'; "
            "print(target.read_text(encoding='utf-8'), end='')"
        )
        res = self.run_shell(f"python3 -c {py_script!r}")
        if res["exit_code"] == 0:
            return {"status": "ok", "content": res["stdout"]}
        return {"status": "error", "message": res["stderr"]}

    def edit_file(self, rel_path: str, old_text: str, new_text: str) -> dict:
        b64_old = base64.b64encode(old_text.encode("utf-8")).decode("ascii")
        b64_new = base64.b64encode(new_text.encode("utf-8")).decode("ascii")
        py_script = (
            "import base64, pathlib; "
            "ws = pathlib.Path('/workspace').resolve(); "
            f"target = (ws / {rel_path!r}).resolve(); "
            "assert str(target).startswith(str(ws)) and target.is_file(), 'File not found'; "
            "content = target.read_text(encoding='utf-8'); "
            f"old = base64.b64decode({b64_old!r}).decode('utf-8'); "
            f"new = base64.b64decode({b64_new!r}).decode('utf-8'); "
            "count = content.count(old); "
            "assert count == 1, f'old_text must be there exactly 1x (found: {count}x)'; "
            "target.write_text(content.replace(old, new, 1), encoding='utf-8')"
        )
        res = self.run_shell(f"python3 -c {py_script!r}")
        return {
            "status": "ok" if res["exit_code"] == 0 else "error",
            "detail": res["stderr"],
        }

    def list_files(self) -> dict:
        cmd = (
            "tree -a -I '.git|__pycache__|.pip_packages|.venv|node_modules' --noreport"
        )
        res = self.run_shell(cmd)
        if res["exit_code"] == 0:
            return {"status": "ok", "tree": res["stdout"]}
        return {"status": "error", "message": res["stderr"]}

    def export_folder(self, dest_dir: str = "./exported_workspace") -> str:
        target_path = pathlib.Path(dest_dir).resolve()
        target_path.mkdir(parents=True, exist_ok=True)

        cmd = [
            "docker",
            "exec",
            self.container_name,
            "tar",
            "-cf",
            "-",
            "-C",
            "/workspace",
            ".",
        ]
        proc = subprocess.run(cmd, capture_output=True, check=False)

        if proc.returncode != 0:
            return f"Export failed:\n{proc.stderr.decode('utf-8', errors='replace')}"

        with tarfile.open(fileobj=io.BytesIO(proc.stdout), mode="r:") as tar:
            tar.extractall(path=target_path, filter="data")

        return str("Exported successfully: " + target_path)

    def stop(self):
        subprocess.run(
            ["docker", "rm", "-f", self.container_name],
            capture_output=True,
            check=False,
        )

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
