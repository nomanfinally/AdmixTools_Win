"""Small Windows adaptations shared by the upstream Python helpers."""
import os
from pathlib import Path


def native_executable(path):
    path = Path(path)
    if os.name == 'nt' and path.suffix.lower() != '.exe':
        candidate = Path(str(path) + '.exe')
        if candidate.is_file():
            return candidate
    return path


def parameter_path(path):
    value = str(path)
    return f'"{value}"' if os.name == 'nt' else value
