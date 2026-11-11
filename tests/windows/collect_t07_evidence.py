"""Collect T07 evidence without turning reproduced upstream bugs into passes."""
import argparse
from fractions import Fraction
import gzip
import json
from pathlib import Path
import re
import subprocess
import tarfile

from audit_qpdstat import normal, sha

ROOT=Path(__file__).resolve().parents[2]


def collect(raw,output):
    names=('windows-initial','windows-final','pristine','port-linux','asan-recover','coverage')
    manifests={n:json.loads((raw/n/'manifest.json').read_text()) for n in names}
    assert all(m['completed'] for m in manifests.values())
    assert all(len(m['cases'])==(121 if n.startswith('windows') else 120) for n,m in manifests.items())
    result=dict(id='T07',date='2026-11-12',status='reviewed with open compatibility differences and deferred upstream defects',
                parity_certified=False,upstream=(ROOT/'UPSTREAM_BASELINE').read_text().strip(),
                working_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
                raw_root=str(raw.relative_to(ROOT)).replace('\\','/'),matrices={},comparisons={},checks={},builds={})
    for name,m in manifests.items():
        oracles={n:m['cases'][n]['rows']==rows for n,rows in m['oracles'].items()}
        assert len(oracles)==11 and all(oracles.values())
        assert m['packed_roundtrip_exact']
        result['matrices'][name]=dict(binary_dir=m['binary_dir'],environment=m['environment'],executables=m['executables'],
            cases={n:{k:c[k] for k in ('tool','arguments','returncode','timeout','rows','sanitizer','temporaries',
                    'external_temporaries','files') if k in c} | {'streams':{s:sha(raw/name/(n+'.'+s)) for s in ('stdout','stderr')}}
                    for n,c in m['cases'].items()},oracles=oracles,manifest_sha256=sha(raw/name/'manifest.json'))
    a,b=manifests['pristine'],manifests['windows-final']
    finite=[n for n,c in a['cases'].items() if n in b['cases'] and c['tool']=='qp4diff' and
            c.get('returncode')==b['cases'][n].get('returncode')==0 and c['rows'] and
            not any(re.fullmatch(r'[+-]?(nan|inf)',v,re.I) for row in c['rows'] for v in row)]
    assert len(finite)==69 and all(a['cases'][n]['rows']==b['cases'][n]['rows'] for n in finite)
    result['checks']['joint_finite_qp4diff_cases']=dict(count=len(finite),exact=finite,
        scientific_row_count=sum(len(a['cases'][n]['rows']) for n in finite))
    for left,right in [('windows-initial','windows-final'),('pristine','windows-final'),('pristine','port-linux'),
                       ('port-linux','asan-recover'),('port-linux','coverage')]:
        path=raw/right/('comparison-'+left+'.json')
        comparison=json.loads(path.read_text())
        result['comparisons'][left+' vs '+right]=dict(total=len(comparison),exact=sum(not v for v in comparison.values()),
             differences={n:v for n,v in comparison.items() if v},sha256=sha(path))
    changes=result['comparisons']['windows-initial vs windows-final']['differences']
    assert changes=={'cli-invalid-option':['stderr'],'cli-missing-value':['stderr'],
                    'forward-paths':['stdout'],'space-paths':['stdout'],'unicode-paths':['stdout']}
    result['checks']['scientific_rows_unchanged_by_fix']=True
    source=(ROOT/'src/qp4diff.c').read_text().replace('#include <admix_platform.h>\n','',1)
    source=source.replace('"470" ADMIX_VERSION_SUFFIX','"470"')
    source=re.sub(r'#ifdef _WIN32\n  while \(\(i = admix_getopt \(argc, argv, "p:vVh"\)\) != -1\) \{\n#else\n'
                  r'(  while \(\(i = getopt \(argc, argv, "p:vVh"\)\) != -1\) \{)\n#endif',r'\1',source)
    upstream=subprocess.check_output(['git','show',result['upstream']+':src/qp4diff.c'],cwd=ROOT,text=True)
    assert [s.rstrip() for s in source.splitlines()]==[s.rstrip() for s in upstream.splitlines()]
    result['checks']['qp4diff_source_changes_only_platform_include_suffix_windows_getopt']=True
    for label in ('pristine','linux','asan'):
        p=raw/'builds'/('build-'+label+'.json'); record=json.loads(p.read_text())
        assert not record['source_mismatches']
        result['builds'][label]=record
    result['builds']['coverage']=json.loads((raw/'final-build/build-coverage.json').read_text())
    result['builds']['windows']=json.loads((raw/'final-build/snapshot/bin/windows-build.json').read_text())
    sources=result['builds']['windows']['source_sha256']
    result['checks']['windows_source_mismatches']=[p for p,h in sources.items() if sha(ROOT/'src'/p)!=h]
    assert not result['checks']['windows_source_mismatches']
    result['direct']={name:json.loads((raw/('direct-final-'+name)/'results.json').read_text())
                      for name in ('windows','linux','asan')}
    result['checks']['rng_800000_values_sha256']={n:sha(raw/('direct-final-'+n)/'rng.stdout') for n in result['direct']}
    assert len(set(result['checks']['rng_800000_values_sha256'].values()))==1
    result['checks']['rounding_equal_key_sort_sha256']={n:sha(raw/('direct-final-'+n)/'platform.stdout') for n in result['direct']}
    assert len(set(result['checks']['rounding_equal_key_sort_sha256'].values()))==1
    a,b=Fraction(3,12),Fraction(7,12)
    expected=('ordinary 1 '+f'{float((a-b)*(Fraction(4,12)-Fraction(9,12))):.12f}'+'\n'+
              'overlap 1 '+f'{float((a-b)**2-(a*(1-a)+b*(1-b))/11):.12f}'+'\n'+
              'NULL 2 1.000000000000\nlarge 1 '+f'{float(-Fraction(1,2)/(2*2147483647-1)):.12f}'+'\n')
    result['checks']['direct_fraction_oracle']={n:normal((raw/('direct-final-'+n)/'f4.stdout').read_bytes())==expected for n in result['direct']}
    assert all(result['checks']['direct_fraction_oracle'].values())
    for name,m in result['direct'].items():
        for case in ('f4','lifetime','lifetime-nonoverlap','platform','rng','largefile'):
            assert m['cases'][case]['returncode']==0 and not m['cases'][case]['sanitizer']
    result['native']=json.loads((raw/'native-final/results.json').read_text(encoding='utf-8-sig'))
    assert all(result['native'][k] for k in ('tee_equal','gzip_equal','stderr_empty','native_temp_path','long_gzip_equal','long_temp_clean'))
    assert result['native']['long_temp_path_length']>260 and result['native']['long_gzip_exit']==0
    result['compiler_inventory']=dict(path='tests/windows/audits/T07_modules.inventory.json',
        sha256=sha(raw/'static-windows/inventory.json'))
    result['coverage']=json.loads(gzip.decompress((raw/'coverage-counters/qp4diff.gcov.json.gz').read_bytes()))
    result['checks']['pristine_source_count']=len(result['builds']['pristine']['sources'])
    result['checks']['fixture_sha256']={name:{f:sha(raw/name/'fixtures'/f) for f in ('input.geno','input.snp','input.ind','output.geno','input.tgeno','roundtrip.geno')}
                                         for name in names}
    for f in result['checks']['fixture_sha256'][names[0]]:
        assert len({v[f] for v in result['checks']['fixture_sha256'].values()})==1
    result['installed_binary']=dict(path='bin/qp4diff.exe',sha256=sha(ROOT/'bin/qp4diff.exe'),replaced=False)
    result['harness_sha256']={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in
        [ROOT/'tests/windows'/n for n in ('audit_qp4diff.py','build_t07_audit.py','build_t07_probe.py',
          'qp4diff_probe.c','run_t07_probes.py','t07_native_checks.ps1','collect_t07_evidence.py')]}
    result['harness_dependency_sha256']={'tests/windows/'+name:sha(ROOT/'tests/windows'/name) for name in
        ('parity.py','audit_qpdstat.py','build_t04_audit.py','build_t04_probes.py','inventory_t04_modules.py',
         'platform_probe.c','largefile_probe.c')}
    result['open_compatibility_findings']=['F088','F089']
    result['deferred_upstream_findings']=['F017','F048','F050','F051','F073','F083','F084','F086','F090']
    result['limitations']=['independent M/H/Q audits pending','6/11 functions; incomplete branches and unflushed aborts',
        'no native Windows sanitizer or macOS build','no real >4 GiB genotype or exhaustive size products',
        'X compatibility checked; no independent sex-aware T07 oracle','installed binary unchanged']
    archive=raw/'raw-evidence.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for directory in (*names,'direct-final-windows','direct-final-linux','direct-final-asan','native-final','static-windows','coverage-counters'):
            for p in sorted((raw/directory).iterdir()):
                if p.is_file() and (p.suffix in ('.stdout','.stderr','.json','.diff','.txt','.gz','.aux')):
                    tar.add(p,arcname=str(p.relative_to(raw)),recursive=False)
        for directory in ('builds','final-build'):
            for p in sorted((raw/directory).iterdir()):
                if p.is_file(): tar.add(p,arcname=str(p.relative_to(raw)),recursive=False)
    result['raw_archive']=dict(path=str(archive.relative_to(ROOT)).replace('\\','/'),sha256=sha(archive),bytes=archive.stat().st_size)
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(output, '69 finite cases exact; open differences retained',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();collect(a.raw.resolve(),a.output.resolve())
