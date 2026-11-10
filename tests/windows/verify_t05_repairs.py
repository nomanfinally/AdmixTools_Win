"""Verify T05 repairs and retain evidence without replacing the original audit.

Run under WSL after the native and Linux matrices finish. Raw platform statuses,
streams and deliberate upstream differences remain in the comparison files.
"""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import audit_qp3pop as tool
import audit_qpdstat as dstat
import audit_t04_modules as modules
import audit_qpadm as adm
import audit_qpfstats as fstats
import audit_qpwave as wave

ROOT=Path(__file__).resolve().parents[2]
FINDINGS=['F044','F045','F048','F050','F051']+[f'F{i:03d}' for i in range(74,83)]
SCIENCE_CHANGES={**{n:'F045' for n in ('limit-77','limit-123','limit-repeat','cli-seed')},
                 **{n:'F082' for n in ('xdata','noxdata-no','x-mixed','oracle-x-mixed')}}

def read(path):return json.loads(path.read_text())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=True)+'\n')

def record(directory):
    m=read(directory/'manifest.json')
    if not m.get('completed',True):raise RuntimeError('incomplete '+str(directory))
    cases={}
    for name,c in m['cases'].items():
        if 'returncode' not in c or c.get('timeout') or c.get('unavailable') or c.get('missing'):
            raise RuntimeError('unavailable/timeout '+str(directory)+' '+name)
        fields=('returncode','expect','expected','tool','args','arguments','files','rows','sanitizer','temporaries','external_temporaries')
        cases[name]={k:c[k] for k in fields if k in c}
        cases[name]['streams']={s:dict(sha256=digest(directory/f'{name}.{s}'),bytes=(directory/f'{name}.{s}').stat().st_size) for s in ('stdout','stderr')}
    return dict(path=str(directory),manifest_sha256=digest(directory/'manifest.json'),count=len(cases),
                environment=m.get('environment'),executables=m.get('executables'),cases=cases,
                verification=read(directory/'verification.json'))

def science(left,right,allowed=None,reader=tool.rows):
    a,b=[read(p/'manifest.json')['cases'] for p in (left,right)]
    exact=[];changed={};not_joint={}
    for name in sorted(a.keys()&b.keys()):
        if a[name].get('returncode')!=0 or b[name].get('returncode')!=0:
            not_joint[name]=[a[name].get('returncode'),b[name].get('returncode')];continue
        x,y=reader(left,name),reader(right,name)
        if not x and not y:continue
        if x==y:exact.append(name)
        else:changed[name]=dict(finding=(allowed or {}).get(name),before=x,after=y)
    return dict(exact=exact,changed=changed,unexpected=[n for n in changed if n not in (allowed or {})],not_jointly_successful=not_joint,
                added=sorted(b.keys()-a.keys()),absent=sorted(a.keys()-b.keys()))

def supplements(win,linux,output):
    output.mkdir(exist_ok=False)
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_CORETYPE='NEHALEM',LC_ALL='C',
             ASAN_OPTIONS='detect_leaks=0:abort_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    result={}
    for name,exe,args,fixture,par in [
        ('early-leaks',linux/'probes-verified-asan/qp3pop_probe',['early-return'],None,None),
        ('full-file-linux',linux/'linux/src/qp3Pop',['-p','par'],linux/'verified-linux/details','full'),
        ('full-file-asan',linux/'asan/src/qp3Pop',['-p','par'],linux/'verified-asan/details','full')]:
        work=output/name
        if fixture:
            shutil.copytree(fixture,work)
            (work/'par').write_text((work/'par').read_text().replace('details.out','/dev/full'))
        else:work.mkdir()
        selected=dict(env,ASAN_OPTIONS='detect_leaks=1:abort_on_error=1') if name=='early-leaks' else env
        p=subprocess.run([str(exe),*args],cwd=work,env=selected,capture_output=True,timeout=30,preexec_fn=dstat.no_core)
        for s,data in zip(('stdout','stderr'),(p.stdout,p.stderr)):(output/f'{name}.{s}').write_bytes(data)
        good=(p.returncode==0 and not p.stderr and b'extra open handles: 0' in p.stdout) if name=='early-leaks' else (
            p.returncode!=0 and b'error writing SNP details: /dev/full' in p.stderr and b' result:' not in p.stdout)
        if not good:raise RuntimeError('supplement failed '+name)
        result[name]=dict(returncode=p.returncode,executable_sha256=digest(exe),stdout=p.stdout.decode(),stderr=p.stderr.decode())
    save(output/'results.json',result)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('windows-root','linux-root','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--baseline',type=Path,default=ROOT/'validation-results/hard-check/T05/complete-windows')
    p.add_argument('--pristine',type=Path,default=Path('/home/user/admixtools-t05/complete-pristine'))
    a=p.parse_args();win=a.windows_root.resolve();linux=a.linux_root.resolve();out=a.output.resolve()
    if out.exists():p.error('output evidence file must be new')
    evidence=dict(id='T05',date='2026-11-11',corrected_findings=FINDINGS,complete_module_audit=False,
        upstream=(ROOT/'UPSTREAM_BASELINE').read_text().strip(),working_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        checks={},comparisons={},science={},failures=[])
    snapshot=read(win/'builds/snapshot.json')
    evidence['source_sha256']=snapshot['sources']
    evidence['source_mismatches']=[s for s,h in snapshot['sources'].items() if digest(ROOT/s)!=h]
    if evidence['source_mismatches']:raise RuntimeError('production sources changed after tested snapshot')
    evidence['builds']={n:read(win/f'builds/build-{n}.json') for n in ('linux','asan')}
    evidence['windows_build']=read(win/'builds/snapshot/bin/windows-build.json')
    evidence['linux_environment']=(win/'builds/linux-environment.txt').read_text()
    for n,r in evidence['builds'].items():
        if r['snapshot_mismatches']:raise RuntimeError('build snapshot mismatch '+n)
    paths={'windows':win/'verified-windows','linux':linux/'verified-linux','asan':linux/'verified-asan'}
    families={'modules':modules,'qpdstat':dstat,'qpadm':adm,'qpfstats':fstats,'qpwave':wave}
    with (out.with_suffix('.log')).open('w') as log,contextlib.redirect_stdout(log):
        for n,path in paths.items():
            if tool.verify(path):evidence['failures'].append(n+' behavior')
            evidence['checks'][n]=record(path)
        for family,runner in families.items():
            for platform in ('windows','linux','asan'):
                path=(win if platform=='windows' else linux)/(family+'-'+platform)
                if runner.verify(path):evidence['failures'].append(family+'-'+platform+' behavior')
                evidence['checks'][family+'-'+platform]=record(path)
            for platform in ('windows','asan'):
                left=linux/(family+'-linux');right=(win if platform=='windows' else linux)/(family+'-'+platform)
                (dstat.compare if family=='modules' else runner.compare)(left,right)
                target=right/('comparison.json' if family=='qpadm' else 'comparison-'+left.name+'.json')
                comparisons=read(target)
                evidence['comparisons'][family+'-linux__'+platform]=comparisons
                if family!='qpdstat':
                    for name,value in comparisons.items():
                        if value!='exact' and value not in (['exit'],['not selected on both sides'],'platform-specific/not selected','not selected'):
                            evidence['failures'].append(family+' '+platform+' unexpected raw/file difference '+name)
        for n in ('windows','asan'):
            tool.compare(paths['linux'],paths[n])
            evidence['comparisons']['linux__'+n]=read(paths[n]/'comparison-verified-linux.json')
            result=science(paths['linux'],paths[n])
            evidence['science']['linux__'+n]=result
            if result['unexpected'] or result['absent'] or result['added']:evidence['failures'].append(n+' science/case coverage')
            result=science(linux/'qpdstat-linux',(win if n=='windows' else linux)/('qpdstat-'+n),reader=dstat.result_rows)
            evidence['science']['qpdstat-linux__'+n]=result
            if result['unexpected']:evidence['failures'].append('qpdstat '+n+' science')
        for n,path in [('original-windows',a.baseline.resolve()),('pristine-linux',a.pristine.resolve())]:
            result=science(path,paths['windows'],SCIENCE_CHANGES)
            evidence['science'][n+'__corrected-windows']=result
            if result['unexpected'] or result['absent']:evidence['failures'].append(n+' unexpected science/missing case')
            tool.compare(path,paths['windows'])
            evidence['comparisons'][n+'__corrected-windows']=read(paths['windows']/('comparison-'+path.name+'.json'))
    evidence['supplements']=supplements(win,linux,out.with_suffix('.supplements'))
    native=json.loads((win/'native-powershell/results.json').read_text(encoding='utf-8-sig'))
    evidence['native_powershell']=native
    if not (native['direct_exit']==native['tee_exit']==native['gzip_exit']==0 and native['tee_equal'] and native['gzip_equal'] and native['stderr_empty'] and native['temporary_count']==0):evidence['failures'].append('native PowerShell')
    evidence['installed']=read(win/'installed-checks/results.json')
    evidence['installed_powershell']=json.loads((win/'installed-powershell/results.json').read_text(encoding='utf-8-sig'))
    installed_native=evidence['installed_powershell']
    if not (installed_native['direct_exit']==installed_native['tee_exit']==installed_native['gzip_exit']==0 and installed_native['tee_equal'] and installed_native['gzip_equal'] and installed_native['stderr_empty'] and installed_native['temporary_count']==0):evidence['failures'].append('installed native PowerShell')
    evidence['installed_before_sha256']=read(win/'installed-before.json')
    for path,h in evidence['installed']['windows_build']['source_sha256'].items():
        if digest(ROOT/'src'/path)!=h:evidence['failures'].append('installed source mismatch '+path)
    evidence['harness_sha256']={str(s.relative_to(ROOT)):digest(s) for s in (ROOT/'tests/windows').glob('*t05*') if s.is_file()}
    for name in ('qp3pop_probe.c','audit_qp3pop.py'):evidence['harness_sha256']['tests/windows/'+name]=digest(ROOT/'tests/windows'/name)
    evidence['probe_builds']={n:read((win/'probes-verified-windows' if n=='windows' else linux/('probes-verified-'+n))/'source-sha256.json') for n in ('windows','linux','asan')}
    evidence['pristine_build']=read(ROOT/'validation-results/hard-check/T05/builds/build-pristine.json')
    evidence['original_audit_evidence_sha256']=digest(ROOT/'tests/windows/audits/T05_qp3Pop.evidence.json')
    if evidence['pristine_build']['upstream_mismatches']:evidence['failures'].append('pristine source mismatch')
    evidence['limitations']=['No full-suite certification or completed independent M/H audit.',
        'Pristine qpfit has its retained declaration conflict; original pinned T05 pristine reference was not modified.',
        'X corrections intentionally use declared F diploid and M/U legacy haploid; inbreeding correction and unknown sex are not used to infer sex.',
        'Raw statuses, absolute paths and platform-only inputs remain differences; no scientific tolerance is used.']
    for name,check in evidence['checks'].items():
        expected=167 if name in ('windows','linux','asan') else 91 if name=='modules-windows' else 89 if name.startswith('modules-') else {'qpdstat':145,'qpadm':22,'qpfstats':32,'qpwave':57}[name.split('-')[0]]
        if check['count']!=expected:evidence['failures'].append(name+' incomplete case selection')
    save(out,evidence)
    print(json.dumps(dict(evidence=str(out),failures=evidence['failures'],cases={n:c['count'] for n,c in evidence['checks'].items()}),indent=2))
    return bool(evidence['failures'])

if __name__=='__main__':sys.exit(main())
