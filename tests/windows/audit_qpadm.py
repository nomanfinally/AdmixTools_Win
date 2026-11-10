"""T01 mode, input, helper and failure audit. No scientific tolerances.

Run --bin DIR --output NEW_DIR on each OS; --compare DIR DIR writes exact diffs.
--select REGEX restricts diagnostic reruns (including an ASan Linux build).
Every process has a timeout, separate working directory and retained raw streams.
"""
import argparse
import difflib
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import random
import shutil
import subprocess
import sys

import compatibility
import parity


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(binary_dir, output, selection):
    output.mkdir(parents=True, exist_ok=False)
    common = output / 'fixtures'
    parity.fixtures(common)
    # Independent-population random fixtures exercise rank fitting but often
    # trigger upstream's large-SE fallback. Correlated right populations below
    # give an informative mixture and exercise the actual Bayesian sampler.
    rng = random.Random(8107)
    signal = []
    for _ in range(2200):
        base, drift, extra = rng.uniform(.3, .7), rng.choice((-.22, .22)), rng.uniform(-.1, .1)
        a, b = base + drift, base - drift
        frequencies = (base, a, b, base + extra, .6*a + .4*b,
                       a + extra, b + extra, base + .5*drift, base - .5*drift)
        signal.append(''.join(str(int(rng.random() < f) + int(rng.random() < f))
                              for f in frequencies for _ in range(6)) + '\n')
    (common / 'signal.geno').write_text(''.join(signal), newline='\n')
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
               OPENBLAS_CORETYPE='NEHALEM', LC_ALL='C', STMP='tmp',
               ASAN_OPTIONS='detect_leaks=0:abort_on_error=1')
    env['PATH'] = str(binary_dir) + os.pathsep + env.get('PATH', '')
    manifest = {'binary_dir': str(binary_dir), 'platform': sys.platform,
                'cases': {}, 'executables': {}, 'environment': {
                    key: env[key] for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS',
                                             'OPENBLAS_CORETYPE', 'LC_ALL', 'STMP', 'ASAN_OPTIONS')}}

    def executable(tool):
        return binary_dir / (tool + ('.exe' if os.name == 'nt' else ''))

    for tool in ('qpAdm', 'qpfstats', 'convertf', 'transpose'):
        manifest['executables'][tool] = sha(executable(tool))

    def invoke(name, tool, args, work, expected='success', selected_env=None, selected_exe=None):
        exe = selected_exe or executable(tool)
        try:
            proc = subprocess.run([exe.name, *args], executable=str(exe), cwd=work,
                                  env=selected_env or env, capture_output=True, timeout=40)
            entry = {'returncode': proc.returncode, 'arguments': args, 'expected': expected}
            for stream in ('stdout', 'stderr'):
                (output / f'{name}.{stream}').write_bytes(getattr(proc, stream))
        except subprocess.TimeoutExpired as error:
            entry = {'timeout': True, 'arguments': args, 'expected': expected}
            for stream in ('stdout', 'stderr'):
                (output / f'{name}.{stream}').write_bytes(getattr(error, stream) or b'')
        entry['files'] = {str(p.relative_to(work)): sha(p) for p in work.rglob('*')
                          if p.is_file() and (p.name in ('model.mv', 'saved.fstats', 'helper.log')
                                              or 'tmp' in p.relative_to(work).parts
                                              or re.match(r'^(fsx|ppp|pops|tpar|fslog|genotmp)\.[0-9]+', p.name))}
        manifest['cases'][name] = entry
        # Save after every case, so an interrupted audit retains its evidence.
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(f'{name}: {entry.get("returncode", "TIMEOUT")}', flush=True)
        return entry

    # Shared scientific files used by direct, cached and compressed qpAdm modes.
    invoke('prepare-packed', 'convertf', ['-p', 'par.convertf'], common)
    invoke('prepare-transpose', 'transpose', ['output.geno', 'input.tgeno'], common)
    invoke('prepare-fstats', 'qpfstats', ['-p', 'par.qpfstats'], common)
    (common / 'par.signal-fstats').write_text((common / 'par.qpfstats').read_text().replace(
        'input.geno', 'signal.geno').replace('output.fstats', 'signal.fstats'))
    invoke('prepare-signal-fstats', 'qpfstats', ['-p', 'par.signal-fstats'], common)
    if re.search(selection, 'plink-ped') or re.search(selection, 'plink-bed'):
        for kind, output_format, extension in (('ped', 'PED', 'ped'), ('bed', 'PACKEDPED', 'bed')):
            text = (common / 'par.convertf').read_text().replace('PACKEDANCESTRYMAP', output_format)
            text = text.replace('output.geno', f'plink.{extension}').replace('output.snp', f'plink-{kind}.pedsnp').replace('output.ind', f'plink-{kind}.pedind')
            (common / f'par.plink-{kind}').write_text(text + 'outputgroup: YES\n')
            invoke('prepare-plink-' + kind, 'convertf', ['-p', f'par.plink-{kind}'], common)
            (common / f'plink.{extension}.gz').write_bytes(gzip.compress((common / f'plink.{extension}').read_bytes(), mtime=0))
    rows = (common / 'input.geno').read_text().splitlines()
    ids = [line.split()[0] for line in (common / 'input.ind').read_text().splitlines()]
    (common / 'input.ancestry').write_text(''.join(
        f'rs{snp:05d} {individual} {rows[snp][index]}\n'
        for snp in range(len(rows)) for index, individual in enumerate(ids)), newline='\n')
    for filename in ('input.geno', 'output.geno', 'input.tgeno', 'input.ancestry'):
        payload = (common / filename).read_bytes()
        split = len(payload) // 2 + 1
        (common / (filename + '.gz')).write_bytes(
            gzip.compress(payload[:split], mtime=0) + gzip.compress(payload[split:], mtime=0))

    base = (common / 'par.qpAdm').read_text()
    modes = {
        'default': '', 'explicit-defaults': 'allsnps: NO\ninbreed: NO\n',
        'details-no': 'details: NO\n', 'hires': 'hires: YES\n',
        'hiprec': 'hiprec_covar: YES\n', 'longsummary': 'longsummary: YES\n',
        'eigen': 'eigenanalysis: YES\n', 'diagonly': 'diagonly: YES\n',
        'oracle-no': 'oracle: NO\n', 'diagplus': 'oracle: NO\ndiagplus: .0001\n',
        'diagvarplus': 'oracle: NO\ndiagvarplus: .000001\n',
        'newmode': 'newmode: YES\nmctrials: 200\n',
        'positive': 'newmode: YES\npositive_coeffs: YES\nmctrials: 200\n',
        'oldmode-no': 'oldmode: NO\nmctrials: 200\n',
        'newmode-no': 'oldmode: NO\nnewmode: NO\n',
        'ratio': 'doratio: YES\nnumboot: 50\n', 'inbreed': 'inbreed: YES\n',
        'fancy-no': 'fancyf4: NO\n', 'popsizelimit': 'popsizelimit: 3\n',
        'chrom': 'chrom: 1\n', 'nochrom': 'nochrom: 1\n',
        'positions': 'chrom: 1\nlopos: 100000\nhipos: 850000\n',
        'gfromp': 'gfromp: YES\n', 'mv': 'mvname: model.mv\n',
        'xchrom': 'chrom: 23\n', 'xchrom-auto': 'chrom: 23\nallsnps: YES\ninbreed: NO\nnumboot: 5\n',
        'auto': 'allsnps: YES\nnumboot: 50\n',
        'auto-inbreed-no': 'allsnps: YES\ninbreed: NO\nnumboot: 50\n',
        'auto-alias': 'useallsnps: YES\nnumboot: 50\n',
        'auto-basepop': 'allsnps: YES\nbasepop: C\nnumboot: 50\n',
        'auto-keep': 'allsnps: YES\nkeeptmp: YES\nnumboot: 50\n',
        'auto-save': 'allsnps: YES\nfstatsoutname: saved.fstats\nfstatslog: helper.log\nnumboot: 50\n',
        'auto-long-temp': 'allsnps: YES\nnumboot: 5\n',
        'cached': 'fstatsname: output.fstats\nnumboot: 50\n',
        'cached-new': 'fstatsname: output.fstats\nnewmode: YES\nmctrials: 200\nnumboot: 50\n',
        'bayes': 'newmode: YES\nmctrials: 200\n',
        'bayes-positive': 'newmode: YES\npositive_coeffs: YES\nmctrials: 200\n',
        'bayes-cached': 'fstatsname: signal.fstats\nnewmode: YES\nmctrials: 200\nnumboot: 50\n',
        'bayes-zero': 'newmode: YES\nmctrials: 0\n',
        'cached-ratio': 'fstatsname: output.fstats\ndoratio: YES\nnumboot: 50\n',
        'cached-hires': 'fstatsname: output.fstats\nhires: YES\nnumboot: 50\n',
        'cached-one-boot': 'fstatsname: output.fstats\nnumboot: 1\n',
        'cached-zero-boot': 'fstatsname: output.fstats\nnumboot: 0\n',
        'cached-negative-boot': 'fstatsname: output.fstats\nnumboot: -1\n',
        'zero-trials': 'newmode: YES\nmctrials: 0\n',
        'target-only': '', 'single-source': '', 'single-auto': 'allsnps: YES\nnumboot: 5\n',
        'ratio-single': 'doratio: YES\nnumboot: 5\n',
        'empty-left': '', 'empty-right': '', 'single-right': '',
        'overlap': '', 'duplicate-left': '', 'missing-pop': '',
        'missing-geno': '', 'truncated-geno': '', 'missing-par': '',
        'empty-value': '', 'empty-int': '', 'empty-dbl': '',
        'too-many-pars': '', 'include-overflow': '', 'include': '',
        'include-duplicate': '', 'max-pars': '',
        'bom': '', 'utf16': '', 'crlf': '', 'embedded-nul': '',
        'no-data': 'chrom: 99\n', 'zero-blocksize': '',
        'all-missing': '', 'constant': '', 'malformed-fstats': 'fstatsname: bad.fstats\n',
        'fstats-noeff': 'fstatsname: bad.fstats\nnumboot: 5\n',
        'fstats-tight-eff': 'fstatsname: bad.fstats\nnumboot: 5\n',
        'fstats-many-pops': 'fstatsname: bad.fstats\n',
        'fstats-empty': 'fstatsname: bad.fstats\n',
        'three-source': '', 'four-source-long': 'longsummary: YES\n',
        'instem': '', 'high-seed': '', 'missing-calls': '',
        'bad-snp': 'badsnpname: bad.snps\n', 'blocks': 'blockname: blocks.txt\n',
        'long-line': '', 'include-cycle': '', 'unclosed-quote': '',
        'gzip-bad-data': '', 'packed-truncated': '',
        'three-hires': 'hires: YES\n',
        'auto-fail': 'allsnps: YES\nchrom: 99\nnumboot: 5\n',
        'plink-ped': '', 'plink-bed': '', 'plink-ped-gzip': '', 'plink-bed-gzip': '',
        'plink-ped-auto': 'allsnps: YES\nnumboot: 5\n',
        'plink-bed-auto': 'allsnps: YES\nnumboot: 5\n',
        'plink-ped-gzip-auto': 'allsnps: YES\nnumboot: 5\n',
        'plink-bed-gzip-auto': 'allsnps: YES\nnumboot: 5\n',
    }
    for kind in ('output.geno', 'input.tgeno', 'input.ancestry', 'input.geno.gz',
                 'output.geno.gz', 'input.tgeno.gz', 'input.ancestry.gz'):
        modes['format-' + kind] = ''
    if os.name == 'nt':
        modes.update({'win-paths': 'allsnps: YES\nnumboot: 5\n',
                      'win-hash-path': 'allsnps: YES\nnumboot: 5\n',
                      'win-long-log': 'allsnps: YES\nnumboot: 5\n',
                      'win-unicode': '', 'win-unicode-helper': 'allsnps: YES\nnumboot: 5\n',
                      'win-no-tempdir': 'allsnps: YES\ntmpdir: absent-directory\n',
                      'win-copy-failure': 'allsnps: YES\nnumboot: 5\nfstatsoutname: absent-directory/saved.fstats\n',
                      'win-missing-helper': 'allsnps: YES\n'})
    else:
        modes.update({'unix-full-mv': 'mvname: /dev/full\n',
                      'unix-full-copy': 'allsnps: YES\nnumboot: 5\nfstatsoutname: /dev/full\n',
                      'unix-full-fstats': '', 'unix-full-fstats-standard': ''})

    for name, extra in modes.items():
        if not re.search(selection, name):
            continue
        work = output / ('work ' + name)
        shutil.copytree(common, work)
        (work / 'tmp').mkdir()
        text, expected, selected_exe = base + extra, 'success', None
        if name.startswith('plink-'):
            kind = name.split('-')[1]
            source = f'plink.{kind}' + ('.gz' if '-gzip' in name else '')
            text = text.replace('input.geno', source).replace('input.snp', f'plink-{kind}.pedsnp').replace('input.ind', f'plink-{kind}.pedind')
        if name.startswith('bayes'): text = text.replace('input.geno', 'signal.geno')
        if name.startswith('xchrom'):
            snps = (work / 'input.snp').read_text().splitlines()
            (work / 'input.snp').write_text('\n'.join(
                re.sub(r'^(\S+) 1 ', r'\1 23 ', line) for line in snps) + '\n')
            inds = (work / 'input.ind').read_text().splitlines()
            (work / 'input.ind').write_text('\n'.join(line.replace(' U ', ' M ' if i % 2 else ' F ')
                                                    for i, line in enumerate(inds)) + '\n')
        if name == 'bayes-zero': expected = 'investigate'
        if name in ('hires', 'cached-hires', 'three-hires', 'target-only', 'single-right',
                    'cached-zero-boot', 'cached-negative-boot', 'zero-trials', 'ratio-single',
                    'empty-value', 'empty-int', 'empty-dbl', 'too-many-pars', 'include-overflow',
                    'embedded-nul', 'utf16', 'zero-blocksize', 'constant', 'win-hash-path', 'win-unicode'):
            expected = 'investigate'
        if name in ('empty-left', 'empty-right', 'missing-pop', 'missing-geno', 'missing-par',
                    'truncated-geno', 'overlap', 'duplicate-left', 'no-data', 'all-missing',
                    'malformed-fstats', 'auto-fail', 'win-missing-helper', 'win-no-tempdir', 'win-copy-failure'):
            expected = 'failure'
        if name.startswith('unix-full'): expected = 'failure'
        if name.startswith('unix-full-fstats'):
            text = (work / 'par.qpfstats').read_text().replace('output.fstats', '/dev/full')
            if name.endswith('standard'): text = text.replace('hires: YES', 'hires: NO')
        if name == 'target-only': (work / 'left').write_text('X\n')
        if name in ('single-source', 'single-auto', 'ratio-single'): (work / 'left').write_text('X\nA\n')
        if name in ('three-source', 'three-hires'): (work / 'left').write_text('X\nA\nB\nC\n')
        if name == 'four-source-long':
            (work / 'left').write_text('X\nA\nB\nC\nR4\n')
            (work / 'right').write_text('Out\nR1\nR2\nR3\nR5\n')
            (work / 'input.ind').write_text((work / 'input.ind').read_text() + ''.join(
                f'R5{i} U R5\n' for i in range(6)))
            (work / 'input.geno').write_text(''.join(row + row[-6:] + '\n' for row in rows))
        if name == 'empty-left': (work / 'left').write_bytes(b'')
        if name == 'empty-right': (work / 'right').write_bytes(b'')
        if name == 'single-right': (work / 'left').write_text('X\nA\n'); (work / 'right').write_text('Out\n')
        if name == 'overlap': (work / 'left').write_text('X\nOut\nB\n')
        if name == 'duplicate-left': (work / 'left').write_text('X\nA\nA\n')
        if name == 'missing-pop': (work / 'left').write_text('X\nA\nAbsent\n')
        if name == 'missing-geno': (work / 'input.geno').unlink()
        if name == 'truncated-geno': (work / 'input.geno').write_bytes(b'0\n')
        if name == 'empty-value': text = text.replace('genotypename: input.geno', 'genotypename:')
        if name == 'empty-int': text = text.replace('seed: 77', 'seed:')
        if name == 'empty-dbl': text = text.replace('blgsize: .005', 'blgsize:')
        if name == 'zero-blocksize': text = text.replace('blgsize: .005', 'blgsize: 0')
        if name == 'instem':
            text = re.sub(r'^(genotypename|snpname|indivname):.*\n', '', text, flags=re.M) + 'instem: input\n'
        if name == 'high-seed': text = text.replace('seed: 77', 'seed: -2147483647')
        if name == 'missing-calls':
            geno = bytearray((work / 'input.geno').read_bytes())
            for index in range(0, len(geno), 71):
                if geno[index] != 10: geno[index] = 57
            (work / 'input.geno').write_bytes(geno)
        if name == 'bad-snp': (work / 'bad.snps').write_text('rs00001\nrs00005\nrs00101\n')
        if name == 'blocks':
            (work / 'blocks.txt').write_text(''.join(f'rs{i:05d} {i // 20}\n' for i in range(2200)))
        if name == 'long-line': text += 'unused: ' + 'x' * 6000 + '\n'; expected = 'failure'
        if name == 'include-cycle': text += '+++ audit.par\n'; expected = 'failure'
        if name == 'unclosed-quote': text = text.replace('input.geno', '"input.geno'); expected = 'investigate'
        if name == 'packed-truncated':
            (work / 'output.geno').write_bytes((work / 'output.geno').read_bytes()[:60])
            text = text.replace('input.geno', 'output.geno'); expected = 'failure'
        if name == 'gzip-bad-data':
            (work / 'broken.gz').write_bytes(gzip.compress(b'not genotype data\n', mtime=0))
            text = text.replace('input.geno', 'broken.gz'); expected = 'failure'
        if name == 'all-missing': (work / 'input.geno').write_text(('9' * 54 + '\n') * 2200)
        if name == 'constant': (work / 'input.geno').write_text(('0' * 54 + '\n') * 2200)
        if name == 'malformed-fstats': (work / 'bad.fstats').write_text('not fstats\n')
        if name == 'fstats-empty': (work / 'bad.fstats').write_bytes(b''); expected = 'failure'
        if name in ('fstats-noeff', 'fstats-tight-eff'):
            fstats = (work / 'output.fstats').read_text()
            if name == 'fstats-noeff': fstats = re.sub(r' effblocks:.*\n', '\n', fstats)
            else: fstats = fstats.replace('effblocks:   ', 'effblocks:')
            (work / 'bad.fstats').write_text(fstats)
        if name == 'fstats-many-pops':
            header = (work / 'output.fstats').read_text().splitlines()[0]
            (work / 'bad.fstats').write_text(header + '\n' + ''.join(f'P{i} P{i} 1\n' for i in range(101)))
            expected = 'failure'
        if name == 'auto-long-temp':
            directory = '/'.join(letter * 100 for letter in 'abc')
            (work / directory).mkdir(parents=True)
            text += f'tmpdir: {directory}\n'; expected = 'investigate'
        if name.startswith('format-'): text = text.replace('input.geno', name[7:])
        if name in ('too-many-pars', 'include-overflow'):
            additions = ''.join(f'unused{i}: value\n' for i in range(410))
            if name == 'include-overflow':
                (work / 'included.par').write_text(additions)
                text += '+++ included.par\n'
            else: text += additions
        if name == 'include':
            (work / 'included.par').write_text('details: NO\n')
            text += '+++ included.par\n'
        if name == 'include-duplicate':
            (work / 'included.par').write_text('seed: 77\n')
            text += '+++ included.par\n'; expected = 'failure'
        if name == 'max-pars':
            text += ''.join(f'unused{i}: value\n' for i in range(400 - len(text.splitlines())))
        if name in ('win-paths', 'win-hash-path', 'win-long-log'):
            directory = 'space & folder' if name == 'win-paths' else 'hash # folder'
            if name == 'win-long-log': directory = 'a' * 105 + '/' + 'b' * 105
            (work / directory).mkdir(parents=True)
            text += f'tmpdir: "{directory}"\nfstatslog: "{directory}/log.txt"\n'
        if name == 'win-unicode':
            shutil.copyfile(work / 'input.geno', work / '日本.geno')
            text = text.replace('input.geno', '日本.geno')
        if name in ('win-missing-helper', 'win-unicode-helper'):
            bindir = work / ('isolated binaries' if name == 'win-missing-helper' else '日本 & binaries')
            bindir.mkdir()
            for path in binary_dir.iterdir():
                if path.suffix.lower() == '.dll' or path.name == 'qpAdm.exe' or (name == 'win-unicode-helper' and path.name == 'qpfstats.exe'):
                    shutil.copyfile(path, bindir / path.name)
            selected_exe = bindir / 'qpAdm.exe'
        if name == 'win-unicode-helper':
            (work / 'tmp 日本 # folder').mkdir()
            text += 'tmpdir: "tmp 日本 # folder"\n'
        data = text.encode('utf-8')
        if name == 'bom': data = b'\xef\xbb\xbf' + data
        if name == 'utf16': data = text.encode('utf-16')
        if name == 'crlf': data = data.replace(b'\n', b'\r\n')
        if name == 'embedded-nul': data = b'\0' + data
        parameter_name = '参数 & #.par' if name == 'win-unicode-helper' else 'audit.par'
        (work / parameter_name).write_bytes(data)
        invoke(name, 'qpfstats' if name.startswith('unix-full-fstats') else 'qpAdm', ['-p', 'absent.par' if name == 'missing-par' else parameter_name],
               work, expected, selected_exe=selected_exe)

    for name, arguments in [('cli-help', ['-h']), ('cli-noargs', []),
                            ('cli-version', ['-v']), ('cli-invalid', ['-?']),
                            ('cli-missing-argument', ['-p']),
                            ('cli-details', ['-d', '-p', 'par.qpAdm']),
                            ('cli-verbose', ['-V', '-p', 'par.qpAdm'])]:
        if re.search(selection, name):
            (common / 'tmp').mkdir(exist_ok=True)
            invoke(name, 'qpAdm', arguments, common,
                   'failure' if name in ('cli-noargs', 'cli-invalid', 'cli-missing-argument') else 'success')


def normalized(data, bindir, auto_seed=False):
    text = compatibility.normalized(data, bindir)
    match = re.search(r'^tmp: (.+)$', text, re.M)
    if match: text = text.replace(match[1], '<FSX>')
    # Default CLI -v deliberately continues upstream and chooses a random seed.
    if auto_seed: text = re.sub(r'^seed: -?[0-9]+$', 'seed: <AUTO>', text, flags=re.M)
    # Binary reader mmap diagnostics: the address is nondeterministic on either OS.
    text = re.sub(r'(mmfaddr: )0x[0-9a-f]+', r'\1<ADDRESS>', text)
    return text


def compare(left, right):
    manifests = [json.loads((p / 'manifest.json').read_text()) for p in (left, right)]
    a, b = manifests
    results, diffs = {}, []
    for name in sorted(a['cases'].keys() | b['cases'].keys()):
        if name not in a['cases'] or name not in b['cases']:
            results[name] = 'platform-specific/not selected'
            continue
        x, y = a['cases'][name], b['cases'][name]
        failures = []
        if x.get('returncode') != y.get('returncode'): failures.append('exit')
        for stream in ('stdout', 'stderr'):
            first, second = [normalized((p / f'{name}.{stream}').read_bytes(), m['binary_dir'], name == 'cli-version')
                             for p, m in zip((left, right), manifests)]
            if first != second:
                failures.append(stream)
                diffs.extend(difflib.unified_diff(first.splitlines(True), second.splitlines(True),
                             fromfile=f'left/{name}.{stream}', tofile=f'right/{name}.{stream}'))
        # Temporary PID names and helper logs are inspected separately; compare scientific files.
        for filename in ('model.mv', 'saved.fstats'):
            if x['files'].get(filename) != y['files'].get(filename): failures.append(filename)
        results[name] = failures or 'exact'
    (right / 'comparison.json').write_text(json.dumps(results, indent=2) + '\n')
    (right / 'comparison.diff').write_text(''.join(diffs), encoding='utf-8')
    print(json.dumps(results, indent=2))


def verify(directory):
    """Assert the repaired contract, including expected failures and cleanup."""
    manifest = json.loads((directory / 'manifest.json').read_text())
    failure_cases = {'cached-one-boot', 'cached-zero-boot', 'cached-negative-boot',
                     'zero-trials', 'bayes-zero', 'target-only', 'ratio-single', 'single-right',
                     'empty-value', 'empty-int', 'empty-dbl', 'too-many-pars', 'include-overflow',
                     'embedded-nul', 'utf16', 'constant', 'unclosed-quote'}
    failures = []
    baseline = next((directory / f'{name}.stdout' for name in ('default', 'plink-ped')
                     if name in manifest['cases']), None)
    baseline_science = None
    if baseline:
        baseline_science = normalized(baseline.read_bytes(), manifest['binary_dir']).split('\nleft pops:\n', 1)[-1]
    for name, case in manifest['cases'].items():
        code = case.get('returncode')
        expected_failure = case['expected'] == 'failure' or name in failure_cases
        if name == 'bom' and manifest['platform'] != 'win32': expected_failure = True
        if code is None or ((code != 0) != expected_failure): failures.append(name + ': exit')
        if code in (-11, 3221225477, 3221226356): failures.append(name + ': memory fault')
        stderr = (directory / f'{name}.stderr').read_bytes()
        if b'AddressSanitizer' in stderr or b'runtime error:' in stderr:
            failures.append(name + ': sanitizer')
        stdout = (directory / f'{name}.stdout').read_bytes()
        if baseline_science is not None and (name.startswith('format-') or
                (name.startswith('plink-') and not name.endswith('-auto'))):
            science = normalized(stdout, manifest['binary_dir']).split('\nleft pops:\n', 1)[-1]
            if science != baseline_science: failures.append(name + ': format changes scientific output')
        if name in ('bayes', 'bayes-positive', 'bayes-cached') and b'mcest (Bayesian):' not in stdout:
            failures.append(name + ': sampler was not exercised')
        if name in ('single-source', 'single-auto') and not re.search(rb'^summ:.* 1\.000 ', stdout, re.M):
            failures.append(name + ': single-source coefficient')
        temps = [path for path in case['files'] if re.match(
            r'^(fsx|ppp|pops|tpar|fslog|genotmp)\.[0-9]+', Path(path).name)]
        if manifest['platform'] == 'win32':
            if name == 'auto-keep' and len(temps) != 5: failures.append(name + ': retained files')
            if name != 'auto-keep' and temps: failures.append(name + ': leaked temporary files')
            if name.startswith(('auto', 'win-path', 'win-hash', 'win-long', 'single-auto')):
                for path in re.findall(rb'^(?:tmp: |removing )(.+)$', stdout, re.M):
                    if b'/' in path: failures.append(name + ': generated path separator')
    result = {'cases': len(manifest['cases']), 'failures': failures}
    (directory / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return bool(failures)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bin', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--select', default='.')
    parser.add_argument('--compare', type=Path, nargs=2)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    if args.verify: sys.exit(verify(args.verify.resolve()))
    if args.compare: compare(*[p.resolve() for p in args.compare])
    elif args.bin and args.output: run(args.bin.resolve(), args.output.resolve(), args.select)
    else: parser.error('specify --bin and --output, or --compare')
