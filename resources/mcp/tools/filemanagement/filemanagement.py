import os
from pathlib import Path

current = Path(__file__).resolve()
working = (current / "../../../../working").resolve()


def get_files():
    return os.listdir(working)


def get_file_content(path):
    return (working / path).resolve().read_text(encoding="utf-8")


def write_file_content(path, content):
    if not (working / path).resolve().is_relative_to(working):
        raise ValueError("Can't go to a higher directory!")
    (working / path).resolve().write_text(content)
