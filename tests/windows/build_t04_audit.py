"""Isolated T04 builds; run on Windows first, then under WSL with --linux.

No production sources are modified. Output must be new. Build logs and source
hashes belong to the evidence, not to the installed bin/ directory.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = (ROOT / 'UPSTREAM_BASELINE').read_text().strip()
TOOLS = 'qpDstat convertf transpose qp3Pop qp4diff qpF4ratio qpAdm qpfstats qpWave qpDpart qpdslow'.split()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(args, cwd, log, env=None):
    log.write(json.dumps([str(x) for x in args]) + '\n')
    log.flush()
    result = subprocess.run([str(x) for x in args], cwd=cwd, env=env,
                            stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'build failed ({result.returncode}); see {log.name}')


def windows(output, toolchain):
    output.mkdir(parents=True, exist_ok=False)
    snapshot = output / 'snapshot'
    snapshot.mkdir()
    shutil.copytree(ROOT / 'src', snapshot / 'src',
                    ignore=shutil.ignore_patterns('.windows', '*.o', '*.a', '__pycache__'))
    for name in ('perlsrc',):
        shutil.copytree(ROOT / name, snapshot / name)
    shutil.copyfile(ROOT / 'UPSTREAM_BASELINE', snapshot / 'UPSTREAM_BASELINE')
    shutil.copytree(ROOT / 'src/.windows/argp', snapshot / 'src/.windows/argp')
    shutil.copytree(ROOT / 'tests/windows', snapshot / 'tests/windows',
                    ignore=shutil.ignore_patterns('__pycache__'))
    manifest = dict(upstream=UPSTREAM,
                    head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                    initial_status=subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True),
                    sources={str(p.relative_to(snapshot)).replace('\\', '/'): sha(p)
                             for p in (snapshot / 'src').rglob('*')
                             if p.suffix in ('.c', '.h') and '.windows' not in p.parts})
    (output / 'snapshot.json').write_text(json.dumps(manifest, indent=2) + '\n')
    env = dict(os.environ, PATH=str(toolchain) + os.pathsep + os.environ['PATH'])
    with (output / 'build-windows.log').open('w') as log:
        command(['python', snapshot / 'src/build_windows.py', '--toolchain', toolchain,
                 '--tools', *TOOLS], snapshot, log, env)
    print(snapshot / 'bin')


def linux(output,coverage=False,linux_root=None,skip_pristine=False):
    snapshot = output / 'snapshot'
    names = ('coverage',) if coverage else (('linux','asan') if skip_pristine else ('pristine','linux','asan'))
    roots = {name: (linux_root / name if linux_root else Path.home() / ('admixtools-t04-' + name))
             for name in names}
    for name, target in roots.items():
        if target.exists():
            raise FileExistsError(target)
        target.mkdir(parents=True)
        if name == 'pristine':
            data = subprocess.check_output(['git', 'archive', UPSTREAM, 'src'], cwd=ROOT)
            with tarfile.open(fileobj=io.BytesIO(data)) as archive:
                archive.extractall(target, filter='data')
        else:
            shutil.copytree(snapshot / 'src', target / 'src',
                            ignore=shutil.ignore_patterns('.windows', '*.o', '*.a', '__pycache__'))
        flags = '-std=gnu11 -ffp-contract=off -fno-fast-math'
        ldflags = ''
        if name == 'asan':
            flags += ' -fsanitize=address,undefined -fno-omit-frame-pointer -g -fno-pie'
            ldflags = '-fsanitize=address,undefined -no-pie'
        if name == 'coverage':
            flags += ' --coverage -fprofile-abs-path'
            ldflags = '--coverage'
        with (output / ('build-' + name + '.log')).open('w') as log:
            command(['make', '-B', 'CFLAGS=' + flags], target / 'src/nicksrc', log)
            command(['make', '-B', '-j2', *TOOLS, 'CFLAGS=' + flags,
                     'LDFLAGS=' + ldflags], target / 'src', log)
        record = dict(root=str(target), flags=flags, link_flags=ldflags,
                      executables={t: sha(target / 'src' / t) for t in TOOLS},
                      sources={str(p.relative_to(target)): sha(p) for p in (target / 'src').rglob('*')
                               if p.suffix in ('.c', '.h')})
        if name == 'pristine':
            record['upstream_mismatches'] = [p for p, h in record['sources'].items()
                if hashlib.sha256(subprocess.check_output(['git', 'show', UPSTREAM + ':' + p], cwd=ROOT)).hexdigest() != h]
        else:
            expected = json.loads((output / 'snapshot.json').read_text())['sources']
            record['snapshot_mismatches'] = [p for p, h in record['sources'].items() if expected.get(p) != h]
        (output / ('build-' + name + '.json')).write_text(json.dumps(record, indent=2) + '\n')
        print(name, target, flush=True)
    environment = subprocess.check_output(['sh', '-c',
        'uname -a; gcc --version; pkg-config --modversion gsl; '
        'dpkg-query -W libgsl28 libopenblas0-pthread zlib1g; '
        'ldd "$HOME/admixtools-t04-linux/src/qpDstat"'], text=True)
    (output / 'linux-environment.txt').write_text(environment)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--toolchain', type=Path, default=Path('C:/msys64/ucrt64/bin'))
    parser.add_argument('--linux', action='store_true')
    parser.add_argument('--coverage', action='store_true')
    parser.add_argument('--linux-root', type=Path, help='new Linux build root; preserves prior reference builds')
    parser.add_argument('--skip-pristine', action='store_true', help='reuse the retained pinned pristine reference')
    args = parser.parse_args()
    if args.linux:
        linux(args.output.resolve(),args.coverage,args.linux_root,args.skip_pristine)
    else:
        windows(args.output.resolve(), args.toolchain.resolve())
