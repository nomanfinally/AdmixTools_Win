"""Collect T05 raw records and focused defect probes; run under WSL.

Requires completed audit matrices. Never repairs production sources or changes
scientific tolerances. Paths are explicit so another machine can reproduce it.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import audit_qp3pop as audit
import audit_qpdstat as shared
import audit_t04_modules as modules

ROOT=Path(__file__).resolve().parents[2]

def write(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')

def record(path):
    m=json.loads((path/'manifest.json').read_text())
    if not m['completed']:raise RuntimeError('incomplete matrix: '+str(path))
    for name,c in m['cases'].items():
        c['streams']={s:dict(sha256=audit.sha(path/f'{name}.{s}'),bytes=(path/f'{name}.{s}').stat().st_size) for s in ('stdout','stderr')}
    return dict(path=str(path),manifest_sha256=audit.sha(path/'manifest.json'),
                manifest=m,verification=json.loads((path/'verification.json').read_text()))

def supplements(base):
    output=base/'supplements';output.mkdir(exist_ok=False)
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_CORETYPE='NEHALEM',LC_ALL='C',
             ASAN_OPTIONS='detect_leaks=0:abort_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    results={}
    jobs=[('float-current',base/'probes-float-asan/qp3pop_probe',['inbreed-large'],None),
          ('float-pristine',base/'probes-float-pristine/qp3pop_probe',['inbreed-large'],None),
          ('early-leaks',base/'probes-final-asan/qp3pop_probe',['early-return'],None)]
    for platform in ('linux','pristine','asan'):
        for kind in ('full-file','fixed-inbreed','fixed-outgroup'):
            jobs.append((kind+'-'+platform,base/platform/'src/qp3Pop',['-p','par'],kind))
    for name,exe,args,kind in jobs:
        work=output/name
        if kind:
            fixture='details' if kind=='full-file' else 'fixed-target'
            shutil.copytree(base/'complete-linux'/fixture,work)
            par=(work/'par').read_text()
            if kind=='full-file':par=par.replace('details.out','/dev/full')
            elif kind=='fixed-inbreed':par=par.replace('inbreed_override: YES\n','')+'inbreed: YES\n'
            else:par+='outgroupmode: YES\n'
            (work/'par').write_text(par)
        else:work.mkdir()
        selected=dict(env,ASAN_OPTIONS='detect_leaks=1:abort_on_error=1') if name=='early-leaks' else env
        p=subprocess.run([str(exe),*args],cwd=work,env=selected,capture_output=True,timeout=30,preexec_fn=shared.no_core)
        for s,data in zip(('stdout','stderr'),(p.stdout,p.stderr)):(output/f'{name}.{s}').write_bytes(data)
        results[name]=dict(executable=str(exe),executable_sha256=audit.sha(exe),args=args,returncode=p.returncode,
            stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),stderr_sha256=hashlib.sha256(p.stderr).hexdigest(),
            stdout=p.stdout.decode(errors='surrogateescape'),stderr=p.stderr.decode(errors='surrogateescape'))
    write(output/'results.json',results)
    return results

def collect(win,linux,output):
    output.mkdir(parents=True,exist_ok=False)
    evidence=dict(id='T05',date='2026-11-10',status='reviewed with open defects; not passed',
        upstream_commit=(ROOT/'UPSTREAM_BASELINE').read_text().strip(),
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
        production_changes=[],runs={},comparisons={})
    snapshot=json.loads((win/'builds/snapshot.json').read_text())
    evidence['snapshot']=snapshot
    evidence['production_snapshot_mismatches']=[p for p,h in snapshot['sources'].items() if audit.sha(ROOT/p)!=h]
    if evidence['production_snapshot_mismatches']:raise RuntimeError('source snapshot mismatch')
    evidence['builds']={n:json.loads((win/f'builds/build-{n}.json').read_text()) for n in ('linux','pristine','asan','coverage')}
    evidence['windows_build']=json.loads((win/'builds/snapshot/bin/windows-build.json').read_text())
    evidence['windows_environment']=(win/'windows-environment.txt').read_text()
    evidence['upstream_source_url']='https://github.com/DReichLab/AdmixTools/blob/'+evidence['upstream_commit']+'/src/qp3Pop.c'
    evidence['notes']=[
        'Only complete-* matrices are authoritative. Earlier diagnostic runs retained initial oracle/fixture/probe revisions; the inbred correction, X block-label fixture and large-probe expectation were corrected before complete-* runs.',
        'The independent mixed-X discrepancy remains a scientific finding (F082), not a normalized exception.',
        'Whole-process matrix leak checks are disabled; the dedicated early-return supplemental probe enables LeakSanitizer.',
        'Initial Windows shared-probe build lacked objects for its unused qpWave mapping injection job. The final shared builder uses --skip-map explicitly and succeeds; the original failure is retained as a harness setup issue, not a production failure. Actual mapping and large-offset service checks ran.']
    # Record the actual qp3Pop linkage, replacing the historical T04 ldd entry.
    commands=[['uname','-a'],['gcc','--version'],['gcc','-dumpmachine'],['pkg-config','--modversion','gsl'],
              ['dpkg-query','-W','libgsl28','libopenblas0-pthread','zlib1g'],['ldd',str(linux/'linux/src/qp3Pop')]]
    evidence['linux_environment']={repr(c):subprocess.check_output(c,text=True) for c in commands}
    # OpenBLAS config exposes the integer ABI; qp3Pop uses no new matrix ABI.
    import ctypes
    lib=ctypes.CDLL('libopenblas.so.0');lib.openblas_get_config.restype=ctypes.c_char_p
    evidence['openblas_linux_config']=lib.openblas_get_config().decode()
    paths={'windows':win/'complete-windows',**{n:linux/('complete-'+n) for n in ('linux','pristine','asan','coverage')}}
    for n,p in paths.items():
        audit.verify(p);evidence['runs'][n]=record(p)
    for a,b in [('linux','windows'),('linux','pristine'),('linux','asan'),('linux','coverage')]:
        audit.compare(paths[a],paths[b]);evidence['comparisons'][a+'__'+b]=json.loads((paths[b]/('comparison-'+paths[a].name+'.json')).read_text())
    for n,p in [('windows',win/'modules-windows-final'),('linux',linux/'modules-linux'),('asan',linux/'modules-asan')]:
        modules.verify(p);evidence['runs']['modules-'+n]=record(p)
    for a,b in [('linux','windows'),('linux','asan')]:
        left=linux/'modules-linux';right=win/'modules-windows-final' if b=='windows' else linux/'modules-asan'
        shared.compare(left,right)
        evidence['comparisons']['modules-'+a+'__'+b]=json.loads((right/('comparison-'+left.name+'.json')).read_text())
    evidence['native_powershell']=json.loads((win/'native-powershell-final/results.json').read_text(encoding='utf-8-sig'))
    evidence['supplements']=supplements(linux)
    gcov=output/'gcov';gcov.mkdir()
    datafiles=list((linux/'coverage').rglob('*.gcda'))+list((linux/'probes-final-coverage').glob('*.gcda'))
    with (gcov/'run.log').open('w') as log:
        subprocess.run(['gcov','--json-format',*[str(p) for p in datafiles]],cwd=gcov,stdout=log,stderr=subprocess.STDOUT,check=True)
    coverage={}
    for p in gcov.glob('*.gcov.json.gz'):
        for f in json.loads(gzip.decompress(p.read_bytes()))['files']:
            name=Path(f['file']).name
            for function in f['functions']:
                coverage.setdefault(name,{}).setdefault(function['name'],0)
                coverage[name][function['name']]+=function['execution_count']
    evidence['coverage']=coverage
    evidence['coverage_note']='Aggregate instrumented diagnostic and completed matrices. Execution counts show reachability only, not completed function or branch contracts.'
    inventory=json.loads((win/'static-windows/inventory.json').read_text())
    for mid,module in inventory['modules'].items():
        for f in module['functions']:f['linux_execution_count']=coverage.get(Path(module['source']).name,{}).get(f['name'])
    inventory.update(upstream=evidence['upstream_commit'],head=evidence['head'],status='scoped connected-module review; independent M/H audits pending')
    write(output/'T05_modules.inventory.json',inventory)
    evidence['harness_sha256']={str(p.relative_to(ROOT)):audit.sha(p) for p in (ROOT/'tests/windows').glob('*t05*') if p.is_file()}
    for name in ('audit_qp3pop.py','qp3pop_probe.c','build_t04_probes.py'):evidence['harness_sha256']['tests/windows/'+name]=audit.sha(ROOT/'tests/windows'/name)
    evidence['open_findings']=['F044','F045','F048','F050','F051',*[f'F{i:03d}' for i in range(74,83)]]
    write(output/'T05_qp3Pop.evidence.json',evidence)
    print('evidence',output,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--windows-base',type=Path,required=True);p.add_argument('--linux-base',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();collect(a.windows_base.resolve(),a.linux_base.resolve(),a.output.resolve())
