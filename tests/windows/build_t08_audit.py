"""Isolated T08 builds; keep pinned-pristine source entirely unmodified."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

import build_t04_audit as build

build.TOOLS = 'qpGraph qpfstats qpreroot convertf transpose'.split()


def linux(output, root, coverage):
    names = ('coverage',) if coverage else ('pristine', 'linux', 'asan')
    for name in names:
        target = root / name
        target.mkdir(parents=True, exist_ok=False)
        if name == 'pristine':
            import io
            import tarfile
            data = subprocess.check_output(['git', 'archive', build.UPSTREAM, 'src'], cwd=build.ROOT)
            with tarfile.open(fileobj=io.BytesIO(data)) as archive:
                archive.extractall(target, filter='data')
        else:
            shutil.copytree(output/'snapshot/src', target/'src',
                            ignore=shutil.ignore_patterns('.windows', '*.o', '*.a', '__pycache__'))
        flags = '-std=gnu11 -ffp-contract=off -fno-fast-math'
        link = ''
        if name == 'asan':
            flags += ' -fsanitize=address,undefined -fno-omit-frame-pointer -g -fno-pie'
            link = '-fsanitize=address,undefined -no-pie'
        if coverage:
            flags += ' --coverage -fprofile-abs-path'
            link = '--coverage'
        with (output/('build-'+name+'.log')).open('w') as log:
            build.command(['make', '-B', 'CFLAGS='+flags], target/'src/nicksrc', log)
            build.command(['make', '-B', '-j2', *build.TOOLS, 'CFLAGS='+flags,
                           'LDFLAGS='+link, 'LDLIBS=-lnick'], target/'src', log)
        sources = {str(p.relative_to(target)): build.sha(p) for p in (target/'src').rglob('*')
                   if p.suffix in ('.c', '.h')}
        expected = (json.loads((output/'snapshot.json').read_text())['sources']
                    if name != 'pristine' else None)
        mismatches = [p for p, digest in sources.items() if digest !=
                      (expected[p] if expected is not None else __import__('hashlib').sha256(
                          subprocess.check_output(['git', 'show', build.UPSTREAM+':'+p], cwd=build.ROOT)).hexdigest())]
        record = dict(upstream=build.UPSTREAM, root=str(target), flags=flags, link_flags=link,
                      sources=sources, source_mismatches=mismatches,
                      executables={t:build.sha(target/'src'/t) for t in build.TOOLS})
        (output/('build-'+name+'.json')).write_text(json.dumps(record, indent=2)+'\n')
        assert not mismatches, mismatches
        print(name, target, flush=True)
    commands = [['uname', '-a'], ['gcc', '--version'], ['gcc', '-dumpmachine'],
                ['pkg-config', '--modversion', 'gsl'],
                ['dpkg-query', '-W', 'libgsl28', 'libopenblas0-pthread', 'zlib1g'],
                ['ldd', str(root/('coverage' if coverage else 'linux')/'src/qpGraph')]]
    (output/'linux-environment.txt').write_text(''.join(
        repr(c)+'\n'+subprocess.check_output(c,text=True) for c in commands))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--toolchain', type=Path, default=Path('C:/msys64/ucrt64/bin'))
    p.add_argument('--linux-root', type=Path)
    p.add_argument('--coverage', action='store_true')
    a = p.parse_args()
    if a.linux_root:
        linux(a.output.resolve(), a.linux_root.resolve(), a.coverage)
    else:
        build.windows(a.output.resolve(), a.toolchain.resolve())

