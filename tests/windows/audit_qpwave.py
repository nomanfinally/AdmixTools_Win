"""T03 qpWave mode/boundary matrix. Retain raw evidence; compare exactly.

Use --bin DIR --output NEW_DIR on each OS; --verify DIR checks behavior;
--compare LINUX WINDOWS retains exact stream/data differences. No tolerances.
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

import audit_qpfstats
import parity


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(bindir, output, selection, probe=None):
    if os.name == 'nt':
        import ctypes
        # Inherited by child CLI processes: do not wait for interactive OS error
        # dialogs in a captured-output test. Their real exit codes are retained.
        ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002)
    output.mkdir(parents=True, exist_ok=False)
    common = output / 'fixtures'
    parity.fixtures(common)
    (common / 'tmp').mkdir()
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
               OPENBLAS_CORETYPE='NEHALEM', LC_ALL='C', STMP='tmp',
               ASAN_OPTIONS='detect_leaks=0:abort_on_error=1',
               UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    env['PATH'] = str(bindir) + os.pathsep + env.get('PATH', '')
    manifest = dict(binary_dir=str(bindir), platform=sys.platform, completed=False,
                    environment={k: env[k] for k in ('OPENBLAS_NUM_THREADS',
                    'OMP_NUM_THREADS', 'OPENBLAS_CORETYPE', 'LC_ALL', 'STMP',
                    'ASAN_OPTIONS', 'UBSAN_OPTIONS')}, executables={}, cases={})

    def invoke(name, tool, args, work, failure=False, selected_env=None, exe=None):
        exe = exe or bindir / (tool + ('.exe' if os.name == 'nt' else ''))
        entry = dict(arguments=args, expected='failure' if failure else 'success', files={})
        manifest['executables'][tool] = sha(exe)
        try:
            proc = subprocess.run([exe.name, *args], executable=str(exe), cwd=work,
                                  env=selected_env or env, capture_output=True, timeout=30)
            entry['returncode'] = proc.returncode
            streams = proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as error:
            entry['timeout'] = True
            streams = error.stdout or b'', error.stderr or b''
        for stream, data in zip(('stdout', 'stderr'), streams):
            (output / f'{name}.{stream}').write_bytes(data)
        for filename in ('saved.fstats', 'result.out'):
            if (work / filename).is_file(): entry['files'][filename] = sha(work / filename)
        if (work / 'helper.log').is_file():
            (output / f'{name}.helperlog').write_bytes((work / 'helper.log').read_bytes())
            entry['helper_log'] = True
        entry['temporaries'] = sorted(p.name for p in (work / 'tmp').glob('*'))
        entry['keep'] = 'keep' in name
        manifest['cases'][name] = entry
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(f'{name}: {entry.get("returncode", "TIMEOUT")}', flush=True)
        return entry

    invoke('prepare-packed', 'convertf', ['-p', 'par.convertf'], common)
    invoke('prepare-transpose', 'transpose', ['output.geno', 'input.tgeno'], common)
    invoke('prepare-fstats', 'qpfstats', ['-p', 'par.qpfstats'], common)
    for kind, fmt in (('ped', 'PED'), ('bed', 'PACKEDPED')):
        text = (common / 'par.convertf').read_text().replace('PACKEDANCESTRYMAP', fmt)
        text = text.replace('output.geno', f'plink.{kind}').replace('output.snp',
                 f'plink-{kind}.pedsnp').replace('output.ind', f'plink-{kind}.pedind')
        (common / f'par.{kind}').write_text(text + 'outputgroup: YES\n')
        invoke('prepare-' + kind, 'convertf', ['-p', f'par.{kind}'], common)
    rows = (common / 'input.geno').read_text().splitlines()
    people = (common / 'input.ind').read_text().splitlines()
    (common / 'input.ancestry').write_text(''.join(
        f'rs{s:05d} {person.split()[0]} {row[i]}\n'
        for s, row in enumerate(rows) for i, person in enumerate(people)))
    for filename in ('input.geno', 'output.geno', 'input.tgeno', 'input.ancestry', 'plink.ped', 'plink.bed'):
        data = (common / filename).read_bytes()
        cut = len(data) // 2
        (common / (filename + '.gz')).write_bytes(gzip.compress(data[:cut], mtime=0) +
                                                 gzip.compress(data[cut:], mtime=0))
    base = (common / 'par.qpWave').read_text()
    modes = {
        'default': '', 'explicit-defaults': 'allsnps: NO\ninbreed: NO\n',
        'inbreed': 'inbreed: YES\n', 'fancy-no': 'fancyf4: NO\n',
        'oracle-no': 'oracle: NO\n', 'oasmode-alias': 'oasmode: NO\n',
        'diagplus': 'oracle: NO\ndiagplus: .001\n',
        'diagvarplus': 'oracle: NO\ndiagvarplus: .000001\n',
        'eigen': 'eigenanalysis: YES\n', 'verbose': '',
        'rank-zero': 'maxrank: 0\n', 'rank-one': 'maxrank: 1\n',
        'rank-negative': 'maxrank: -1\n', 'rank-large': 'maxrank: 100\n',
        'two-left': '', 'square': '', 'square-two': '', 'reorder': '', 'one-left': '', 'one-right': '',
        'empty-left': '', 'empty-right': '', 'no-left': '', 'no-right': '',
        'left-greater': '', 'duplicate-left': '', 'duplicate-right': '', 'overlap': '',
        'unknown-pop': '', 'duplicate-ind': '', 'duplicate-snp': '',
        'chrom': 'chrom: 3\n', 'xchrom': 'chrom: 23\n',
        'xchrom-male': 'chrom: 23\ninbreed: YES\n', 'gfromp': 'gfromp: YES\n',
        'physical-fallback': '', 'numchrom': 'numchrom: 21\n',
        'badsnp': 'badsnpname: badsnps\n', 'blockfile': 'blockname: blocks\n',
        'blockfile-overflow': 'blockname: blocks\n',
        'blockfile-intmax': 'blockname: blocks\n',
        'missing-direct': '', 'missing-allsnps': 'allsnps: YES\n',
        'popsizelimit': 'popsizelimit: 3\n', 'popsizelimit-repeat': 'popsizelimit: 3\n',
        'popsizelimit-seed': 'popsizelimit: 3\nseed: 123\n',
        'popsizelimit-zero': 'popsizelimit: 3\nseed: 0\n',
        'popsizelimit-one': 'popsizelimit: 3\nseed: 1\n',
        'popsizelimit-high': 'popsizelimit: 3\nseed: -2147483648\n',
        'unlimited': 'popsizelimit: 100\n',
        'manual-subset-77': '', 'manual-subset-123': '',
        'allsnps': 'allsnps: YES\n', 'allsnps-diploid': 'allsnps: YES\ninbreed: NO\n',
        'allsnps-inbreed': 'allsnps: YES\ninbreed: YES\n',
        'allsnps-base': 'allsnps: YES\nbasepop: C\n',
        'allsnps-output': 'allsnps: YES\nfstatsoutname: saved.fstats\nfstatslog: helper.log\n',
        'allsnps-keep': 'allsnps: YES\nkeeptmp: YES\n',
        'allsnps-limit': 'allsnps: YES\npopsizelimit: 3\n',
        'allsnps-limit-seed': 'allsnps: YES\npopsizelimit: 3\nseed: 123\n',
        'allsnps-copy-failure': 'allsnps: YES\nfstatsoutname: absent/saved.fstats\n',
        'allsnps-helper-failure': 'allsnps: YES\ngenotypename: absent\n',
        'allsnps-keep-failure': 'allsnps: YES\ngenotypename: absent\nkeeptmp: YES\n',
        'allsnps-missing-temp': 'allsnps: YES\ntmpdir: absent\n',
        'allsnps-missing-helper': 'allsnps: YES\n',
        'cached': 'fstatsname: output.fstats\n',
        'cached-eigen': 'fstatsname: output.fstats\neigenanalysis: YES\n',
        'cached-oracle-no': 'fstatsname: output.fstats\noracle: NO\n',
        'cached-duplicate': 'fstatsname: output.fstats\n',
        'cached-missing-base': 'fstatsname: output.fstats\n',
        'cached-empty': 'fstatsname: output.fstats\n',
        'cached-malformed': 'fstatsname: output.fstats\n',
        'cached-truncated': 'fstatsname: output.fstats\n',
        'cached-nan': 'fstatsname: output.fstats\n',
        'cached-missing-cov': 'fstatsname: output.fstats\n',
        'cached-missing-mean': 'fstatsname: output.fstats\n',
        'cached-invalid-number': 'fstatsname: output.fstats\n',
        'cached-partial-number': 'fstatsname: output.fstats\n',
        'cached-infinite': 'fstatsname: output.fstats\n',
        'cached-conflict': 'fstatsname: output.fstats\n',
        'cached-bare-base': 'fstatsname: output.fstats\n',
        'cached-reversed': 'fstatsname: output.fstats\n',
        'readonly-tgeno': 'genotypename: input.tgeno\n',
        'duplicate-ind-ancestry': 'genotypename: input.ancestry\n',
        'duplicate-ind-packed': 'genotypename: output.geno\n',
        'duplicate-ind-tgeno': 'genotypename: input.tgeno\n',
        'cached-dim-overflow': 'fstatsname: output.fstats\n',
        'cached-no-header': 'fstatsname: output.fstats\n',
        'cached-overflow': 'fstatsname: output.fstats\n',
        'cached-long-header': 'fstatsname: output.fstats\n',
        'zero-blocksize': 'blgsize: 0\n', 'negative-blocksize': 'blgsize: -1\n',
        'nan-blocksize': 'blgsize: nan\n', 'infinite-diag': 'oracle: NO\ndiagplus: inf\n',
        'nan-diag': 'oracle: NO\ndiagvarplus: nan\n',
        'one-block': 'chrom: 1\nblgsize: 100\n', 'no-valid-snps': 'chrom: 99\n',
        'all-missing': '', 'constant': '', 'missing-geno': '', 'missing-par': '',
        'empty-snp': '', 'empty-ind': '', 'truncated-packed': '',
        'gzip-corrupt': '', 'gzip-truncated': '', 'gzip-crc': '', 'gzip-length': '',
        'gzip-empty': '', 'gzip-onebyte': '',
        'missing-fstats': 'fstatsname: absent\n',
        'instem': '', 'include': '', 'bom': '', 'utf16': '', 'embedded-nul': '',
        'output': 'output: result.out\n', 'outputname': 'outputname: result.out\n',
        'oldallsnpsmode': 'allsnps: YES\noldallsnpsmode: YES\n',
        'numboot': 'numboot: 0\n', 'details': 'details: YES\n',
        'space-hash-unicode': '', 'forward-paths': '',
    }
    for fmt in ('text', 'packed', 'tgeno', 'ancestry', 'ped', 'bed'):
        modes['format-' + fmt] = ''
        modes['gzip-' + fmt] = ''
    failures = {'one-left', 'one-right', 'empty-left', 'empty-right', 'no-left', 'no-right',
        'left-greater', 'duplicate-left', 'duplicate-right', 'overlap', 'unknown-pop',
        'duplicate-ind', 'duplicate-snp', 'zero-blocksize', 'negative-blocksize', 'nan-blocksize',
        'infinite-diag', 'nan-diag', 'one-block', 'no-valid-snps', 'all-missing', 'constant',
        'missing-geno', 'missing-par', 'missing-fstats', 'empty-snp', 'empty-ind', 'truncated-packed',
        'gzip-corrupt', 'gzip-truncated', 'utf16', 'embedded-nul', 'cached-duplicate',
        'cached-missing-base', 'cached-empty', 'cached-malformed', 'cached-truncated',
        'cached-nan', 'cached-no-header', 'cached-overflow', 'cached-missing-cov', 'cached-dim-overflow',
        'cached-missing-mean', 'cached-invalid-number', 'cached-partial-number',
        'cached-infinite', 'cached-conflict', 'cached-bare-base',
        'duplicate-ind-ancestry', 'duplicate-ind-packed', 'duplicate-ind-tgeno',
        'gzip-crc', 'gzip-length', 'gzip-empty', 'gzip-onebyte',
        'blockfile-overflow', 'blockfile-intmax',
        'allsnps-copy-failure', 'allsnps-helper-failure', 'allsnps-keep-failure',
        'allsnps-missing-temp', 'allsnps-missing-helper',
        'output', 'outputname', 'oldallsnpsmode', 'numboot', 'details'}
    for name, extra in modes.items():
        if not re.search(selection, name): continue
        if name.startswith('manual-subset') and probe is None: continue
        work = output / name
        shutil.copytree(common, work)
        text = base
        for line in extra.splitlines():
            text = re.sub(r'^' + re.escape(line.split(':')[0]) + r':.*\n', '', text, flags=re.M)
        text += extra
        args, selected_env, exe = ['-p', 'par'], dict(env), None
        if name == 'verbose': args += ['-V']
        if name in ('two-left', 'one-left', 'square', 'square-two', 'one-right', 'empty-left', 'empty-right',
                    'duplicate-left', 'duplicate-right', 'overlap', 'left-greater',
                    'cached-duplicate', 'unknown-pop', 'cached-missing-base'):
            if name == 'two-left': (work / 'left').write_text('X\nA\n')
            if name == 'one-left': (work / 'left').write_text('X\n')
            if name == 'one-right': (work / 'right').write_text('Out\n')
            if name == 'square': (work / 'right').write_text('Out\nR1\nR2\n')
            if name == 'square-two':
                (work / 'left').write_text('X\nA\n')
                (work / 'right').write_text('Out\nR1\n')
            if name == 'empty-left': (work / 'left').write_text('')
            if name == 'empty-right': (work / 'right').write_text('')
            if name in ('duplicate-left', 'cached-duplicate'): (work / 'left').write_text('X\nX\nB\n')
            if name == 'duplicate-right': (work / 'right').write_text('Out\nR1\nR1\n')
            if name == 'overlap': (work / 'right').write_text('Out\nX\nR2\n')
            if name == 'left-greater': (work / 'right').write_text('Out\nR1\n')
            if name in ('unknown-pop', 'cached-missing-base'): (work / 'left').write_text('Absent\nA\nB\n')
        if name in ('no-left', 'no-right'):
            text = text.replace('popleft: left\n' if name == 'no-left' else 'popright: right\n', '')
        if name == 'reorder': (work / 'left').write_text('B\nX\nA\n')
        if name.startswith('duplicate-ind-'):
            lines = (work / 'input.ind').read_text().splitlines()
            lines[1] = lines[0]
            (work / 'input.ind').write_text('\n'.join(lines) + '\n')
        if name == 'readonly-tgeno': (work / 'input.tgeno').chmod(0o444)
        if name in ('output', 'outputname'): (work / 'result.out').write_bytes(b'preserve existing output\n')
        if name in ('missing-geno', 'empty-ind', 'empty-snp', 'duplicate-ind', 'duplicate-snp'):
            filename = {'missing-geno':'input.geno', 'empty-ind':'input.ind', 'empty-snp':'input.snp',
                        'duplicate-ind':'input.ind', 'duplicate-snp':'input.snp'}[name]
            p = work / filename
            if name == 'missing-geno': p.unlink()
            elif name.startswith('empty'): p.write_text('')
            else:
                lines = p.read_text().splitlines()
                lines[1] = lines[0]
                p.write_text('\n'.join(lines) + '\n')
        if name in ('all-missing', 'constant'):
            (work / 'input.geno').write_text(((('9' if name == 'all-missing' else '0') * 54) + '\n') * len(rows))
        if name in ('missing-direct', 'missing-allsnps'):
            (work / 'input.geno').write_text(''.join(''.join('9' if (s * 7 + i) % 37 == 0 else value
                for i, value in enumerate(row)) + '\n' for s, row in enumerate(rows)))
        if name in ('xchrom', 'xchrom-male'):
            (work / 'input.snp').write_text((work / 'input.snp').read_text().replace(' 22 ', ' 23 '))
            if name == 'xchrom-male': (work / 'input.ind').write_text((work / 'input.ind').read_text().replace(' U ', ' M '))
        if name == 'physical-fallback':
            (work / 'input.snp').write_text(''.join(' '.join(line.split()[:2] + ['0'] + line.split()[3:]) + '\n'
                                                  for line in (work / 'input.snp').read_text().splitlines()))
        if name == 'badsnp': (work / 'badsnps').write_text('rs00000\nrs00200\n')
        if name.startswith('blockfile'):
            block = 2221 if name == 'blockfile-overflow' else 2147483647
            (work / 'blocks').write_text(''.join(f'rs{s:05d} {s // 5 if name == "blockfile" else block}\n'
                                                 for s in range(len(rows))))
        if name.startswith('manual-subset'):
            selected_seed = name.rsplit('-', 1)[1]
            (work / 'analysis-pops').write_text((work / 'left').read_text() + (work / 'right').read_text())
            proc = subprocess.run([str(probe), 'sample', 'input.ind', 'analysis-pops', '3', selected_seed],
                                  cwd=work, env=env, capture_output=True, check=True)
            indices = [int(s) for s in proc.stdout.splitlines() if s.isdigit()]
            assert len(indices) == 24
            (work / 'input.ind').write_text(''.join(people[i] + '\n' for i in indices))
            (work / 'input.geno').write_text(''.join(''.join(row[i] for i in indices) + '\n' for row in rows))
        if name.startswith(('format-', 'gzip-')) or name == 'truncated-packed':
            fmt = name.split('-', 1)[1]
            filename = {'text':'input.geno', 'packed':'output.geno', 'tgeno':'input.tgeno',
                        'ancestry':'input.ancestry', 'ped':'plink.ped', 'bed':'plink.bed',
                        'corrupt':'input.geno', 'truncated':'input.geno',
                        'crc':'input.geno', 'length':'input.geno'}.get(fmt, 'output.geno')
            if name.startswith('gzip-'): filename += '.gz'
            text = text.replace('genotypename: input.geno', 'genotypename: ' + filename)
            if fmt in ('ped', 'bed'):
                text = text.replace('input.ind', f'plink-{fmt}.pedind').replace('input.snp', f'plink-{fmt}.pedsnp')
            if name == 'truncated-packed': (work / filename).write_bytes((work / filename).read_bytes()[:100])
            if name == 'gzip-corrupt': (work / filename).write_bytes(b'bad gzip')
            if name == 'gzip-truncated': (work / filename).write_bytes((work / filename).read_bytes()[:-9])
            if name in ('gzip-crc', 'gzip-length'):
                # One member makes the damaged trailer's classification unambiguous.
                data = bytearray(gzip.compress((work / 'input.geno').read_bytes(), mtime=0))
                data[-8 if name == 'gzip-crc' else -4] ^= 1
                (work / filename).write_bytes(data)
            if name == 'gzip-empty': (work / filename).write_bytes(b'')
            if name == 'gzip-onebyte': (work / filename).write_bytes(b'x')
        if name.startswith('cached-'):
            p = work / 'output.fstats'
            content = p.read_text()
            if name == 'cached-empty': content = ''
            if name == 'cached-malformed': content = '# fbasis basepop: Out\nA B garbage\n'
            if name == 'cached-truncated': content = content[:content.index('\n', content.index('\n') + 1) + 1]
            if name == 'cached-nan': content = re.sub(r'(?m)^(\s*A\s+A)\s+[^\n]+$', r'\1 nan', content, count=1)
            if name == 'cached-missing-cov':
                lines = content.splitlines(True)
                index = next(i for i, line in enumerate(lines) if line.split()[:4] == ['A', 'R1', 'A', 'R1'])
                content = ''.join(lines[:index] + lines[index + 1:])
            if name == 'cached-missing-mean':
                content = ''.join(line for line in content.splitlines(True) if not
                    (len(line.split()) == 3 and line.split()[:2] == ['A', 'R1']))
            if name == 'cached-invalid-number':
                content = re.sub(r'(?m)^(\s*A\s+R1)\s+[^\n]+$', r'\1 invalid', content, count=1)
            if name in ('cached-partial-number', 'cached-infinite'):
                value = '1.5oops' if name == 'cached-partial-number' else 'inf'
                content = re.sub(r'(?m)^(\s*A\s+R1)\s+[^\n]+$', lambda m: m[1] + ' ' + value, content, count=1)
            if name == 'cached-conflict': content += 'A R1 9999\n'
            if name == 'cached-bare-base': content = '##fbasis. basepop:\n'
            if name == 'cached-reversed':
                lines = content.splitlines(True)
                content = lines[0] + ''.join(reversed(lines[1:]))
            if name == 'cached-dim-overflow':
                (work / 'left').write_text(''.join(f'L{i}\n' for i in range(218)))
                (work / 'right').write_text(''.join(f'R{i}\n' for i in range(218)))
            if name == 'cached-no-header': content = '\n'.join(content.splitlines()[1:]) + '\n'
            if name == 'cached-overflow': content = '# fbasis basepop: Out\n' + ''.join(f'P{i} P{i} 1\n' for i in range(100))
            if name == 'cached-long-header': content = content.splitlines()[0] + ' ' * 460 + '\n' + '\n'.join(content.splitlines()[1:]) + '\n'
            p.write_text(content)
        if name == 'instem':
            text = re.sub(r'^(genotypename|snpname|indivname):.*\n', '', text, flags=re.M) + 'instem: input\n'
        if name == 'include': (work / 'included').write_text(text); text = '+++ included\n'
        if name in ('space-hash-unicode', 'forward-paths'):
            dirname = 'data # café' if name == 'space-hash-unicode' else 'data'
            (work / dirname).mkdir()
            for filename in ('input.geno', 'input.snp', 'input.ind', 'left', 'right'):
                shutil.copyfile(work / filename, work / dirname / filename)
                path = str(Path(dirname) / filename)
                if name == 'forward-paths': path = path.replace('\\', '/')
                operand = '"' + path + '"' if os.name == 'nt' else path
                text = re.sub(r'(?m)(: )' + re.escape(filename) + r'$', lambda m: m[1] + operand, text)
        if name == 'allsnps-missing-helper':
            isolated = work / 'isolated'
            isolated.mkdir()
            exe = isolated / ('qpWave.exe' if os.name == 'nt' else 'qpWave')
            shutil.copyfile(bindir / exe.name, exe)
            if os.name == 'nt':
                for dll in bindir.glob('*.dll'): shutil.copyfile(dll, isolated / dll.name)
            else: exe.chmod(0o755)
            selected_env['PATH'] = str(isolated)
        if name == 'missing-par': args = ['-p', 'absent']
        if name == 'bom': (work / 'par').write_bytes(b'\xef\xbb\xbf' + text.encode())
        elif name == 'utf16': (work / 'par').write_bytes(text.encode('utf-16'))
        elif name == 'embedded-nul': (work / 'par').write_bytes(text.encode() + b'x:\0bad\n')
        else: (work / 'par').write_text(text, encoding='utf-8', newline='\n')
        invoke(name, 'qpWave', args, work, name in failures, selected_env, exe)
    for name, args, failure in [('help', ['-h'], False), ('no-args', [], True),
            ('version', ['-v'], False), ('invalid-option', ['-z'], True),
            ('missing-option-value', ['-p'], True)]:
        if re.search(selection, name): invoke('cli-' + name, 'qpWave', args, common, failure)
    manifest['completed'] = True
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


def normalized(data, bindir):
    return audit_qpfstats.normalized(data, bindir)


def results(directory, name):
    text = (directory / f'{name}.stdout').read_text(encoding='utf-8', errors='replace')
    start = text.find('f4info:')
    end = text.find('removing ', start)
    if end < 0: end = text.find('##end of qpWave:', start)
    return text[start:end] if start >= 0 and end >= 0 else None


def verify(directory):
    m = json.loads((directory / 'manifest.json').read_text())
    failures = []
    if not m['completed']: failures.append('incomplete matrix')
    for name, case in m['cases'].items():
        code = case.get('returncode')
        expected = case['expected']
        # Quoted paths with spaces and an initial UTF-8 BOM are Windows extensions.
        if m['platform'] != 'win32' and name in ('bom', 'space-hash-unicode'): expected = 'failure'
        if code is None or (code != 0) != (expected == 'failure'): failures.append(name + ': exit')
        err = (directory / f'{name}.stderr').read_bytes()
        out = (directory / f'{name}.stdout').read_bytes()
        if b'AddressSanitizer' in err or b'runtime error:' in err: failures.append(name + ': sanitizer')
        if code in (-11, 3221225477, 3221226356): failures.append(name + ': memory fault')
        if case['temporaries'] and not case['keep']: failures.append(name + ': temporary leak')
        if case['keep'] and len(case['temporaries']) != 5: failures.append(name + ': retention')
        if code == 0 and not name.startswith(('prepare-', 'cli-')):
            if results(directory, name) is None: failures.append(name + ': no rank output')
            scientific = (results(directory, name) or '').encode()
            if re.search(rb'(?i)(?<![a-z])(nan|[+-]?inf)(?![a-z])', scientific): failures.append(name + ': nonfinite results')
        if name.startswith('popsizelimit') and code == 0 and b'indivs: 24' not in out:
            failures.append(name + ': incorrect selected row count')
        if name == 'allsnps-output' and ('saved.fstats' not in case['files'] or not case.get('helper_log')):
            failures.append(name + ': missing requested artifacts')
        if name in ('output', 'outputname') and case['files'].get('result.out') != hashlib.sha256(b'preserve existing output\n').hexdigest():
            failures.append(name + ': output was modified')
        if name == 'cli-version' and (err or out.strip() != (b'version: 2201.w' if m['platform'] == 'win32' else b'version: 2201')):
            failures.append(name + ': version-only contract')
        if m['platform'] == 'win32' and name.startswith('allsnps'):
            match = re.search(rb'^tmp: (.+)$', out, re.M)
            if match and b'/' in match[1]: failures.append(name + ': generated path separators')
    for a, b in [('default', 'explicit-defaults'), ('default', 'unlimited'), ('default', 'instem'),
            ('default', 'eigen'), ('cached', 'cached-eigen'), ('default', 'forward-paths'),
            ('default', 'space-hash-unicode'), ('oracle-no', 'oasmode-alias'),
            ('default', 'readonly-tgeno'), ('cached', 'cached-reversed'),
            ('popsizelimit', 'popsizelimit-repeat'), ('popsizelimit-zero', 'popsizelimit-one'),
            ('popsizelimit', 'manual-subset-77'), ('popsizelimit-seed', 'manual-subset-123')]:
        if a in m['cases'] and b in m['cases']:
            if b == 'space-hash-unicode' and m['platform'] != 'win32': continue
            if not results(directory, a) or results(directory, a) != results(directory, b): failures.append(a + '/' + b + ': rank output differs')
    for a, b in [('default', 'popsizelimit'), ('popsizelimit', 'popsizelimit-seed')]:
        if a in m['cases'] and b in m['cases'] and results(directory, a) == results(directory, b):
            failures.append(a + '/' + b + ': sampling/seed has no effect')
    (directory / 'verification.json').write_text(json.dumps({'failures': failures}, indent=2) + '\n')
    print(json.dumps(failures, indent=2))
    return bool(failures)


def compare(left, right):
    manifests = [json.loads((p / 'manifest.json').read_text()) for p in (left, right)]
    result, diffs = {}, []
    for name in sorted(manifests[0]['cases'].keys() | manifests[1]['cases'].keys()):
        if not all(name in m['cases'] for m in manifests):
            result[name] = 'not selected'; continue
        a, b = [m['cases'][name] for m in manifests]
        errors = []
        if a.get('returncode') != b.get('returncode'): errors.append('exit')
        for stream in ('stdout', 'stderr', *(('helperlog',) if a.get('helper_log') or b.get('helper_log') else ())):
            paths = [p / f'{name}.{stream}' for p in (left, right)]
            if not all(p.exists() for p in paths): errors.append(stream + ': missing'); continue
            x, y = [normalized(p.read_bytes(), m['binary_dir']) for p, m in zip(paths, manifests)]
            if x != y:
                errors.append(stream)
                diffs.extend(difflib.unified_diff(x.splitlines(True), y.splitlines(True),
                    fromfile=f'left/{name}.{stream}', tofile=f'right/{name}.{stream}'))
        if a['files'] != b['files']: errors.append('scientific files')
        result[name] = errors or 'exact'
    (right / ('comparison-' + left.name + '.json')).write_text(json.dumps(result, indent=2) + '\n')
    (right / ('comparison-' + left.name + '.diff')).write_text(''.join(diffs), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return any(isinstance(v, list) for v in result.values())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bin', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--select', default='.')
    parser.add_argument('--probe', type=Path)
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--compare', nargs=2, type=Path)
    args = parser.parse_args()
    if args.verify: sys.exit(verify(args.verify.resolve()))
    if args.compare: sys.exit(compare(*[p.resolve() for p in args.compare]))
    if args.bin and args.output:
        run(args.bin.resolve(), args.output.resolve(), args.select, args.probe.resolve() if args.probe else None)
    else: parser.error('use --bin DIR --output NEW_DIR, --verify DIR, or --compare DIR DIR')
