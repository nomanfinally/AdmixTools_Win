"""Assert T08 invariants; retain failures and archive the raw comparison evidence."""
import argparse
import gzip
import json
from pathlib import Path
import re
import subprocess
import tarfile

from audit_qpdstat import sha
from audit_qpgraph import normal
from build_t04_audit import ROOT, UPSTREAM


def collect(raw,output):
    names=('windows-before','windows-final','windows-verified','pristine-final','port-linux-final','asan-recover','coverage',
           'supplement-windows','supplement-pristine','supplement-coverage','supplement-asan',
           'nan-windows','nan-pristine','nan-coverage','nan-asan')
    manifests={n:json.loads((raw/n/'manifest.json').read_text()) for n in names}
    assert all(m['completed'] and m['packed_roundtrip_exact'] for m in manifests.values())
    result=dict(id='T08',date='2026-11-12',status='reviewed with open compatibility differences and deferred upstream defects',
                parity_certified=False,upstream=UPSTREAM,working_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),matrices={},comparisons={},checks={},builds={})
    for name,m in manifests.items():
        result['matrices'][name]=dict(case_count=len(m['cases']),binary_dir=m['binary_dir'],executables=m['executables'],
            environment=m['environment'],manifest_sha256=sha(raw/name/'manifest.json'),
            cases={n:{k:v for k,v in c.items() if k!='inputs'} | {'streams':{s:sha(raw/name/(n+'.'+s)) for s in ('stdout','stderr')}}
                   for n,c in m['cases'].items()})
    fixture_names=('input.geno','input.snp','input.ind','input.fstats','output.geno','input.tgeno','roundtrip.geno')
    result['checks']['fixture_sha256']={n:{f:sha(raw/n/'fixtures'/f) for f in fixture_names} for n in names}
    for f in fixture_names:
        assert len({v[f] for v in result['checks']['fixture_sha256'].values()})==1,f
    a,b=manifests['pristine-final'],manifests['windows-verified']
    finite=[n for n,c in a['cases'].items() if c['tool']=='qpGraph' and c.get('returncode')==0 and c['scores']
            and b['cases'][n].get('returncode')==0]
    assert len(finite)==56 and all(a['cases'][n]['scores']==b['cases'][n]['scores'] for n in finite)
    result['checks']['joint_successful_main_fits']=finite
    # Every scientific output artifact, not just final-score rows.
    artifact_checks={}
    for name in finite:
        artifact_checks[name]={}
        for f in ('graph.out','graph.dot','f3.log','fit.dump','mix.out','outliers'):
            if f not in a['cases'][name]['files'] and f not in b['cases'][name]['files']:
                continue
            x,y=[raw/n/name/f for n in ('pristine-final','windows-verified')]
            assert x.exists() and y.exists()
            same=x.read_bytes().replace(b'\r\n',b'\n')==y.read_bytes().replace(b'\r\n',b'\n')
            artifact_checks[name][f]=same
            assert same,(name,f)
    result['checks']['scientific_artifacts']=artifact_checks
    for n in ('interior-admix','two-admix'):
        x,y=[raw/p/(n+'.stdout') for p in ('supplement-pristine','supplement-windows')]
        assert normal(x.read_bytes())==normal(y.read_bytes()),n
        for f in ('graph.out','graph.dot','f3.log','fit.dump','mix.out','outliers'):
            x,y=[raw/p/n/f for p in ('supplement-pristine','supplement-windows')]
            assert x.read_bytes().replace(b'\r\n',b'\n')==y.read_bytes().replace(b'\r\n',b'\n'),(n,f)
    result['checks']['two_extra_fits_and_artifacts_exact']=True
    result['checks']['initial_nan_fixture_was_unmutated']='Initial matrices retain a mislabeled no-op nan-fstats fixture. Corrected nan-* matrices assert a real substitution; no NaN-domain pass is inferred from the initial row.'
    for n in ('nan-windows','nan-pristine','nan-coverage','nan-asan'):
        assert b'nan' in (raw/n/'nan-fstats/input.fstats').read_bytes()
    for left,right in [('windows-before','windows-final'),('windows-final','windows-verified'),('pristine-final','windows-verified'),
                       ('pristine-final','port-linux-final'),('port-linux-final','asan-recover'),('port-linux-final','coverage'),
                       ('supplement-pristine','supplement-windows'),('supplement-pristine','supplement-coverage'),
                       ('supplement-pristine','supplement-asan'),('nan-pristine','nan-windows'),('nan-pristine','nan-coverage'),('nan-pristine','nan-asan')]:
        p=raw/right/('comparison-'+left+'.json'); c=json.loads(p.read_text())
        result['comparisons'][left+' vs '+right]=dict(total=len(c),exact=sum(not v for v in c.values()),differences={n:v for n,v in c.items() if v},sha256=sha(p))
    for label,directory in [('pristine','builds'),('linux','builds'),('asan','builds'),('coverage','final-build')]:
        record=json.loads((raw/directory/('build-'+label+'.json')).read_text());assert not record['source_mismatches']
        result['builds'][label]=record
    w=json.loads((raw/'verified-build/snapshot/bin/windows-build.json').read_text())
    result['builds']['windows']=w
    result['builds']['windows_environment']=json.loads((raw/'verified-build/windows-environment.json').read_text())
    result['builds']['linux_environment']=(raw/'builds/linux-environment.txt').read_text()
    assert all(sha(ROOT/'src'/p)==h for p,h in w['source_sha256'].items())
    result['checks']['final_native_sources_match_worktree']=True
    # Strip only reviewed adapters; all other primary graph/fit lines must match upstream.
    for name in ('qpGraph','qpgsubs'):
        s=(ROOT/'src'/(name+'.c')).read_text()
        s=s.replace('#include <admix_types.h>\n','',1).replace('#include <admix_platform.h>\n','',1)
        s=s.replace(' ADMIX_VERSION_SUFFIX','').replace('static admix_long ncall','static long ncall')
        if name=='qpGraph':
            s=re.sub(r'#ifdef _WIN32\n  while \(\(i = admix_getopt[^\n]+\n#else\n([^\n]+)\n#endif',r'\1',s)
            start=s.index('#ifdef _WIN32\nvoid mkfstats')
            end=s.index('\n#endif',s.index('\n#else\nvoid mkfstats',start))
            s=s[:start]+s[s.index('void mkfstats',s.index('\n#else\nvoid mkfstats',start)):end]+s[end+len('\n#endif'):]
        else:
            s=re.sub(r'#ifdef _WIN32\n  /\*.*?\*/\n  sprintf \(tmpqq, "graphtt_%d", \(int\) getpid\(\)\);\n#else\n([^\n]+)\n#endif',r'\1',s,flags=re.S)
        u=subprocess.check_output(['git','show',UPSTREAM+':src/'+name+'.c'],cwd=ROOT,text=True)
        assert [l.rstrip() for l in s.splitlines() if l.strip()]==[l.rstrip() for l in u.splitlines() if l.strip()],name
    result['checks']['primary_scientific_sources_equal_upstream_outside_reviewed_adapters']=True
    direct_names=('direct-before','direct-verified','direct-pristine-verified','direct-asan-verified')
    result['direct']={n:json.loads((raw/n/'results.json').read_text()) for n in direct_names}
    for n in ('direct-verified','direct-pristine-verified'):
        assert all(c['returncode']==0 for c in result['direct'][n]['cases'].values())
    for case in ('solve','graph','simplify','delete','lifetime','gsl','platform','rng','largefile'):
        assert (raw/'direct-verified'/(case+'.stdout')).read_bytes()==(raw/'direct-pristine-verified'/(case+'.stdout')).read_bytes(),case
    expected='interior 2.000000000000 3.000000000000 0.000000000000\nboundary 0.000000000000 2.500000000000 1.500000000000\n'
    assert (raw/'direct-verified/solve.stdout').read_text()==expected
    lines=(raw/'direct-verified/graph.stdout').read_text().splitlines()
    vectors=[[-1,1,1,1,0,0,0],[-1,1,1,0,1,0,0],[-1,1,0,0,0,1,0],[-1,1,.6,0,0,.4,1]]
    assert lines[0]=='graph 5 4 7 1'
    for line,label,vector in zip(lines[1:],('A-Out','B-Out','C-Out','X-Out'),vectors):
        assert line==label+' '+ ' '.join(f'{v:.12f}' for v in vector)+' a:0.000000000000'
    assert result['direct']['direct-before']['cases']['simplify']['new_files']==['graphtt']
    assert result['direct']['direct-verified']['cases']['simplify']['new_files']==[]
    result['checks']['independent_solver_and_graph_path_oracles']=True
    result['checks']['rng_800000_values_sha256']=sha(raw/'direct-verified/rng.stdout')
    result['native']=json.loads((raw/'native-corrected/results.json').read_text(encoding='utf-8-sig'))
    assert all(result['native'][k] for k in ('stderr_empty','temp_clean','temp_native','scores_equal','tee_equal','simplify_no_temp','simplify_no_base_file'))
    assert all(result['native'][k]==0 for k in ('direct_exit','tee_exit','auto_exit','gzip_exit','simplify_exit'))
    result['helper_fault']={n:json.loads((raw/n/'results.json').read_text()) for n in ('helper-before','helper-verified','helper-pristine')}
    assert result['helper_fault']['helper-before']['returncode']!=0
    for n in ('helper-verified','helper-pristine'):
        assert result['helper_fault'][n]['returncode']==0 and result['helper_fault'][n]['child_diagnostic']
    assert result['helper_fault']['helper-verified']['final_score']==result['helper_fault']['helper-pristine']['final_score']
    result['coverage']={}
    for p in (raw/'coverage-counters').glob('*.gz'):
        for f in json.loads(gzip.decompress(p.read_bytes()))['files']:
            if not f['file'].endswith('.c'):continue
            result['coverage'][Path(f['file']).name]=dict(functions=len(f['functions']),functions_hit=sum(x['execution_count']>0 for x in f['functions']),
                lines=len(f['lines']),lines_hit=sum(x['count']>0 for x in f['lines']),branches=sum(len(x.get('branches',[])) for x in f['lines']),
                branches_hit=sum(b['count']>0 for x in f['lines'] for b in x.get('branches',[])))
    result['compiler_inventory']=dict(path='tests/windows/audits/T08_modules.inventory.json',sha256=sha(ROOT/'tests/windows/audits/T08_modules.inventory.json'))
    result['installed_binaries']={n:sha(ROOT/'bin'/(n+'.exe')) for n in ('qpGraph','qpfstats','qpreroot')}
    result['installed_binaries_replaced']=False
    harness=('build_t08_audit.py','audit_qpgraph.py','qpgraph_probe.c','gslqp_probe.c','probe_t08.py','t08_native_checks.ps1','helper_t08.py','t08_helper_child.c','collect_t08_evidence.py')
    result['harness_sha256']={n:sha(ROOT/'tests/windows'/n) for n in harness}
    result['harness_dependencies']={n:sha(ROOT/'tests/windows'/n) for n in ('build_t04_audit.py','build_t04_probes.py','audit_qpdstat.py','inventory_t04_modules.py','parity.py','platform_probe.c','largefile_probe.c')}
    result['fixed_findings']=['F044','F091','F092']
    result['open_compatibility_findings']=['F088','F093']
    result['deferred_upstream_findings']=['F017','F037','F048','F051','F086','F094','F095','F096']
    result['limitations']=['incomplete branch/module/header audits','no real cohort or macOS/native Windows sanitizer',
        'sparse offset check is not a real >4 GiB genotype analysis','half-score and malformed-input upstream UB prevent deterministic parity claims',
        'Windows quoted-space/Unicode/BOM extensions are explicit differences','renderer PDF layout not certified by T08',
        'initial no-op NaN case superseded by corrected nan-* fixtures','installed binaries preserved']
    archive=raw/'raw-evidence.tar.gz'
    directories=(*names,*direct_names,'native-corrected','helper-before','helper-verified','helper-pristine','coverage-counters','static-windows','static-final')
    with tarfile.open(archive,'w:gz') as tar:
        for n in directories:
            for p in sorted((raw/n).rglob('*')):
                if p.is_file() and (p.suffix in ('.stdout','.stderr','.json','.diff','.txt','.gz','.aux','.log','.dump','.out','.dot') or p.name in ('par','input.fstats','mix.out','outliers','graph','par.fstats','graphpops')):
                    tar.add(p,arcname=str(p.relative_to(raw)),recursive=False)
        for n in ('builds','native-build','final-build','verified-build'):
            for p in (raw/n).iterdir():
                if p.is_file():tar.add(p,arcname=str(p.relative_to(raw)),recursive=False)
    result['raw_archive']=dict(path=str(archive.relative_to(ROOT)).replace('\\','/'),bytes=archive.stat().st_size,sha256=sha(archive))
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(output,'58 fitting cases and artifacts exact; open differences retained')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();collect(a.raw.resolve(),a.output.resolve())
