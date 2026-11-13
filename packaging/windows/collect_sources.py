"""Collect matching source packages beside an existing Windows distribution.

Run on the build machine before publishing binaries. Uses the selected MSYS2
package database, checks installed runtime bytes against the payload manifest,
and archives tracked project sources plus the actual patched argp sources.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def fields(path):
    result = {}
    for block in path.read_text(encoding='utf-8').split('\n\n'):
        lines = block.splitlines()
        if lines and lines[0].startswith('%'):
            result[lines[0].strip('%')] = lines[1:]
    return result


def packages(runtime, manifest):
    wanted = {name.removeprefix('bin/'): digest for name, digest in manifest['payload_sha256'].items()
              if name.startswith('bin/') and name.count('/') == 1 and name.lower().endswith(('.dll', '.exe'))
              and name.removeprefix('bin/').removesuffix('.exe') not in manifest['native_build']['executables']}
    owners = {}
    result = {}
    database = runtime.parent / 'var/lib/pacman/local'
    for directory in database.iterdir():
        listing = directory / 'files'
        if not listing.is_file(): continue
        owned = {line.removeprefix('ucrt64/bin/') for line in listing.read_text(encoding='utf-8').splitlines()
                 if line.startswith('ucrt64/bin/')}
        selected = owned & wanted.keys()
        if not selected: continue
        record = fields(directory / 'desc')
        base, version = record['BASE'][0], record['VERSION'][0]
        key = base + '-' + version
        entry = result.setdefault(key, {'base': base, 'version': version, 'packages': [], 'files': [],
            'archive': key + '.src.tar.zst',
            'url': 'https://repo.msys2.org/mingw/sources/' + key + '.src.tar.zst'})
        entry['packages'].append(record['NAME'][0])
        for name in sorted(selected):
            if sha(runtime / 'bin' / name) != wanted[name]:
                raise ValueError('Installed dependency differs from packaged binary: ' + name)
            owners[name] = key
            entry['files'].append(name)
    if set(owners) != set(wanted):
        raise ValueError('Cannot identify runtime source packages: ' + ', '.join(sorted(set(wanted) - set(owners))))
    return sorted(result.values(), key=lambda entry: entry['archive'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--runtime-root', type=Path, default=Path('C:/msys64/ucrt64'))
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    parser.add_argument('--download-only', action='store_true')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    entries = packages(args.runtime_root.resolve(), manifest)
    cache = HERE / '.build/source-packages'
    cache.mkdir(parents=True, exist_ok=True)

    def download(entry):
        target = cache / entry['archive']
        if not target.exists():
            temporary = target.with_suffix(target.suffix + '.partial')
            print('Downloading source ' + entry['archive'], flush=True)
            request = urllib.request.Request(entry['url'], headers={'User-Agent': 'AdmixTools-source-distribution'})
            with urllib.request.urlopen(request, timeout=120) as response, temporary.open('wb') as stream:
                while block := response.read(1024 * 1024): stream.write(block)
            temporary.replace(target)
        if target.stat().st_size < 100: raise ValueError('Empty source package: ' + target.name)
        with target.open('rb') as stream:
            if stream.read(4) != b'\x28\xb5\x2f\xfd': raise ValueError('Not a zstd source archive: ' + target.name)
        entry['sha256'] = sha(target)
        entry['size_bytes'] = target.stat().st_size

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(download, entries))
    print('Matching source packages: ' + str(len(entries)), flush=True)
    if args.download_only: return

    if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=ROOT).strip():
        raise ValueError('Commit tracked project changes before archiving release sources')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    argp = ROOT / 'src/.windows/argp-source'
    revision = subprocess.check_output(['git', '-C', str(argp), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != '8ded2bc942740b5d291e450af661c5090dc3ca38':
        raise ValueError('Unexpected argp source revision')
    sources = {}
    for directory, prefix in ((ROOT, 'AdmixTools/'), (argp, 'argp-standalone/')):
        names = subprocess.check_output(['git', '-C', str(directory), 'ls-files', '-z']).decode('utf-8').split('\0')
        for name in filter(None, names):
            path = directory / name
            if not path.is_file(): raise ValueError('Missing tracked source: ' + name)
            sources[prefix + name] = path
    # Scan project text and nested JSON without echoing any private match.
    from build_msi import privacy_check
    for path in sources.values(): privacy_check(path)
    args.output.mkdir(parents=True, exist_ok=True)
    stem = 'AdmixTools-' + manifest['version'] + '-windows-x64-sources'
    target = args.output / (stem + '.zip')
    if target.exists(): raise ValueError('Source output already exists; refusing replacement')
    source_record = {'schema': 1, 'project_commit': commit,
        'upstream_commit': manifest['native_build']['upstream_commit'],
        'argp_commit': revision, 'argp_patch': 'prepare-windows.ps1 GNU diagnostic quoting adaptation',
        'source_file_sha256': {name: sha(path) for name, path in sorted(sources.items())},
        'msys2_source_packages': entries}
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, path in sorted(sources.items()): archive.write(path, name)
        for entry in entries:
            archive.write(cache / entry['archive'], 'dependencies/' + entry['archive'], compress_type=zipfile.ZIP_STORED)
        archive.writestr('SOURCE-MANIFEST.json', json.dumps(source_record, indent=2) + '\n')
        archive.writestr('README.txt',
            'Matching sources for the accompanying AdmixTools Windows binaries.\n'
            'AdmixTools/ contains the tagged project, including Windows build instructions.\n'
            'argp-standalone/ contains the actual pinned GNU argument-parser sources with the documented diagnostic patch.\n'
            'dependencies/ contains MSYS2 source packages: upstream sources, patches, licenses and PKGBUILD recipes.\n'
            'Use MSYS2 makepkg-mingw for those recipes; see https://www.msys2.org/wiki/Creating-Packages/.\n'
            'SOURCE-MANIFEST.json records versions, origin URLs, hashes and the matching project commit.\n')
    checksum = sha(target) + '  ' + target.name + '\n'
    (args.output / (stem + '.sha256')).write_text(checksum, encoding='ascii')
    print('Created ' + target.name + ' (' + str(target.stat().st_size) + ' bytes)', flush=True)


if __name__ == '__main__': main()
