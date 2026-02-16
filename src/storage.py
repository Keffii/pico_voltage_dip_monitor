# storage.py

import os

def ensure_file(path, header_line):
    """Create file with header if it doesn't exist."""
    try:
        with open(path, "r"):
            pass
    except OSError:
        try:
            with open(path, "w") as f:
                f.write(header_line + "\n")
        except OSError as e:
            print(f"ERROR: Failed to create {path}: {e}")
            raise

def append_lines(path, lines):
    """Append multiple lines to file. Returns number of lines written."""
    if not lines:
        return 0
    try:
        with open(path, "a") as f:
            for line in lines:
                f.write(line)
        return len(lines)
    except OSError as e:
        print(f"ERROR: Failed to append to {path}: {e}")
        return 0

def append_line(path, line):
    """Append single line to file. Returns True on success."""
    try:
        with open(path, "a") as f:
            f.write(line)
        return True
    except OSError as e:
        print(f"ERROR: Failed to append to {path}: {e}")
        return False

def get_file_size(path):
    """Get file size in bytes."""
    try:
        stat = os.stat(path)
        return stat[6]
    except OSError:
        return 0

def get_free_space():
    """Get free flash space in bytes."""
    try:
        stat = os.statvfs('/')
        return stat[0] * stat[3]  # block size * free blocks
    except (OSError, AttributeError):
        return 0

def truncate_to_last_n_lines(path, n_lines, header_line):
    """Keep only last N lines of file (circular buffer). Preserves header."""
    try:
        # Read all lines
        with open(path, 'r') as f:
            lines = f.readlines()
        
        # Keep header + last N data lines
        if len(lines) <= n_lines + 1:  # +1 for header
            return  # File is small enough
        
        kept_lines = [header_line + '\n'] + lines[-(n_lines):]
        
        # Rewrite file
        with open(path, 'w') as f:
            f.writelines(kept_lines)
        
        print(f"Truncated {path} to last {n_lines} lines")
    except OSError as e:
        print(f"ERROR: Failed to truncate {path}: {e}")

def check_file_size_limit(path, max_size_bytes, header_line, max_lines=None):
    """Check if file exceeds limits and truncate if needed."""
    size = get_file_size(path)
    
    if max_size_bytes and size > max_size_bytes:
        if max_lines:
            truncate_to_last_n_lines(path, max_lines, header_line)
        else:
            print(f"WARNING: {path} exceeds {max_size_bytes} bytes (currently {size})")
    
    return size