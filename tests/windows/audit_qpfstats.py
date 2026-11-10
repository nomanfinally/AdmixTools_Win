"""T02 direct qpfstats modes, boundaries and downstream consumers.

Retains raw streams/exits and generated scientific bytes. --compare uses exact
printed precision, never a floating-point tolerance. Use a new output directory.
"""
import argparse
import difflib
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import compatibility
import parity


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(bindir, output, selection):
    output.mkdir(parents=True, exist_ok=False)
    common = output / 'fixtures'
    parity.fixtures(common)
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
               OPENBLAS_CORETYPE='NEHALEM', LC_ALL='C', STMP='tmp',
               ASAN_OPTIONS='detect_leaks=0:abort_on_error=1',
               UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    env['PATH'] = str(bindir) + os.pathsep + env.get('PATH', '')
    manifest = {'binary_dir': str(bindir), 'platform': sys.platform,
                'environment': {k: env[k] for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS',
                    'OPENBLAS_CORETYPE', 'LC_ALL', 'STMP', 'ASAN_OPTIONS', 'UBSAN_OPTIONS')},
                'executables': {}, 'cases': {}}

    def invoke(name, tool, args, work, expected='success', selected_env=None):
        exe = bindir / (tool + ('.exe' if os.name == 'nt' else ''))
        if not exe.is_file():
            manifest['cases'][name] = {'missing': True, 'arguments': args, 'expected': expected,
                                      'files': {}, 'temporaries': [], 'new_temporaries': []}
            (output / f'{name}.stdout').write_bytes(b'')
            (output / f'{name}.stderr').write_text('unavailable executable: ' + str(exe) + '\n')
            (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
            print(name + ': MISSING', flush=True)
            return
        manifest['executables'][tool] = sha(exe)
        before = sorted(p.name for p in (work / 'tmp').glob('*'))
        try:
            proc = subprocess.run([exe.name, *args], executable=str(exe), cwd=work,
                                  env=selected_env or env, capture_output=True, timeout=45)
            entry = {'returncode': proc.returncode, 'arguments': args, 'expected': expected}
            streams = (proc.stdout, proc.stderr)
        except subprocess.TimeoutExpired as error:
            entry = {'timeout': True, 'arguments': args, 'expected': expected}
            streams = (error.stdout or b'', error.stderr or b'')
        for stream, data in zip(('stdout', 'stderr'), streams):
            (output / f'{name}.{stream}').write_bytes(data)
        entry['files'] = {('output.fstats' if p.name.endswith('output.fstats') else p.name): sha(p)
                          for p in work.rglob('*') if p.is_file() and
                          (p.name.endswith('output.fstats') or p.name in ('output.fmv', 'model.mv'))}
        entry['temporaries'] = sorted(p.name for p in (work / 'tmp').glob('*'))
        entry['new_temporaries'] = sorted(set(entry['temporaries']) - set(before))
        manifest['cases'][name] = entry
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(f'{name}: {entry.get("returncode", "TIMEOUT")}', flush=True)

    (common / 'tmp').mkdir()
    invoke('prepare-packed', 'convertf', ['-p', 'par.convertf'], common)
    invoke('prepare-transpose', 'transpose', ['output.geno', 'input.tgeno'], common)
    rows = (common / 'input.geno').read_text().splitlines()
    ids = [line.split()[0] for line in (common / 'input.ind').read_text().splitlines()]
    (common / 'input.ancestry').write_text(''.join(
        f'rs{snp:05d} {person} {rows[snp][index]}\n'
        for snp in range(len(rows)) for index, person in enumerate(ids)), newline='\n')
    for filename in ('input.geno', 'output.geno', 'input.tgeno', 'input.ancestry'):
        data = (common / filename).read_bytes()
        cut = len(data) // 2
        (common / (filename + '.gz')).write_bytes(gzip.compress(data[:cut], mtime=0) +
                                                 gzip.compress(data[cut:], mtime=0))
    for kind, fmt in (('ped', 'PED'), ('bed', 'PACKEDPED')):
        text = (common / 'par.convertf').read_text().replace('PACKEDANCESTRYMAP', fmt)
        text = text.replace('output.geno', f'plink.{kind}').replace('output.snp',
                    f'plink-{kind}.pedsnp').replace('output.ind', f'plink-{kind}.pedind')
        (common / f'par.{kind}').write_text(text + 'outputgroup: YES\n')
        invoke('prepare-' + kind, 'convertf', ['-p', f'par.{kind}'], common)
        (common / f'plink.{kind}.gz').write_bytes(gzip.compress((common / f'plink.{kind}').read_bytes(), mtime=0))
    base = (common / 'par.qpfstats').read_text()
    modes = {
        'default': '', 'explicit-defaults': 'allsnps: NO\ninbreed: NO\n',
        'allsnps-default-inbreed': 'allsnps: YES\n',
        'allsnps-diploid': 'allsnps: YES\ninbreed: NO\n',
        'complete-inbreed': 'allsnps: NO\ninbreed: YES\n',
        'standard-precision': 'hires: NO\n', 'details': 'details: YES\n',
        'verbose': '', 'unscaled': 'scale: NO\n', 'doscale-alias': 'doscale: NO\n',
        'lambda': 'lambdascale: 2\n', 'cli-lambda': '', 'lambda-large': 'lambdascale: 1e100\n',
        'sizeweight': 'sizeweight: YES\n', 'outpop-none': 'outpop: NONE\n',
        'outpop-base': 'outpop: Out\n', 'outpop-other': 'outpop: A\n',
        'chrom': 'chrom: 3\n', 'nochrom': 'nochrom: 3\n',
        'gfromp': 'gfromp: YES\n', 'physical-fallback': '', 'xchrom': 'chrom: 23\n',
        'xchrom-male': 'chrom: 23\ninbreed: YES\n',
        'xdata': 'xdata: YES\n', 'noxdata-no': 'noxdata: NO\n',
        'custom-numchrom': 'numchrom: 21\nxdata: YES\n',
        'popsizelimit': 'popsizelimit: 3\n', 'popsizelimit-seed': 'popsizelimit: 3\nseed: 123\n',
        'cli-seed': 'popsizelimit: 3\n', 'high-seed': 'popsizelimit: 3\nseed: -2147483648\n',
        'inbreed-list': 'inbreedlistname: inbreeds\n',
        'inbreed-list-override': 'inbreed: YES\ninbreedlistname: inbreeds\n',
        'inbreed-list-empty': 'inbreedlistname: inbreeds\n',
        'inbreed-list-extra': 'inbreedlistname: inbreeds\n',
        'pseudo': 'allsnps: YES\ninbreed: NO\n',
        'pseudo-inbreed': 'allsnps: YES\ninbreed: YES\n',
        'pseudo-base': 'allsnps: YES\ninbreed: NO\n',
        'single-sample': 'allsnps: YES\ninbreed: NO\n',
        'single-inbreed': 'allsnps: YES\ninbreed: YES\n',
        'missing-complete': 'allsnps: NO\ninbreed: NO\n',
        'missing-all': 'allsnps: YES\ninbreed: NO\n',
        'missing-sizeweight': 'allsnps: YES\ninbreed: NO\nsizeweight: YES\n',
        'missing-disjoint': 'allsnps: YES\ninbreed: NO\n',
        'two-pops': '', 'three-pops': '', 'reorder': '', 'long-popnames': '',
        'no-poplist': '', 'empty-poplist': '', 'one-pop': '', 'many-pops': '',
        'overflow-pops': '', 'duplicate-pops': '', 'unknown-pop': '',
        'no-output': '', 'instem': '', 'poplist-alias': '', 'useallsnps-alias': 'useallsnps: YES\n',
        'legacy-keys': 'doanalysis: NO\nquartet: YES\nfstdmode: YES\nuseweights: NO\n'
                       'diag: .123\nminvar: .5\nnostatslim: 1\nf3log: unused.f3\nroot: unused\noutput: unused.out\n',
        'badsnp': 'badsnpname: badsnps\n', 'no-valid-snps': 'chrom: 99\n',
        'all-missing': '', 'constant': '', 'one-block': 'blgsize: 100\nchrom: 1\n',
        'zero-blocksize': 'blgsize: 0\n', 'negative-blocksize': 'blgsize: -1\n',
        'nan-blocksize': 'blgsize: nan\n', 'nan-lambda': 'lambdascale: nan\n',
        'infinite-lambda': 'lambdascale: inf\n',
        'missing-par': '', 'missing-geno': '', 'truncated-packed': '', 'empty-ind': '', 'empty-snp': '',
        'duplicate-ind': '', 'duplicate-snp': '', 'empty-scalar': 'inbreed:\n',
        'bom': '', 'utf16': '', 'embedded-nul': '', 'include': '',
        'packed': '', 'tgeno': '', 'ancestry': '', 'gzip-text': '', 'gzip-packed': '',
        'gzip-tgeno': '', 'gzip-ancestry': '', 'ped': '', 'bed': '', 'gzip-ped': '', 'gzip-bed': '',
        'gzip-corrupt': '', 'gzip-truncated': '', 'gzip-reader-fatal': '',
        'output-directory': '',
    }
    if os.name == 'nt':
        modes.update({'win-space-hash-unicode': '', 'win-forward-temp': '', 'win-missing-temp': '', 'win-long-path': ''})
    else:
        modes.update({'unix-full-hires': '', 'unix-full-standard': 'hires: NO\n'})
    failures = {'pseudo-base', 'single-inbreed', 'empty-poplist', 'one-pop', 'many-pops',
                'overflow-pops', 'duplicate-pops', 'unknown-pop', 'no-valid-snps', 'all-missing',
                'constant', 'missing-par', 'missing-geno', 'truncated-packed', 'empty-scalar',
                'utf16', 'embedded-nul', 'gzip-corrupt', 'gzip-truncated', 'gzip-reader-fatal',
                'output-directory', 'win-missing-temp', 'nan-lambda', 'infinite-lambda', 'outpop-other',
                'no-poplist', 'one-block', 'duplicate-snp', 'empty-ind', 'empty-snp'}
    for name, extra in modes.items():
        if not re.search(selection, name):
            continue
        work = output / name
        shutil.copytree(common, work)
        (work / 'output.fstats').unlink(missing_ok=True)
        text = base
        for line in extra.splitlines():
            key = line.split(':', 1)[0] + ':'
            text = '\n'.join(s for s in text.splitlines() if not s.startswith(key)) + '\n'
        text += extra
        args = ['-p', 'par']
        selected_env = dict(env)
        if name == 'verbose': args += ['-V']
        if name == 'cli-lambda': args += ['-l', '2']
        if name == 'cli-seed': args += ['-s', '123']
        if name.startswith('inbreed-list'):
            value = '' if name.endswith('empty') else ('A\n' if not name.endswith('extra') else 'A\nUnused\n')
            (work / 'inbreeds').write_text(value)
        if name.startswith('pseudo'):
            change = range(6) if name == 'pseudo-base' else range(6, 12)
            (work / 'input.geno').write_text(''.join(''.join(
                ('0' if row[i] == '1' else row[i]) if i in change else row[i]
                for i in range(len(row))) + '\n' for row in rows))
        if name.startswith('single-'):
            (work / 'input.ind').write_text(''.join(line + '\n' for i, line in enumerate(
                (work / 'input.ind').read_text().splitlines()) if i not in range(7, 12)))
            (work / 'input.geno').write_text(''.join(row[:7] + row[12:] + '\n' for row in rows))
        if name in ('missing-complete', 'missing-all', 'missing-disjoint', 'missing-sizeweight'):
            (work / 'input.geno').write_text(''.join(
                (row[:6] + '9'*6 + row[12:] if k % 4 == 0 else
                 row[:12] + '9'*6 + row[18:] if name == 'missing-disjoint' else row) + '\n'
                for k, row in enumerate(rows)))
            if name == 'missing-sizeweight':
                (work / 'input.geno').write_text(''.join(
                    (row[:6] + '999' + row[9:] if k % 4 == 0 else row) + '\n'
                    for k, row in enumerate(rows)))
        lists = {'two-pops': 'Out\nA\n', 'three-pops': 'Out\nA\nB\n', 'reorder': 'A\nOut\nB\nC\nX\nR1\nR2\nR3\nR4\n',
                 'empty-poplist': '', 'one-pop': 'Out\n', 'duplicate-pops': 'Out\nA\nA\n',
                 'unknown-pop': 'Out\nAbsent\n', 'many-pops': ''.join(f'P{i}\n' for i in range(60))}
        if name in lists: (work / 'pops').write_text(lists[name])
        if name == 'overflow-pops':
            (work / 'pops').write_text(''.join(f'P{i}\n' for i in range(216)))
            (work / 'input.ind').write_text(''.join(f'I{i} U P{i}\n' for i in range(216)))
            (work / 'input.geno').write_text(''.join((row*4) + '\n' for row in rows))
        if name == 'long-popnames':
            names = {p: p + 'LongPopulationName' for p in (work / 'pops').read_text().split()}
            (work / 'pops').write_text(''.join(p + '\n' for p in names.values()))
            (work / 'input.ind').write_text(''.join(f'{a} {b} {names[c]}\n' for a,b,c in
                                                    [line.split() for line in (work / 'input.ind').read_text().splitlines()]))
        if name in ('no-poplist', 'no-output', 'poplist-alias', 'instem'):
            key = {'no-poplist': 'poplistname:', 'no-output': 'fstatsoutname:', 'poplist-alias': 'poplistname:', 'instem': 'genotypename:'}[name]
            text = '\n'.join(s for s in text.splitlines() if not s.startswith(key)) + '\n'
            if name == 'poplist-alias': text += 'poplist: pops\n'
            if name == 'instem': text += 'instem: input\n'
        if name in ('xchrom', 'xchrom-male', 'xdata', 'noxdata-no'):
            (work / 'input.snp').write_text((work / 'input.snp').read_text().replace(' 22 ', ' 23 '))
            (work / 'input.ind').write_text((work / 'input.ind').read_text().replace(' U ',
                                            ' M ' if name == 'xchrom-male' else ' F '))
            if name == 'xchrom-male':
                (work / 'input.geno').write_text(''.join(row.replace('1', '0') + '\n' for row in rows))
        if name == 'physical-fallback':
            (work / 'input.snp').write_text(''.join(' '.join([s[0],s[1],'0',*s[3:]])+'\n' for s in
                                                    [line.split() for line in (work / 'input.snp').read_text().splitlines()]))
        if name == 'badsnp': (work / 'badsnps').write_text('rs00001\nrs00020\n')
        if name in ('all-missing', 'constant'):
            (work / 'input.geno').write_text(((('9' if name == 'all-missing' else '0')*54)+'\n')*len(rows))
        if name == 'missing-geno': (work / 'input.geno').unlink()
        if name == 'empty-ind': (work / 'input.ind').write_bytes(b'')
        if name == 'empty-snp': (work / 'input.snp').write_bytes(b'')
        if name == 'duplicate-ind':
            p = work / 'input.ind'; p.write_text(p.read_text().replace('Out1 ', 'Out0 '))
        if name == 'duplicate-snp':
            p = work / 'input.snp'; p.write_text(p.read_text().replace('rs00001 ', 'rs00000 '))
        formats = {'packed': 'output.geno', 'tgeno': 'input.tgeno', 'ancestry': 'input.ancestry',
                   'gzip-text': 'input.geno.gz', 'gzip-packed': 'output.geno.gz',
                   'gzip-tgeno': 'input.tgeno.gz', 'gzip-ancestry': 'input.ancestry.gz',
                   'truncated-packed': 'output.geno', 'gzip-corrupt': 'input.geno.gz',
                   'gzip-truncated': 'input.geno.gz', 'gzip-reader-fatal': 'input.geno.gz'}
        if name in formats: text = text.replace('genotypename: input.geno\n', f'genotypename: {formats[name]}\n')
        if name == 'truncated-packed': (work / 'output.geno').write_bytes((work / 'output.geno').read_bytes()[:-50])
        if name == 'gzip-corrupt': (work / 'input.geno.gz').write_bytes(b'not gzip')
        if name == 'gzip-truncated':
            p = work / 'input.geno.gz'; p.write_bytes(p.read_bytes()[:-8])
        if name == 'gzip-reader-fatal': (work / 'input.geno.gz').write_bytes(gzip.compress(b'invalid data\n'))
        if name in ('ped', 'bed', 'gzip-ped', 'gzip-bed'):
            kind = name.split('-')[-1]
            text = text.replace('input.geno', f'plink.{kind}' + ('.gz' if name.startswith('gzip') else ''))
            text = text.replace('input.snp', f'plink-{kind}.pedsnp').replace('input.ind', f'plink-{kind}.pedind')
        if name == 'output-directory': text = text.replace('output.fstats', '.')
        if name.startswith('unix-full'): text = text.replace('output.fstats', '/dev/full')
        if name == 'include':
            (work / 'included').write_text(text); text = '+++ included\n'
        if name == 'win-space-hash-unicode':
            for filename in ('input.geno', 'input.snp', 'input.ind', 'pops', 'output.fstats'):
                replacement = '日 本#& ' + filename
                if (work / filename).exists(): (work / filename).rename(work / replacement)
                text = text.replace(': ' + filename + '\n', ': "' + replacement + '"\n')
        if name == 'win-forward-temp':
            selected_env['STMP'] = str(work / 'tmp').replace('\\', '/')
            text = text.replace('input.geno\n', 'input.geno.gz\n')
        if name == 'win-missing-temp':
            selected_env['STMP'] = 'absent'; text = text.replace('input.geno\n', 'input.geno.gz\n')
        if name == 'win-long-path':
            directory = work.joinpath(*(['long-path-' + 'a'*45]*4))
            directory.mkdir(parents=True)
            for filename in ('input.geno', 'input.snp', 'input.ind', 'pops', 'output.fstats'):
                if (work / filename).exists(): shutil.copyfile(work / filename, directory / filename)
                text = text.replace(': ' + filename + '\n', ': "' + str(directory / filename) + '"\n')
        data = text.encode('utf-8')
        if name == 'bom': data = b'\xef\xbb\xbf' + data
        if name == 'utf16': data = text.encode('utf-16')
        if name == 'embedded-nul': data += b'x\0y\n'
        (work / 'par').write_bytes(data)
        if name == 'missing-par': args[1] = 'absent.par'
        expected = 'failure' if name in failures or name.startswith('unix-full') else 'success'
        if name == 'bom' and os.name != 'nt': expected = 'failure'
        invoke(name, 'qpfstats', args, work, expected, selected_env)

    for name, args, expected in (
            ('cli-help', ['-h'], 'success'), ('cli-version', ['-v'], 'success'),
            ('cli-none', [], 'success'), ('cli-invalid', ['-?'], 'failure'),
            ('cli-missing-argument', ['-p'], 'failure'),
            ('cli-unused', ['-g', 'ignored', '-o', 'ignored', '-x'], 'success')):
        if re.search(selection, name): invoke(name, 'qpfstats', args, common, expected)
    # Real serialized data consumers and automatic helper launch.
    if re.search(selection, 'consumer'):
        invoke('consumer-prepare', 'qpfstats', ['-p', 'par.qpfstats'], common)
        invoke('consumer-qpfmv', 'qpfmv', ['-p', 'par.qpfmv'], common)
        for tool in ('qpAdm', 'qpWave', 'qpfit'):
            (common / 'par.consumer').write_text('fstatsname: output.fstats\npopleft: left\npopright: right\nseed: 77\nnumboot: 50\n')
            invoke('consumer-' + tool, tool, ['-p', 'par.consumer'], common)
        (common / 'par.consumer-auto').write_text((common / 'par.qpAdm').read_text() + 'allsnps: YES\nnumboot: 50\n')
        invoke('consumer-auto-qpAdm', 'qpAdm', ['-p', 'par.consumer-auto'], common)
        invoke('consumer-auto-qpWave', 'qpWave', ['-p', 'par.consumer-auto'], common)
        invoke('consumer-auto-qpfit', 'qpfit', ['-p', 'par.consumer-auto'], common)
        (common / 'par.consumer-mix').write_text('fstatsname: output.fstats\npoplistname: mixpops\nseed: 77\nnumboot: 10\nmctrials: 10\ngslmaxiter: 20\n')
        (common / 'mixpops').write_text('X\nA\nB\n')
        invoke('consumer-qpmix', 'qpmix', ['-p', 'par.consumer-mix'], common)
        (common / 'par.consumer-graph').write_text('fstatsname: output.fstats\ngraphname: graph\nseed: 77\ndiag: .0001\nlsqmode: YES\nhires: YES\n')
        invoke('consumer-qpGraph', 'qpGraph', ['-p', 'par.consumer-graph'], common)
        (common / 'par.consumer-graph-auto').write_text((common / 'par.qpGraph').read_text() + 'graphname: graph\n')
        invoke('consumer-auto-qpGraph', 'qpGraph', ['-p', 'par.consumer-graph-auto'], common)
        (common / 'mixed-quads').write_text('Out A Out A\nOut A Out B\nOut A B X\n')
        (common / 'par.consumer-fmv').write_text('fstatsname: output.fstats\npopfilename: mixed-quads\nfmvoutname: output.fmv\nprintsd: YES\n')
        invoke('consumer-mixed-qpfmv', 'qpfmv', ['-p', 'par.consumer-fmv'], common)


def normalized(data, bindir):
    text = compatibility.normalized(data, bindir)
    for tool in ('qpfstats', 'qpfit', 'qpmix'):
        text = text.replace(tool + '.exe', tool)
    text = re.sub(r'(mmfaddr: )0x[0-9a-f]+', r'\1<ADDRESS>', text)
    match = re.search(r'^tmp: (.+)$', text, re.M)
    if match: text = text.replace(match[1], '<FSX>')
    return text


def verify(directory):
    m = json.loads((directory / 'manifest.json').read_text())
    failures = []
    for name, case in m['cases'].items():
        code = case.get('returncode')
        if code is None or ((code != 0) != (case['expected'] == 'failure')): failures.append(name + ': exit')
        stderr = (directory / f'{name}.stderr').read_bytes()
        if b'AddressSanitizer' in stderr or b'runtime error:' in stderr: failures.append(name + ': sanitizer')
        if code in (-11, 3221225477, 3221226356): failures.append(name + ': memory fault')
        if code == 0 and 'output.fstats' in case['files'] and name not in ('prepare-packed', 'prepare-transpose', 'prepare-ped', 'prepare-bed'):
            work = directory / ('fixtures' if name.startswith(('consumer-', 'cli-')) else name)
            paths = list(work.glob('*output.fstats'))
            if paths and re.search(rb'(?i)(?<![a-z])(nan|[+-]?inf)(?![a-z])', paths[0].read_bytes()):
                failures.append(name + ': nonfinite fstats')
        if m['platform'] == 'win32' and case.get('new_temporaries', case['temporaries']):
            failures.append(name + ': temporary leak')
        if name == 'win-forward-temp':
            data = (directory / f'{name}.stdout').read_text()
            match = re.search(r'^unzip cmd:.* > "?([^"\n]+)', data, re.M)
            if not match or '/' in match[1]: failures.append(name + ': generated separators')
    # These equivalences test effective behavior, including inherited ignored keys.
    for first, second in (('default', 'explicit-defaults'), ('unscaled', 'doscale-alias'),
            ('default', 'poplist-alias'), ('default', 'instem'), ('default', 'legacy-keys'),
            ('popsizelimit', 'popsizelimit-seed'), ('popsizelimit', 'cli-seed'),
            ('popsizelimit', 'high-seed'), ('default', 'win-space-hash-unicode'),
            ('allsnps-default-inbreed', 'useallsnps-alias')):
        if first in m['cases'] and second in m['cases']:
            x, y = [m['cases'][n]['files'].get('output.fstats') for n in (first, second)]
            if not x or x != y: failures.append(first + '/' + second + ': data differ')
    (directory / 'verification.json').write_text(json.dumps({'failures': failures}, indent=2) + '\n')
    print(json.dumps(failures, indent=2))
    return bool(failures)


def compare(left, right):
    a, b = [json.loads((p / 'manifest.json').read_text()) for p in (left, right)]
    result, diffs = {}, []
    for name in sorted(a['cases'].keys() | b['cases'].keys()):
        if name not in a['cases'] or name not in b['cases']:
            result[name] = 'platform-specific/not selected'; continue
        x, y = a['cases'][name], b['cases'][name]
        errors = []
        if x.get('returncode') != y.get('returncode'): errors.append('exit')
        for stream in ('stdout', 'stderr'):
            first, second = [normalized((p / f'{name}.{stream}').read_bytes(), m['binary_dir'])
                             for p,m in ((left,a),(right,b))]
            if first != second:
                errors.append(stream)
                diffs.extend(difflib.unified_diff(first.splitlines(True), second.splitlines(True),
                             fromfile=f'left/{name}.{stream}', tofile=f'right/{name}.{stream}'))
        for filename in x['files'].keys() | y['files'].keys():
            if x['files'].get(filename) != y['files'].get(filename): errors.append(filename)
        result[name] = errors or 'exact'
    (right / ('comparison-' + left.name + '.json')).write_text(json.dumps(result, indent=2) + '\n')
    (right / ('comparison-' + left.name + '.diff')).write_text(''.join(diffs), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bin', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--select', default='.')
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--compare', nargs=2, type=Path)
    args = parser.parse_args()
    if args.verify: sys.exit(verify(args.verify.resolve()))
    elif args.compare: compare(*[p.resolve() for p in args.compare])
    elif args.bin and args.output: run(args.bin.resolve(), args.output.resolve(), args.select)
    else: parser.error('use --bin DIR --output NEW_DIR, --verify DIR, or --compare DIR DIR')
