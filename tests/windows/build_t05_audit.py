"""Isolated qp3Pop audit builds, including pristine and sanitizer references.

Reuses the recorded T04 build mechanism; never overwrites installed binaries.
"""
import argparse
from pathlib import Path
import subprocess
import build_t04_audit as build

build.TOOLS = 'qp3Pop convertf transpose qpDstat qpF4ratio qp4diff qpBound'.split()

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--toolchain', type=Path)
    p.add_argument('--linux', action='store_true')
    p.add_argument('--linux-root', type=Path)
    p.add_argument('--coverage', action='store_true')
    p.add_argument('--related', action='store_true', help='also build affected shared consumers')
    p.add_argument('--skip-pristine', action='store_true', help='retain the pinned original reference')
    a = p.parse_args()
    if a.related:
        build.TOOLS += 'qpAdm qpfstats qpWave qpDpart qpdslow qpff3base qpfit qpfmv'.split()
    if a.linux:
        build.linux(a.output.resolve(), a.coverage, a.linux_root, a.skip_pristine)
        # The reused T04 helper's final ldd line names its historical tree.
        # Replace that environment record with this audit's actual target.
        root=a.linux_root.resolve() if a.linux_root else Path.home()/'admixtools-t05'
        binary=root/('coverage' if a.coverage else 'linux')/'src/qp3Pop'
        commands=[['uname','-a'],['gcc','--version'],['gcc','-dumpmachine'],
                  ['pkg-config','--modversion','gsl'],
                  ['dpkg-query','-W','libgsl28','libopenblas0-pthread','zlib1g'],['ldd',str(binary)]]
        record=''.join('$ '+repr(c)+'\n'+subprocess.check_output(c,text=True) for c in commands)
        (a.output/'linux-environment.txt').write_text(record)
    else:
        build.windows(a.output.resolve(), a.toolchain.resolve())
