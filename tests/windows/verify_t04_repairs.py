"""Record T04 repair verification without replacing historical audit evidence.

Run under WSL so both native Linux and mounted Windows evidence are readable.
Every output directory must already contain a completed audit manifest.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import audit_qpdstat as tool
import audit_t04_modules as modules
import audit_qpwave as wave

ROOT = Path(__file__).resolve().parents[2]
FINDINGS = ['F024','F044','F045','F048','F050','F051'] + [f'F{i:03d}' for i in range(56,74)]
INTENTIONAL_SCIENCE = {
    'popsizelimit':'F045', 'popsizelimit-repeat':'F045', 'popsizelimit-seed':'F045',
    'popsizelimit-zero':'F045', 'popsizelimit-one':'F045', 'popsizelimit-high':'F045',
    'tree-four':'F056', 'tree-five':'F056', 'oracle-zero':'F060',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(directory):
    return json.loads((directory/'manifest.json').read_text())


def science(left, right, allowed=None):
    a, b = manifest(left), manifest(right)
    exact, changed, excluded, failures = [], {}, [], []
    for name in sorted(a['cases'].keys() & b['cases'].keys()):
        if a['cases'][name].get('returncode') != 0 or b['cases'][name].get('returncode') != 0:
            excluded.append(name)
            continue
        x, y = tool.result_rows(left,name), tool.result_rows(right,name)
        if not x and not y:
            continue
        if x == y:
            exact.append(name)
        else:
            changed[name] = dict(finding=(allowed or {}).get(name), before=x, after=y)
            if name not in (allowed or {}):
                failures.append(name)
    return dict(exact=exact, intentional_changes=changed,
                not_jointly_successful=excluded, unexpected_differences=failures)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('windows','linux','asan','windows-modules','linux-modules','asan-modules',
                 'baseline','pristine','builds','powershell','qpwave-windows','qpwave-linux','output'):
        p.add_argument('--'+name,required=True,type=Path)
    args=p.parse_args()
    if args.output.exists():
        p.error('use a new output evidence file')
    record=dict(upstream=(ROOT/'UPSTREAM_BASELINE').read_text().strip(),
                corrected_findings=FINDINGS, complete_module_audit=False, checks={}, failures=[])
    paths={k:v.resolve() for k,v in vars(args).items()}
    for label in ('windows','linux','asan','windows_modules','linux_modules','asan_modules'):
        directory=paths[label]
        failed=(modules.verify if 'modules' in label else tool.verify)(directory)
        record['checks'][label]=dict(path=str(directory),cases=len(manifest(directory)['cases']),
            manifest_sha256=digest(directory/'manifest.json'),
            verification=json.loads((directory/'verification.json').read_text()))
        if failed:record['failures'].append(label)
    for label in ('qpwave_windows','qpwave_linux'):
        directory=paths[label]
        failed=wave.verify(directory)
        record['checks'][label]=dict(path=str(directory),cases=len(manifest(directory)['cases']),
                manifest_sha256=digest(directory/'manifest.json'),
                verification=json.loads((directory/'verification.json').read_text()))
        if failed:record['failures'].append(label)
    native=json.loads((paths['powershell']/'powershell.json').read_text(encoding='utf-8-sig'))
    record['checks']['powershell']=native
    if any(native[k]!=0 for k in ('direct_exit','tee_exit','gzip_exit')) or not native['result_text_equal'] or not native['gzip_result_text_equal'] or native['temporary_files']:
        record['failures'].append('native PowerShell')
    record['science_windows_linux']=science(paths['linux'],paths['windows'])
    record['science_linux_asan']=science(paths['linux'],paths['asan'])
    record['science_before_repairs']=science(paths['baseline'],paths['windows'],INTENTIONAL_SCIENCE)
    record['science_pinned_pristine']=science(paths['pristine'],paths['linux'],INTENTIONAL_SCIENCE)
    for key,value in list(record.items()):
        if key.startswith('science_') and value['unexpected_differences']:
            record['failures'].append(key)
    # Full terminal and generated-file comparisons retain raw OS abort statuses,
    # format/path extensions and all correlation/tree diagnostics in their diffs.
    for left,right in (('linux','windows'),('linux','asan'),
                       ('baseline','windows'),('pristine','linux'),
                       ('linux_modules','windows_modules'),('linux_modules','asan_modules')):
        tool.compare(paths[left],paths[right])
        compared=paths[right]/('comparison-'+paths[left].name+'.json')
        entries=json.loads(compared.read_text())
        record['checks'][left+'_vs_'+right]=dict(path=str(compared),sha256=digest(compared),
                exact=sum(v=='exact' for v in entries.values()),total=len(entries),
                raw_differences={k:v for k,v in entries.items() if v!='exact'})
    for name in ('M01-rng','M07-hash','M12-packing','M12-small-normal','T04-tree-oracle','T04-banker-large'):
        raw=[(paths[label]/(name+'.stdout')).read_bytes()
             for label in ('windows_modules','linux_modules','asan_modules')]
        if raw[0]!=raw[1] or raw[1]!=raw[2]:record['failures'].append(name+': raw outputs differ')
        record['checks'][name]=dict(stdout_sha256=[hashlib.sha256(x).hexdigest() for x in raw])
    snap=json.loads((paths['builds']/'snapshot.json').read_text())
    record['source_sha256']=snap['sources']
    mismatch=[name for name,value in snap['sources'].items() if digest(ROOT/name)!=value]
    record['source_snapshot_mismatches']=mismatch
    if mismatch:record['failures'].append('source snapshot mismatch')
    record['build_records']={name:json.loads((paths['builds']/('build-'+name+'.json')).read_text())
                            for name in ('linux','asan')}
    for value in record['build_records'].values():
        if value['snapshot_mismatches']:record['failures'].append('Linux build source mismatch')
    record['test_sha256']={str(path.relative_to(ROOT)).replace('\\','/'):digest(path)
        for path in (ROOT/'tests/windows').iterdir() if path.suffix in ('.py','.c','.ps1') and
        ('t04' in path.name or 'qpdstat' in path.name)}
    args.output.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(dict(failures=record['failures'],output=str(args.output)),indent=2))
    return bool(record['failures'])


if __name__=='__main__':
    sys.exit(main())
