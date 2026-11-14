from datetime import date
from pathlib import Path

VERSION = 1.0


class MStorageParseError(Exception):
    def __init__(self, message: str, line=None):
        self.line = line
        full_message = f"Line {line}: {message}" if line is not None else message
        super().__init__(full_message)


def get_file(lines=False):
    filepath = Path(__file__).resolve().parent / "memory.mstorage"

    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()
        if lines:
            return content.splitlines()
        return content


def get_version():
    content = get_file(True)[0]
    if not content.startswith("version:"):
        raise MStorageParseError("No version found")
    return content[8:]


def get_layout():
    content = get_file(True)[1]
    if not content.startswith("layout:"):
        raise MStorageParseError("No layout found")
    layout = content[7:]
    return layout.split(sep=",")


def reset_file():
    filepath = Path(__file__).resolve().parent / "memory.mstorage"

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(f"version:{VERSION}\nlayout:\n")
    return "Reset successful"


def get_blocks():
    content = get_file(True)[2:]
    current_block = None
    blocks = {}
    for line_num, line in enumerate(content):
        if line.startswith("START:"):
            block = line[6:]
            if current_block != None:
                raise MStorageParseError("Block started while active block", line_num)
            if block in blocks:
                raise MStorageParseError("Block already exists", line_num)
            current_block = block
            blocks[current_block] = {}

        elif line.startswith("END:"):
            block = line[4:]
            if current_block == None:
                raise MStorageParseError("Block ended while no active block", line_num)
            if block != current_block:
                raise MStorageParseError("Wrong Block ended", line_num)
            current_block = None

        elif line.startswith("text:"):
            text = line[5:]
            if current_block == None:
                raise MStorageParseError("Text started while no active block", line_num)
            blocks[current_block]["text"] = text

        elif line.startswith("date:"):
            date = line[5:]
            if current_block == None:
                raise MStorageParseError("Date started while no active block", line_num)
            blocks[current_block]["date"] = date

    if current_block != None:
        raise MStorageParseError("File ended with open block")

    return blocks


def edit_block(block, text):
    content = get_file(True)
    get_blocks()  # Validating Layout
    done = False

    for line_num, line in enumerate(content):
        if line == f"START:{block}":
            for line_num2, line2 in enumerate(content[line_num:], start=line_num):
                if line2.startswith("END:"):
                    done = True
                    break
                elif line2.startswith("text:"):
                    content[line_num2] = f"text:{text}"
                elif line2.startswith("date:"):
                    content[line_num2] = f"date:{date.today().isoformat()}"
        if done:
            break

    filepath = Path(__file__).resolve().parent / "memory.mstorage"

    with open(filepath, "w", encoding="utf-8") as file:
        file.write("\n".join(content))
    return "Edited block successful"


def add_block(block, text):
    blocks = get_blocks()
    if block in blocks:
        raise ValueError("Block already exists")
    part = f"\nSTART:{block}\ndate:{date.today().isoformat()}\ntext:{text}\nEND:{block}"

    filepath = Path(__file__).resolve().parent / "memory.mstorage"
    content = get_file() + part
    content = content.splitlines()
    for line_num, line in enumerate(content):
        if line.startswith("layout:"):
            if line == "layout:":
                content[line_num] = line + block
            else:
                content[line_num] = line + "," + block
    content = "\n".join(content)

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content)
    return "Added block successful"


def delete_block(block):
    blocks = get_blocks()
    if block not in blocks:
        raise ValueError("Block doesn't exist")

    layout = get_layout()
    if block in layout:
        layout.remove(block)

    content = get_file(True)
    new_content = []
    skip = False

    for line in content:
        if line.startswith("layout:"):
            new_content.append(f"layout:{','.join(layout)}")
        elif line == f"START:{block}":
            skip = True
        elif line == f"END:{block}":
            skip = False
        elif not skip:
            new_content.append(line)

    filepath = Path(__file__).resolve().parent / "memory.mstorage"
    with open(filepath, "w", encoding="utf-8") as file:
        file.write("\n".join(new_content))
    return "Deleted successful"
