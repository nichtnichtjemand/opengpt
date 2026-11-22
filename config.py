import os
from pathlib import Path

from dotenv import load_dotenv


def get_config_dir() -> Path:
    base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "opengpt"


def get_env_path() -> Path:
    return get_config_dir() / ".env"


def load_api_keys() -> None:
    local_env = Path(__file__).resolve().parent / ".env"
    if not local_env.is_file():
        local_env = Path.cwd() / ".env"

    if local_env.is_file():
        load_dotenv(local_env, override=True)

    env_path = get_env_path()
    if env_path.is_file():
        load_dotenv(env_path, override=False)


def get_api_key(name: str) -> str:
    load_api_keys()
    return (os.getenv(name) or "").strip()


def save_api_key(name: str, value: str) -> None:
    value = value.strip()
    if not value:
        raise ValueError("API key cannot be empty.")

    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    env_path = get_env_path()

    values: dict[str, str] = {}
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, existing = line.split("=", 1)
                values[key.strip()] = existing.strip()

    values[name] = value
    env_path.write_text(
        "".join(f"{key}={item}\n" for key, item in values.items()),
        encoding="utf-8",
    )
    os.chmod(env_path, 0o600)
    os.environ[name] = value
