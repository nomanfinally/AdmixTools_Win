"""Isolated T06 builds: native Windows, pinned pristine Linux, port and sanitizers."""
import argparse
from pathlib import Path
import subprocess
import build_t04_audit as build

build.TOOLS = 'qpF4ratio convertf transpose qp4diff qpDstat qp3Pop'.split()

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--toolchain', type=Path)
    p.add_argument('--linux', action='store_true')
    p.add_argument('--linux-root', type=Path)
    p.add_argument('--coverage', action='store_true')
    p.add_argument('--related', action='store_true')
    p.add_argument('--skip-pristine', action='store_true')
    a = p.parse_args()
    if a.related:
        build.TOOLS += 'qpAdm qpfstats qpWave qpfit qpdslow'.split()
    if a.linux:
        if not a.linux_root:p.error('--linux-root is required for isolated T06 builds')
        build.linux(a.output.resolve(), a.coverage, a.linux_root, a.skip_pristine)
        binary = a.linux_root.resolve()/('coverage' if a.coverage else 'linux')/'src/qpF4ratio'
        commands = [['uname', '-a'], ['gcc', '--version'], ['gcc', '-dumpmachine'],
                    ['pkg-config', '--modversion', 'gsl'],
                    ['dpkg-query', '-W', 'libgsl28', 'libopenblas0-pthread', 'zlib1g'], ['ldd', str(binary)]]
        record = ''.join('$ '+repr(c)+'\n'+subprocess.check_output(c, text=True) for c in commands)
        (a.output/'linux-environment.txt').write_text(record)
    else:
        build.windows(a.output.resolve(), a.toolchain.resolve())
