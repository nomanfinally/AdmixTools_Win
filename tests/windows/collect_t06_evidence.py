"""Collect T06 evidence under WSL, retaining failures and raw numerical differences.

Run after both platform matrices, shared checks, direct probes and native checks.
No defect is turned into a pass by this collector. Output must be new.
"""
import argparse
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import audit_qpf4ratio as tool

ROOT=Path(__file__).resolve().parents[2]


def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')


def record(p):
    m=read(p/'manifest.json')
    if not m.get('completed',True):raise RuntimeError('incomplete '+str(p))
    result={}
    for n,c in m['cases'].items():
        if 'returncode' not in c or c.get('timeout'):raise RuntimeError('missing/timeout '+n)
        result[n]={**c,'streams':{s:dict(sha256=sha(p/f'{n}.{s}'),bytes=(p/f'{n}.{s}').stat().st_size) for s in ('stdout','stderr')}}
    return dict(path=str(p),manifest_sha256=sha(p/'manifest.json'),count=len(result),environment=m.get('environment'),
                executables=m.get('executables'),cases=result,verification=read(p/'verification.json'))


def science(left,right):
    a,b=[read(p/'manifest.json')['cases'] for p in (left,right)]
    exact=[];changed={};not_joint={};finite_exact=[]
    for n in sorted(a.keys()&b.keys()):
        if a[n]['returncode'] or b[n]['returncode']:
            not_joint[n]=[a[n]['returncode'],b[n]['returncode']];continue
        x,y=tool.rows(left,n),tool.rows(right,n)
        if not x and not y:continue
        if x==y:
            exact.append(n)
            if not any(t.lower() in ('nan','-nan','inf','-inf','+inf') for row in x for t in row):finite_exact.append(n)
        else:changed[n]=dict(left=x,right=y)
    return dict(exact=exact,finite_exact=finite_exact,changed=changed,not_jointly_successful=not_joint)


def isolated_coverage(tree,cases,output):
    """Fresh counters from qpF4ratio only; helper preparations are excluded."""
    output.mkdir(exist_ok=False)
    counters=output/'raw';counters.mkdir()
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',LC_ALL='C',STMP='tmp',GCOV_PREFIX=str(counters))
    m=read(cases/'manifest.json');observed={}
    for n,c in m['cases'].items():
        if c['tool']!='qpF4ratio':continue
        work=cases/n if (cases/n).is_dir() else cases/'fixtures'
        p=subprocess.run(['qpF4ratio',*c['args']],executable=str(tree/'src/qpF4ratio'),cwd=work,env=env,capture_output=True,timeout=20)
        observed[n]=dict(returncode=p.returncode,same_status=p.returncode==c['returncode'])
    # gcov finds counters beside the matching notes, with original absolute source paths.
    sources={}
    for note in (tree/'src').rglob('*.gcno'):
        target=counters/str(note).lstrip('/')
        if target.with_suffix('.gcda').exists():
            shutil.copyfile(note,target)
            p=subprocess.run(['gcov','--json-format','--branch-probabilities','--branch-counts',str(target)],cwd=output,capture_output=True,text=True)
            if p.returncode:raise RuntimeError(p.stderr)
    for path in output.glob('*.gcov.json.gz'):
        data=json.loads(gzip.decompress(path.read_bytes()))
        for f in data['files']:
            try:rel=str(Path(f['file']).relative_to(tree))
            except ValueError:continue
            functions=f.get('functions',[]);lines=f['lines']
            branches=[b for line in lines for b in line.get('branches',[])]
            sources[rel]=dict(functions=len(functions),executed_functions=sum(f['execution_count']>0 for f in functions),
                lines=len(lines),executed_lines=sum(l['count']>0 for l in lines),branches=len(branches),
                executed_branches=sum(b['count']>0 for b in branches),
                function_counts={f['name']:f['execution_count'] for f in functions})
    result=dict(scope='qpF4ratio cases only; fresh GCOV_PREFIX counters; aborted processes may not flush error branches',
                cases=observed,sources=sources)
    save(output/'summary.json',result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('windows-root','linux-root','shared-root','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();win=a.windows_root.resolve();linux=a.linux_root.resolve();shared=a.shared_root.resolve();out=a.output.resolve()
    if out.exists():raise FileExistsError(out)
    snapshot=read(win/'builds/snapshot.json')
    mismatches=[s for s,h in snapshot['sources'].items() if sha(ROOT/s)!=h]
    if mismatches:raise RuntimeError('production changed after snapshot '+repr(mismatches))
    evidence=dict(id='T06',date='2026-11-11',status='reviewed with open defects',complete_module_audit=False,
                  upstream=snapshot['upstream'],working_head=snapshot['head'],source_sha256=snapshot['sources'],
                  source_mismatches=mismatches,matrices={},comparisons={},science={},oracles={})
    dirs=dict(windows=win/'final-windows',linux=linux/'final-linux',pristine=linux/'final-pristine',asan=linux/'final-asan',coverage=shared/'final-coverage')
    evidence['builds']={n:read(win/f'builds/build-{n}.json') for n in ('linux','pristine','asan','coverage')}
    for n,b in evidence['builds'].items():
        if b.get('snapshot_mismatches') or b.get('upstream_mismatches'):raise RuntimeError('build/source mismatch '+n)
    evidence['windows_build']=read(win/'builds/snapshot/bin/windows-build.json')
    evidence['linux_environment']=(win/'builds/linux-environment.txt').read_text()
    for n,d in dirs.items():
        tool.verify(d);evidence['matrices'][n]=record(d)
        m=read(d/'manifest.json')
        evidence['oracles'][n]=dict(expected=m['oracles'],failed={k:dict(expected=v,actual=tool.rows(d,k)) for k,v in m['oracles'].items() if tool.rows(d,k)!=v})
    for left,right in [('linux','windows'),('linux','pristine'),('linux','asan'),('linux','coverage')]:
        tool.compare(dirs[left],dirs[right]);label=left+'-'+right
        result=read(dirs[right]/('comparison-'+dirs[left].name+'.json'))
        evidence['comparisons'][label]=dict(exact=sum(not v for v in result.values()),total=len(result),differences={k:v for k,v in result.items() if v})
        evidence['science'][label]=science(dirs[left],dirs[right])
    evidence['shared']={n:record(d) for n,d in dict(windows=win/'shared-windows',linux=shared/'shared-linux',asan=shared/'shared-asan').items()}
    evidence['direct']={n:read(d/'results.json') for n,d in dict(windows=win/'direct-windows',linux=linux/'direct-linux',asan=linux/'direct-asan').items()}
    if any(v['verification']['failures'] for v in evidence['shared'].values()):raise RuntimeError('shared verification failed')
    if any(v['failures'] for v in evidence['direct'].values()):raise RuntimeError('direct probe failed')
    evidence['native_powershell']=read(win/'native-powershell-final/results.json')
    evidence['coverage']=isolated_coverage(shared/'coverage',dirs['coverage'],shared/'isolated-tool-coverage')
    evidence['production_diff']=subprocess.check_output(['git','diff',snapshot['upstream'],'--','src/qpF4ratio.c'],cwd=ROOT,text=True)
    evidence['audit_script_sha256']={str(s.relative_to(ROOT)):sha(s) for s in (ROOT/'tests/windows').iterdir() if 't06' in s.name.lower() or 'qpf4ratio' in s.name.lower()}
    evidence['original_windows_matrix']=record(win/'original-windows')
    evidence['cli_repair_matrix']=record(win/'windows')
    before=read(win/'original-windows/manifest.json');after=read(win/'windows/manifest.json')
    evidence['cli_repair_scientific_changes']=[n for n in before['cases'] if before['cases'][n]['rows']!=after['cases'][n]['rows']]
    # Portable raw inputs/streams, executable bytes and coverage; prior evidence remains untouched.
    archive=win/'linux-evidence.tar.gz'
    with tarfile.open(archive,'x:gz') as tar:
        for n,d in dirs.items():
            if n!='windows':tar.add(d,arcname='results/'+n)
        for n in ('linux','asan','pristine'):
            tar.add(linux/n/'src/qpF4ratio',arcname='executables/'+n+'/qpF4ratio')
        for n in ('direct-linux','direct-asan'):tar.add(linux/n,arcname=n)
        for n in ('shared-linux','shared-asan','isolated-tool-coverage'):tar.add(shared/n,arcname=n)
    evidence['linux_raw_archive']=dict(path=str(archive),sha256=sha(archive),bytes=archive.stat().st_size)
    save(out,evidence)
    print(json.dumps(dict(cases={n:v['count'] for n,v in evidence['matrices'].items()},
         science={n:dict(exact=len(v['exact']),finite_exact=len(v['finite_exact']),changed=list(v['changed'])) for n,v in evidence['science'].items()},
         oracle_failures={n:list(v['failed']) for n,v in evidence['oracles'].items()},coverage=evidence['coverage']['sources'].get('src/qpF4ratio.c')),indent=2))


if __name__=='__main__':main()
