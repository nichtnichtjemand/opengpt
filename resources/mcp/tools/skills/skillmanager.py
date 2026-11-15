from pathlib import Path


def get_skills():
    current = Path(__file__).resolve().parent
    path = (current / "../../../skills").resolve()

    skills = []

    for file in path.glob("*/SKILL.md"):
        if file.is_file():
            print(f"Found: {file}")
            content = file.read_text("utf-8").splitlines()
            name = content[1][6:]
            description = content[2][13:]
            skills.append([name, description])
    return skills


def get_skill(name):
    current = Path(__file__).resolve().parent
    path = (current / "../../../skills" / name).resolve()

    file = next(path.glob("SKILL.md"))
    return file.read_text("utf-8")
