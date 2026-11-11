"""Verify T06 corrections without discarding failed pristine scientific rows."""
import argparse,json,sys,hashlib
from pathlib import Path
import audit_qpf4ratio as tool
import audit_t04_modules as modules
import audit_qpdstat as dstat
import audit_qpadm as adm
import audit_qpwave as wave
import audit_qpfstats as fstats
from collect_t06_evidence import read,save,sha,record,science,ROOT

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=a.root.resolve();out=a.output.resolve()
 if out.exists():raise FileExistsError(out)
 e=dict(id='T06',date='2026-11-11',corrected_findings=['F044','F048','F050','F051','F060','F080','F083','F084','F085','F086','F087'],checks={},science={},comparisons={},failures=[])
 e['snapshot']=read(r/'final-builds/snapshot.json')
 if any(sha(ROOT/s)!=h for s,h in e['snapshot']['sources'].items()):raise RuntimeError('source mismatch')
 e['builds']={n:read(r/f'final-builds/build-{n}.json') for n in ('linux','asan')}
 if any(b['snapshot_mismatches'] for b in e['builds'].values()):raise RuntimeError('build source mismatch')
 e['windows_build']=read(r/'final-builds/snapshot/bin/windows-build.json');e['linux_environment']=(r/'final-builds/linux-environment.txt').read_text()
 for plat in ('windows','linux','asan'):
  d=r/('completed-'+plat)
  if tool.verify(d):e['failures'].append(plat+' matrix')
  e['checks'][plat]=record(d);m=read(d/'manifest.json');e['checks'][plat]['oracles']=m['oracles']
  if len(m['cases'])!=225:raise RuntimeError('matrix incomplete')
  if len(m['oracles'])!=50:raise RuntimeError('oracle case count changed')
  d=r/('shared-'+plat if plat=='windows' else 'shared-completed-'+plat)
  if modules.verify(d):e['failures'].append(plat+' shared')
  e['checks']['shared-'+plat]=record(d)
  q=read(r/('direct-'+plat)/'results.json');e['checks']['direct-'+plat]=q
  if q['failures'] or len(q['cases'])!=11:e['failures'].append(plat+' direct')
  d=r/('qpdstat-'+plat)
  if dstat.verify(d):e['failures'].append(plat+' qpDstat')
  e['checks']['qpdstat-'+plat]=record(d)
 for family,runner in [('qpadm',adm),('qpwave',wave),('qpfstats',fstats)]:
  for plat in ('windows','linux','asan'):
   d=r/(family+'-'+plat)
   if runner.verify(d):e['failures'].append(family+' '+plat)
   e['checks'][family+'-'+plat]=record(d)
 for plat in ('windows','asan'):
  l,rgt=r/'completed-linux',r/('completed-'+plat);tool.compare(l,rgt);s=science(l,rgt);e['science'][plat]=s
  e['comparisons'][plat]=read(rgt/'comparison-completed-linux.json')
  if s['changed']:e['failures'].append(plat+' science')
 for label,b in [('original-windows',ROOT/'validation-results/hard-check/T06/final-windows'),('pristine-linux',Path('/home/user/admixtools-t06-final/final-pristine'))]:
  s=science(b,r/'completed-windows');e['science'][label]=s;e[label+'_manifest_sha256']=sha(b/'manifest.json')
  bad=[n for n in s['changed'] if not(n.startswith(('limit-','oracle-x-')) or n in ('xdata','noxdata-no','x-explicit','cli-version-then-run'))]
  if bad:e['failures'].append(label+' unexpected changes '+repr(bad))
 n=read(r/'native-powershell-verified/results.json');e['native']=n
 if not(n['direct_exit']==n['tee_exit']==n['gzip_exit']==0 and n['tee_equal'] and n['gzip_equal'] and n['stderr_empty'] and n['temporary_count']==0 and n['native_temp_path']):e['failures'].append('PowerShell')
 e['installed']=read(r/'installed-checks/results.json')
 e['installed_before']=read(r/'installed-before.json')
 if e['installed']['failures']:e['failures'].append('installed binary')
 n=read(r/'installed-powershell/results.json');e['installed_powershell']=n
 if not(n['direct_exit']==n['tee_exit']==n['gzip_exit']==0 and n['tee_equal'] and n['gzip_equal'] and n['stderr_empty'] and n['temporary_count']==0 and n['native_temp_path']):e['failures'].append('installed PowerShell')
 e['script_sha256']={str(s.relative_to(ROOT)):sha(s) for s in (ROOT/'tests/windows').iterdir() if s.is_file() and ('t06' in s.name.lower() or 'qpf4ratio' in s.name.lower())}
 save(out,e);print(json.dumps(dict(failures=e['failures'],cases={n:c.get('count',len(c.get('cases',{}))) for n,c in e['checks'].items()},science={n:dict(exact=len(s['finite_exact']),changed=list(s['changed'])) for n,s in e['science'].items()}),indent=2))
 return bool(e['failures'])
if __name__=='__main__':sys.exit(main())
