# storage.py

def ensure_file(path, header_line):
    try:
        with open(path, "r"):
            pass
    except OSError:
        with open(path, "w") as f:
            f.write(header_line + "\n")

def append_lines(path, lines):
    if not lines:
        return
    with open(path, "a") as f:
        for line in lines:
            f.write(line)

def append_line(path, line):
    with open(path, "a") as f:
        f.write(line)
