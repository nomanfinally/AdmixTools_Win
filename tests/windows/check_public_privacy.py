"""Reject machine-specific profile paths in tracked public text.

Run from any directory. The personal guide and recovery files must be ignored.
This is a privacy check, not a scientific parity test or a general secret scanner.
"""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PROFILE = re.compile(r"(?i)(?:[a-z]:[/\\]+Users[/\\]+|/mnt/[a-z]/Users/)([^/\\\s\"'<>;]+)")
HOST = re.compile(r"\b(?:DESKTOP|LAPTOP)-[A-Z0-9]{5,}\b", re.I)
GENERIC = {'username', 'user', 'public', 'default', 'example', 'yourname', 'your-username'}


def main():
    result = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True, check=True)
    failures = []
    for relative in filter(None, result.stdout.decode('utf-8').split('\0')):
        path = ROOT / relative
        if not path.is_file():
            continue
        data = path.read_bytes()
        if b'\0' in data[:8000]:
            continue
        text = data.decode('utf-8', errors='replace')
        if any(match[1].lower() not in GENERIC for match in PROFILE.finditer(text)) or HOST.search(text):
            # Print file names only; never echo the private matched value.
            failures.append(relative)
    for relative in ('README.WINDOWS.personal.md', '.private/privacy-check-placeholder'):
        ignored = subprocess.run(['git', 'check-ignore', '--quiet', '--', relative], cwd=ROOT)
        if ignored.returncode != 0:
            failures.append(relative + ': missing ignore protection or tracked personal file')
    if failures:
        print('Public privacy check failed in:')
        print('\n'.join(failures))
        return 1
    print('Public privacy check passed; personal guide and recovery directory are ignored.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
