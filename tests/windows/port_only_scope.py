"""Pristine-Linux oracle for the compatibility-only scope restoration.

No repaired-science expectations or broad floating-point tolerances. Raw stream
differences, failure codes and generated-file hashes are retained for review.
"""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import random
import shutil
import subprocess
import sys
import tarfile

import compatibility
import parity

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = (ROOT / 'UPSTREAM_BASELINE').read_text().strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_linux(destination):
    """Fresh pinned source and a separate current-port Linux build."""
    destination.mkdir(exist_ok=False, parents=True)
    tools = sorted({tool for _, tool, _ in parity.cases()})
    for name in ('pristine', 'port'):
        target = destination / name
        target.mkdir()
        if name == 'pristine':
            data = subprocess.check_output(['git', 'archive', UPSTREAM, 'src'], cwd=ROOT)
            with tarfile.open(fileobj=io.BytesIO(data)) as archive:
                archive.extractall(target, filter='data')
        else:
            shutil.copytree(ROOT / 'src', target / 'src',
                            ignore=shutil.ignore_patterns('.windows', '*.o', '*.a', '__pycache__'))
        flags = 'CFLAGS=-std=gnu11 -ffp-contract=off -fno-fast-math'
        commands = [['make', '-j2', flags], ['make', '-j4', *tools, flags, 'LDLIBS=-lnick']]
        with (destination / ('build-' + name + '.log')).open('w') as log:
            for command, directory in zip(commands, (target/'src/nicksrc', target/'src')):
                log.write(repr(command) + '\n'); log.flush()
                subprocess.run(command, cwd=directory, stdout=log, stderr=subprocess.STDOUT, check=True)
        # qpfit is outside the 26-tool suite and has a conflicting declaration
        # in pristine source. Isolate its one build-only declaration correction.
        source = target / 'src/qpfit.c'
        before = source.read_bytes()
        if name == 'pristine':
            assert b'void addscaldiag(double *mat, double scal, int n)' in before
            source.write_bytes(before.replace(b'void addscaldiag(double *mat, double scal, int n)',
                                              b'int addscaldiag(double *mat, double scal, int n)'))
        with (destination / ('build-' + name + '-qpfit.log')).open('w') as log:
            subprocess.run(['make', 'qpfit', flags, 'LDLIBS=-lnick'], cwd=target/'src', stdout=log, stderr=subprocess.STDOUT, check=True)
        # Retain the exact reference source after producing the isolated binary.
        source.write_bytes(before)
        (destination / ('build-' + name + '.json')).write_text(json.dumps({
            'upstream': UPSTREAM, 'root': str(target), 'commands': commands,
            'sources': {str(p.relative_to(target)): sha(p) for p in (target/'src').rglob('*')
                        if p.suffix in ('.c', '.h')},
            'executables': {tool: sha(target/'src'/tool) for tool in [*tools, 'qpfit']},
            'qpfit_only_build_exception': 'void -> int addscaldiag declaration; upstream exit before fitting retained'
                if name == 'pristine' else None}, indent=2) + '\n')
        print(name, target/'src', flush=True)


def run(binary_dir, output, selection='.'):
    output.mkdir(parents=True, exist_ok=False)
    common = output / 'fixtures'
    parity.fixtures(common)
    rng = random.Random(8107)
    signal = []
    for _ in range(2200):
        base, drift, extra = rng.uniform(.3,.7), rng.choice((-.22,.22)), rng.uniform(-.1,.1)
        a,b = base+drift,base-drift
        frequencies = (base,a,b,base+extra,.6*a+.4*b,a+extra,b+extra,base+.5*drift,base-.5*drift)
        signal.append(''.join(str(int(rng.random()<f)+int(rng.random()<f))
                              for f in frequencies for _ in range(6))+'\n')
    (common/'signal.geno').write_text(''.join(signal),encoding='ascii',newline='\n')
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
               OPENBLAS_CORETYPE='NEHALEM', LC_ALL='C', STMP='tmp')
    env['PATH'] = str(binary_dir) + os.pathsep + env.get('PATH', '')
    result = {'upstream': UPSTREAM, 'binary_dir': str(binary_dir), 'platform': sys.platform,
              'environment': {k:env[k] for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','OPENBLAS_CORETYPE','LC_ALL','STMP')},
              'executables': {}, 'cases': {}, 'completed': False}
    cases = []
    for tool in ('qpAdm','qpfstats','qpWave','qpDstat','qp3Pop','qpF4ratio'):
        for label, extra in [('ordinary', ''), ('limited-77', 'popsizelimit: 3\n'),
                             ('limited-123', 'popsizelimit: 3\n'),
                             ('inactive-output', 'output: ignored.out\n'),
                             ('partial-number', ''), ('duplicate-ids', ''), ('x-mixed', '')]:
            cases.append((tool+'-'+label, tool, label, extra))
        for option in ('-v','-h','-?'):
            label = 'invalid' if option == '-?' else option[1:]
            cases.append((tool+'-cli-'+label, tool, option, ''))
    cases += [('qpAdm-maxrank', 'qpAdm', 'maxrank', 'maxrank: 1\n'),
              ('qpAdm-no-sampler-cap', 'qpAdm', 'maxreject', 'maxreject: 0\n'),
              ('qpfit-early-exit','qpfit','cached-exit','fstatsname: cached.fstats\n'),
              ('qpAdm-auto', 'qpAdm', 'auto', 'allsnps: YES\n'),
              ('qpWave-auto', 'qpWave', 'auto', 'allsnps: YES\n'),
              ('qpAdm-gzip','qpAdm','gzip',''),
              ('qp3Pop-gzip','qp3Pop','gzip','')]
    cases += [('qpAdm-bayes','qpAdm','bayes','newmode: YES\nmctrials: 200\n'),
              ('qpAdm-bayes-positive','qpAdm','bayes','newmode: YES\nmctrials: 200\npositive_coeffs: YES\n'),
              ('qpAdm-bayes-ignored-cap','qpAdm','bayes','newmode: YES\nmctrials: 200\npositive_coeffs: YES\nmaxreject: 0\n'),
              ('qpAdm-single-auto','qpAdm','single-auto','allsnps: YES\nnumboot: 5\n')]
    if os.name == 'nt':
        cases += [('qpAdm-win-unicode', 'qpAdm', 'unicode', ''),
                  ('qpAdm-win-unicode-auto', 'qpAdm', 'unicode-auto', 'allsnps: YES\n'),
                  ('qpAdm-win-long-temp', 'qpAdm', 'long-temp', 'allsnps: YES\n'),
                  ('qpAdm-win-bom', 'qpAdm', 'bom', ''),
                  ('qpAdm-win-crlf', 'qpAdm', 'crlf', '')]
    for name,tool,mode,extra in cases:
        if not re.search(selection, name): continue
        work = output / ('work ' + name)
        shutil.copytree(common, work)
        (work/'tmp').mkdir()
        executable = binary_dir / (tool + ('.exe' if os.name == 'nt' else ''))
        result['executables'][tool] = sha(executable)
        args = [mode] if mode.startswith('-') else ['-p','audit.par']
        text = (work/('par.'+('qpAdm' if tool == 'qpfit' else tool))).read_text() + extra
        if mode == 'cached-exit':
            helper = binary_dir / ('qpfstats.exe' if os.name == 'nt' else 'qpfstats')
            prepared = subprocess.run([str(helper), '-p', 'par.qpfstats'], cwd=work,
                                      env=env,capture_output=True,timeout=45)
            assert prepared.returncode == 0, prepared.stderr
            for stream in ('stdout','stderr'):
                (output/('prepare-'+name+'.'+stream)).write_bytes(getattr(prepared,stream))
            (work/'cached.fstats').write_bytes((work/'output.fstats').read_bytes())
        if mode == 'limited-123': text = text.replace('seed: 77', 'seed: 123')
        if mode == 'bayes': text = text.replace('input.geno','signal.geno')
        if mode == 'single-auto': (work/'left').write_text('X\nA\n')
        if mode == 'partial-number': text = text.replace('blgsize: .005', 'blgsize: .005junk')
        if mode == 'duplicate-ids':
            lines = (work/'input.ind').read_text().splitlines()
            lines[1] = lines[1].replace('Out1','Out0')
            (work/'input.ind').write_text('\n'.join(lines)+'\n')
        if mode == 'x-mixed':
            (work/'input.snp').write_text(re.sub(r'^(\S+) \d+ ', r'\1 23 ', (work/'input.snp').read_text(), flags=re.M))
            rows = (work/'input.ind').read_text().splitlines()
            (work/'input.ind').write_text('\n'.join(row.replace(' U ', ' F ' if i%2 else ' M ')
                                                 for i,row in enumerate(rows))+'\n')
            text += 'chrom: 23\n'
        if mode == 'gzip':
            (work/'input.geno.gz').write_bytes(gzip.compress((work/'input.geno').read_bytes(), mtime=0))
            text = text.replace('input.geno','input.geno.gz')
        if mode.startswith('unicode'):
            filename = '日本 & # input.geno'
            (work/filename).write_bytes((work/'input.geno').read_bytes())
            text = text.replace('genotypename: input.geno', 'genotypename: "'+filename+'"')
        if mode == 'long-temp':
            folder = work/'tmp'/('a'*100)/('b'*100)/('c'*100)
            folder.mkdir(parents=True)
            text += 'tmpdir: "'+str(folder)+'"\n'
        data = text.encode('utf-8')
        if mode == 'bom': data = b'\xef\xbb\xbf'+data
        if mode == 'crlf': data = data.replace(b'\n',b'\r\n')
        (work/'audit.par').write_bytes(data)
        try:
            proc = subprocess.run([executable.name,*args], executable=str(executable), cwd=work,
                                  env=env, capture_output=True, timeout=45)
            entry = {'returncode':proc.returncode,'arguments':args}
            for stream in ('stdout','stderr'): (output/(name+'.'+stream)).write_bytes(getattr(proc,stream))
        except subprocess.TimeoutExpired as error:
            entry = {'timeout': True,'arguments':args}
            for stream in ('stdout','stderr'): (output/(name+'.'+stream)).write_bytes(getattr(error,stream) or b'')
        entry['files'] = {p.name:sha(p) for p in work.iterdir() if p.name in ('output.fstats','ignored.out')}
        result['cases'][name] = entry
        (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
        print(name, entry.get('returncode','TIMEOUT'), flush=True)
    result['completed'] = True
    (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')


def normalized(data, binary_dir, name):
    text = compatibility.normalized(data, binary_dir)
    for tool in ('qpAdm','qpfstats','qpWave','qpDstat','qp3Pop','qpF4ratio','qpfit'):
        text = text.replace(tool+'.exe',tool)
    text = re.sub(r'(mmfaddr: )0x[0-9a-f]+',r'\1<ADDRESS>',text)
    if name.endswith('-cli-v'):
        text = re.sub(r'^seed: -?[0-9]+$', 'seed: <AUTO>',text,flags=re.M)
    return text


def compare(left, right):
    a,b = [json.loads((p/'manifest.json').read_text()) for p in (left,right)]
    assert a['completed'] and b['completed']
    result = {}
    for name in sorted(a['cases'].keys() & b['cases'].keys()):
        x,y = a['cases'][name],b['cases'][name]
        errors = []
        if x.get('timeout') or y.get('timeout'): errors.append('timeout')
        if x.get('returncode') != y.get('returncode'): errors.append('exit')
        for stream in ('stdout','stderr'):
            first,second = [normalized((p/(name+'.'+stream)).read_bytes(), m['binary_dir'],name)
                            for p,m in ((left,a),(right,b))]
            if first != second: errors.append(stream)
        if x['files'] != y['files']: errors.append('files')
        result[name] = errors or 'exact'
    (right/('comparison-'+left.name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build-linux', type=Path)
    p.add_argument('--bin', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--compare',nargs=2,type=Path)
    p.add_argument('--select',default='.')
    a = p.parse_args()
    if a.build_linux: build_linux(a.build_linux.resolve())
    elif a.compare: compare(*[v.resolve() for v in a.compare])
    elif a.bin and a.output: run(a.bin.resolve(),a.output.resolve(),a.select)
    else: p.error('use --build-linux, --bin/--output, or --compare')
