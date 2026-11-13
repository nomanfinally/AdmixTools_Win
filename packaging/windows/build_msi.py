"""Package the existing native x64 build. Does not compile or install AdmixTools.

Generated payloads/tool caches live under ignored .build/; only MSI, ZIP,
sanitized manifests and checksums go to the requested distribution directory.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import urllib.request
import uuid
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
WIX_VERSION = '6.0.2'
WIX_URL = 'https://github.com/wixtoolset/wix/releases/download/v6.0.2/wix-cli-x64.msi'
WIX_SHA256 = 'a8a5cc7443353cef3ab900c60cd7a3a5ee601746319d104ac7b12ad0ced2345c'
NAMESPACE = uuid.UUID('4c8c3a55-8e71-4a1a-b50d-139223c85cab')
XMLNS = 'http://wixtoolset.org/schemas/v4/wxs'
ET.register_namespace('', XMLNS)
PROFILE = re.compile(rb'(?i)(?:[a-z]:[/\\]+Users[/\\]+|/mnt/[a-z]/Users/)([^/\\\s\x00"\x27<>;]+)')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, cwd=None):
    subprocess.run([str(x) for x in command], cwd=cwd or ROOT, check=True)


def pe_x64(path):
    with path.open('rb') as stream:
        assert stream.read(2) == b'MZ', f'Not a PE executable: {path.name}'
        stream.seek(0x3c)
        offset = struct.unpack('<I', stream.read(4))[0]
        stream.seek(offset)
        assert stream.read(4) == b'PE\0\0' and stream.read(2) == b'\x64\x86', f'Not x64: {path.name}'


def privacy_check(path):
    for match in PROFILE.finditer(path.read_bytes()):
        if match[1].lower() not in (b'username', b'user', b'public', b'default', b'example'):
            raise ValueError('Personal profile path in payload: ' + path.name)


def prepare_wix(cache, requested):
    cache.mkdir(parents=True, exist_ok=True)
    if requested:
        wix = requested.resolve()
    else:
        cache.mkdir(parents=True, exist_ok=True)
        msi = cache / 'wix-cli-x64.msi'
        if not msi.exists():
            print('Downloading pinned WiX CLI build tools...', flush=True)
            urllib.request.urlretrieve(WIX_URL, msi)
        if sha(msi) != WIX_SHA256:
            raise ValueError('WiX CLI checksum mismatch; tool not executed')
        extracted = cache / 'wix'
        candidates = list(extracted.rglob('wix.exe')) if extracted.exists() else []
        if not candidates:
            print('Extracting build tools without registering a system installation...', flush=True)
            run(['msiexec.exe', '/a', msi, '/qn', 'REBOOT=ReallySuppress', 'TARGETDIR=' + str(extracted),
                 '/l*v', str(cache / 'extract.log')])
            candidates = list(extracted.rglob('wix.exe'))
        if len(candidates) != 1:
            raise ValueError('Cannot identify the extracted WiX CLI')
        wix = candidates[0]
    version = subprocess.check_output([str(wix), '--version'], text=True).strip()
    if not version.startswith(WIX_VERSION + '+') and version != WIX_VERSION:
        raise ValueError('Use pinned WiX ' + WIX_VERSION)
    extension = cache / '.wix/extensions/WixToolset.UI.wixext' / WIX_VERSION / 'wixext6/WixToolset.UI.wixext.dll'
    if not extension.exists():
        run([wix, 'extension', 'add', 'WixToolset.UI.wixext/' + WIX_VERSION], cwd=cache)
    if not extension.exists():
        raise ValueError('WiX UI extension not found after preparation')
    return wix, extension


def bundle_renderers(staged, runtime):
    """Bundle native dot/PS/PDF support, including its DLL closure and notices."""
    tools = ['dot.exe', 'gswin64c.exe', 'libgvplugin_core-8.dll',
             'libgvplugin_dot_layout-8.dll', 'libgvplugin_pango-8.dll']
    pending = list(tools)
    copied = set()
    objdump = runtime / 'bin/objdump.exe'
    system = Path(os.environ['SystemRoot']) / 'System32'
    while pending:
        name = pending.pop()
        if name.lower() in copied: continue
        source = runtime / 'bin' / name
        if not source.is_file():
            raise ValueError('Missing native renderer dependency: ' + name + '; install UCRT64 graphviz/ghostscript first')
        pe_x64(source)
        target = staged / 'bin' / name
        if target.exists() and sha(target) != sha(source):
            raise ValueError('Conflicting scientific/renderer DLL: ' + name)
        shutil.copy2(source, target)
        copied.add(name.lower())
        imports = subprocess.check_output([str(objdump), '-p', str(source)], text=True)
        for dependency in re.findall(r'DLL Name:\s*(\S+)', imports):
            if (runtime / 'bin' / dependency).is_file(): pending.append(dependency)
            elif not (system / dependency).is_file() and not dependency.lower().startswith(('api-ms-', 'ext-ms-')):
                raise ValueError('Unresolved renderer dependency: ' + dependency)
    for directory in ('share/ghostscript', 'etc/fonts'):
        source = runtime / directory
        if source.exists(): shutil.copytree(source, staged / directory)
    # Keep all local runtime notices; build-only tools are not in the payload.
    shutil.copytree(runtime / 'share/licenses', staged / 'bin/licenses', dirs_exist_ok=True)
    license_file = HERE / '.build/tools/graphviz-COPYING.txt'
    if not license_file.exists():
        urllib.request.urlretrieve('https://gitlab.com/graphviz/graphviz/-/raw/16.1.0/COPYING', license_file)
    license_destination = staged / 'bin/licenses/graphviz'
    license_destination.mkdir(exist_ok=True)
    shutil.copy2(license_file, license_destination / 'COPYING')
    env = dict(os.environ, PATH=str(staged / 'bin') + os.pathsep + str(system),
               GVBINDIR=str(staged / 'bin'))
    subprocess.run([str(staged / 'bin/dot.exe'), '-c'], cwd=staged / 'bin', env=env, check=True)
    return sorted(copied)


def payload(binary_dir, work, version, runtime):
    metadata = json.loads((binary_dir / 'windows-build.json').read_text())
    spec = importlib.util.spec_from_file_location('windows_build_inventory', ROOT / 'src/build_windows.py')
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    _, rules = build.inventory()
    expected = set(rules) - set(build.BLOCKED)
    if set(metadata['executables']) != expected:
        raise ValueError('Package a complete supported build; selected-target metadata is insufficient')
    for relative, digest in metadata['source_sha256'].items():
        if sha(ROOT / 'src' / relative) != digest:
            raise ValueError('Native source changed since build: ' + relative + '; rebuild first')
    for relative, digest in metadata['script_sha256'].items():
        if sha(ROOT / 'src/script' / relative) != digest:
            raise ValueError('Helper source changed since build: ' + relative)
    staged = work / 'payload'
    staged.mkdir()
    (staged / 'bin').mkdir()
    for name in sorted(expected):
        source = binary_dir / (name + '.exe')
        pe_x64(source)
        shutil.copy2(source, staged / 'bin' / source.name)
    for name, digest in metadata['runtime_sha256'].items():
        source = binary_dir / name
        if sha(source) != digest:
            raise ValueError('Runtime DLL hash mismatch: ' + name)
        pe_x64(source)
        shutil.copy2(source, staged / 'bin' / name)
    # The offline installer ships native commands, not interpreter-dependent
    # Perl/R/Python workflows. Those stay available through the source checkout.
    for directory in ('licenses',):
        if not (binary_dir / directory).is_dir():
            raise ValueError('Missing payload directory: ' + directory)
        shutil.copytree(binary_dir / directory, staged / 'bin' / directory,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    renderers = bundle_renderers(staged, runtime)
    docs = staged / 'docs'
    docs.mkdir()
    for source in ROOT.glob('README*'):
        if source.is_file() and '.personal.' not in source.name:
            shutil.copy2(source, docs / source.name)
    shutil.copy2(ROOT / 'src/LICENSE.txt', docs / 'ADMIXTOOLS-LICENSE.txt')
    shutil.copy2(ROOT / 'src/nicksrc/LICENSE.txt', docs / 'NICKLIB-LICENSE.txt')
    shutil.copy2(HERE / 'INSTALLED-README.txt', staged / 'README.txt')
    info = {key: metadata[key] for key in ('upstream_commit', 'working_head', 'compiler',
             'executables', 'runtime_sha256', 'source_sha256', 'script_sha256', 'optimization',
             'link_flags', 'zlib_header_version', 'manifest_sha256')}
    info.update(package_version=version, architecture='x64', install_scope='current-user',
                distribution='development', linux_parity_certified=False, bundled_renderer_files=renderers,
                interpreter_scripts_included=False)
    (staged / 'bin/windows-build.json').write_text(json.dumps(info, indent=2) + '\n', encoding='utf-8')
    files = {str(p.relative_to(staged)).replace('\\', '/'): sha(p) for p in staged.rglob('*') if p.is_file()}
    for relative in files: privacy_check(staged / relative)
    return staged, files, info


def author_payload(staged, output):
    def sub(parent, tag, **attributes):
        return ET.SubElement(parent, '{' + XMLNS + '}' + tag, attributes)
    document = ET.Element('{' + XMLNS + '}Wix')
    fragment = sub(document, 'Fragment')
    directory = sub(fragment, 'DirectoryRef', Id='INSTALLFOLDER')
    group = sub(fragment, 'ComponentGroup', Id='Payload')

    def add(folder, element):
        files = sorted(p for p in folder.iterdir() if p.is_file())
        for index, file in enumerate(files):
            relative = file.relative_to(staged).as_posix()
            ident = 'F' + hashlib.sha256(relative.encode()).hexdigest()[:24]
            component = sub(element, 'Component', Id='C' + ident,
                            Guid=str(uuid.uuid5(NAMESPACE, relative)), Bitness='always64')
            sub(component, 'File', Id=ident, Source=str(file), Name=file.name)
            sub(component, 'RegistryValue', Root='HKCU', Key='Software\\AdmixToolsWindows\\Components',
                Name=ident, Value='1', Type='string', KeyPath='yes')
            if index == 0 and folder != staged:
                sub(component, 'RemoveFolder', Id='R' + ident, On='uninstall')
            sub(group, 'ComponentRef', Id='C' + ident)
        for child in sorted(p for p in folder.iterdir() if p.is_dir()):
            relative = child.relative_to(staged).as_posix()
            element_child = sub(element, 'Directory', Id='D' + hashlib.sha256(relative.encode()).hexdigest()[:24], Name=child.name)
            add(child, element_child)
    add(staged, directory)
    ET.indent(document)
    ET.ElementTree(document).write(output, encoding='utf-8', xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='8.1.0')
    parser.add_argument('--bin', type=Path, default=ROOT / 'bin')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    parser.add_argument('--wix', type=Path)
    parser.add_argument('--runtime-root', type=Path, default=Path('C:/msys64/ucrt64'))
    args = parser.parse_args()
    if os.name != 'nt': parser.error('Build MSI packages on native Windows')
    parts = args.version.split('.')
    if len(parts) != 3 or not all(p.isdigit() for p in parts) or any(int(p) > limit for p, limit in zip(parts, (255, 255, 65535))):
        parser.error('MSI version must be major.minor.build within 255.255.65535')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    name = 'AdmixTools-' + args.version + '-windows-x64'
    targets = [output / (name + suffix) for suffix in ('.msi', '.zip', '.manifest.json', '.sha256')]
    if any(p.exists() for p in targets):
        parser.error('Output package already exists; choose a fresh output directory or a new version')
    work = HERE / '.build' / (name + '-' + uuid.uuid4().hex[:12])
    work.mkdir(parents=True)
    wix, extension = prepare_wix(HERE / '.build/tools', args.wix)
    staged, files, metadata = payload(args.bin.resolve(), work, args.version, args.runtime_root.resolve())
    art = work / 'artwork'
    run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', HERE / 'branding.ps1',
         '-OutputDirectory', art])
    # The original upstream license, faithfully escaped as RTF.
    license_text = (ROOT / 'src/LICENSE.txt').read_text()
    escaped = license_text.replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}').replace('\n', '\\par\n')
    license_rtf = work / 'License.rtf'
    license_rtf.write_text('{\\rtf1\\ansi\\deff0{\\fonttbl{\\f0 Segoe UI;}}\\f0\\fs18\n' + escaped + '}', encoding='ascii')
    author_payload(staged, work / 'Payload.wxs')
    print('Building MSI for ' + str(len(metadata['executables'])) + ' native tools...', flush=True)
    run([wix, 'build', HERE / 'Product.wxs', work / 'Payload.wxs', '-arch', 'x64',
         '-ext', extension, '-d', 'ProductVersion=' + args.version, '-d', 'LicenseRtf=' + str(license_rtf),
         '-d', 'Artwork=' + str(art), '-loc', HERE / 'Product.en-us.wxl',
         '-pdbtype', 'none', '-intermediatefolder', work / 'objects', '-out', targets[0]])
    with zipfile.ZipFile(targets[1], 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in sorted(files): archive.write(staged / relative, name + '/' + relative)
    manifest = {'schema': 1, 'product': 'AdmixTools Windows', 'version': args.version,
                'development_build': True, 'signed': False, 'architecture': 'x64', 'scope': 'current-user',
                'wix_version': WIX_VERSION, 'payload_sha256': files, 'native_build': metadata,
                'artifacts_sha256': {p.name: sha(p) for p in targets[:2]}}
    targets[2].write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    targets[3].write_text(''.join(sha(p) + '  ' + p.name + '\n' for p in targets[:3]), encoding='ascii')
    print('Built ' + str(targets[0]), flush=True)
    print('Portable ZIP, sanitized manifest and SHA256 checksums are beside it.', flush=True)


if __name__ == '__main__':
    main()
