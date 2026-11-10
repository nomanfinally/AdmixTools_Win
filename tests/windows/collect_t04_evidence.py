"""Collect T04 evidence (--linux first, then Windows); never certify coverage.

The archive contains the complete final Linux inputs/streams, not filtered logs.
This collector writes reports and inventory artifacts, not production sources.
"""
import argparse
import ctypes
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tarfile

import audit_qpdstat as tool
import audit_t04_modules as modules

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'validation-results/hard-check/T04'
REPORTS=ROOT/'tests/windows/audits'
MODULES={
 'M01':('Native platform services','RNG, binary I/O, line reading, environment, owned temps, gzip, native processes, mapping and diagnostic metrics.',
        'Graph rendering, storage/permission failure combinations, forced termination, handle inheritance isolation and exhaustive allocator-failure injection remain unverified.'),
 'M02':('Strings, files and shell helpers','Tokenization, names/lists, parameter substitution, errors, owned temporary lifecycle and the legacy runcmd shell path.',
        'Obsolete samtools/fgrep/cut/sed and Slurm helpers remain Unix-shell-dependent; no samtools/Slurm environment was provisioned. Their command construction is reviewed, not certified on Windows.'),
 'M03':('Parameter parsing','Scalar parsing, substitutions, includes, include recursion, capacity, long lines, empty fields, CRLF and malformed numeric tokens.',
        'Scalar atoi/atof semantics accept trailing junk/nonfinite values; callers must validate scientific settings. The full family of vector parsers and every include/encoding interaction is not dynamically covered.'),
 'M04':('Gaussian sampling','Fresh-process fixed-seed scalar/array Gaussian sampling and its process-global cached second variate.',
        'SRAND alone does not reset gauss\' cached second variate. Preserve upstream sequence semantics; this audit does not introduce or promise an independent reseed API.'),
 'M05':('Random distributions','Fixed-seed exponential/gamma/beta/Poisson/binomial streams, sampling, permutations and selected zero/equal-bound cases.',
        'Wishart/Dirichlet/truncated-tail and rejection edge contracts are not exhaustively validated; fresh-process equality is not a distributional proof.'),
 'M06':('Sorting and medians','Integer/double equal-key ordering, zero-length rejection, finite medians and short-median allocation lifetimes.',
        'Custom setorder/pointer/string ordering and nonfinite comparator semantics need additional contracts. No new tie policy is proposed here.'),
 'M07':('Hashes and search','Ordinary/extreme signed keys, duplicate original indices, missing lookup, table teardown, 32/64-bit arithmetic.',
        'Sanitizer stops at the first UB; this does not establish absence of further arithmetic/table-capacity defects. Hash values must be preserved by any later unsigned-arithmetic repair.'),
 'M08':('Vectors and diagnostics','Long-width rounding above 32 bits, arithmetic, sums/dots, matrix print diagnostics and memory/timing consumers.',
        'Many generic vector/integer/combinatorial functions remain unexercised; warnings are navigation evidence, not accepted proof of correctness.'),
 'M09':('Statistical routines','Weighted jackknife, zero-weight removal, one-block rejection, normal tail/inverse and scientific consumer paths.',
        'Tail extremes, remaining distributions, Tracy-Widom tables, spectral/correlation helpers and all degeneracies are not independently validated.'),
 'M10':('Linear algebra','Positive-definite solve/inverse, singular return behavior and tree/regression consumers.',
        'Constrained optimizers, all pivot/boundary cases and exhaustive alias/ownership contracts remain untested; no solver or calculation order was changed.'),
 'M11':('Genotype I/O','Text/packed/transposed/ancestry/PED/BED and gzip readers, duplicates, truncation, chromosome filtering and native paths.',
        'No full research dataset, end-to-end >4-GiB scientific analysis, storage-exhaustion matrix or exhaustive historical output-format coverage. Unix gzip temporaries are measured separately.'),
 'M12':('Genotype matrices','Both orientations, all 2-bit values, non-byte-aligned dimensions, padding, hashes, mmap/full reads, malformed headers and output errors.',
        'Bounds/allocation/header and lifetime defects remain. No assertion-free build is certified and no failed-read object ownership contract has been repaired.'),
 'M13':('Mapped file lifecycle','Success, close-before-use, packed element access, missing files, real Linux address-space failure, injected native Windows failure and >4-GiB platform offsets.',
        'Native object-allocation failure after a successful map and external file mutation/truncation races are not injected. Large-file service checks are not an end-to-end scientific run.'),
 'M14':('Population and genotype utilities','Packed-bit round trips, selected populations, actual fixed-seed physical subsets, duplicate-ID validator and genotype access consumers.',
        'Other record mutators, duplicate-detection algorithms and every ownership/index boundary remain outside dynamic coverage; qpDstat does not call the available ID validator.'),
 'M17':('Shared f-statistic and block code','Counts including X ploidy, block definitions/bounds, weighted/Fourier jackknife, selected cached-fstats and automatic qpfstats helper paths.',
        'The full 132-function shared surface is not certified. Fourier is unsafe; cached/helper regression evidence does not validate every estimator or every caller.'),
 'M18':('Population-list helpers','Typed/untyped lists, population mapping, capacity misuse and repeated typed-list file ownership.',
        'Legacy loadlist/loadlist_type have no capacity argument. Caller allocations require validation before writes; descriptor leakage remains unfixed.'),
 'M19':('LD routines','Diploid LD likelihood and z-score, ordinary counts, low/empty counts and scientific callers.',
        'Phased modes, all rare-cell/optimization boundaries and independent likelihood oracles remain untested; exact port/reference output alone is not a statistical proof.'),
 'M20':('Regression utilities','Ordinary least squares, singular matrices, tree fitting and singular diagnostic array lengths.',
        'Logistic fits, constrained weight maximization and their failure/ownership paths remain unexercised. Singular diagnostics contain a reproduced out-of-bounds read.'),
}


def write(path,data):
    path.write_text(json.dumps(data,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')


def record(directory):
    manifest=json.loads((directory/'manifest.json').read_text())
    cases={}
    for name,case in manifest['cases'].items():
        item={k:v for k,v in case.items() if k not in ('inputs',)}
        item['streams']={s:dict(sha256=tool.sha(directory/f'{name}.{s}'),bytes=(directory/f'{name}.{s}').stat().st_size) for s in ('stdout','stderr')}
        if case.get('tool')=='qpDstat':item['scientific_rows']=tool.result_rows(directory,name)
        stderr=(directory/f'{name}.stderr').read_text(errors='replace')
        item['sanitizer']=any(s in stderr for s in ('AddressSanitizer','LeakSanitizer','runtime error:'))
        cases[name]=item
    return dict(path=str(directory),manifest_sha256=tool.sha(directory/'manifest.json'),
        case_count=len(cases),completed=manifest['completed'],environment=manifest['environment'],
        executables=manifest['executables'],cases=cases,
        binary_roundtrip_exact=manifest.get('binary_roundtrip_exact'),packed_roundtrip_exact=manifest.get('packed_roundtrip_exact'),
        oracles=manifest.get('oracles',{}),
        verification=json.loads((directory/'verification.json').read_text()) if (directory/'verification.json').exists() else None)


def linux():
    base=Path.home()/'t04-final'
    selected=['linux','pristine','asan','coverage','modules-linux-complete','modules-pristine-complete',
        'modules-asan-complete','modules-coverage','modules-parser-linux','modules-parser-pristine','modules-parser-asan',
        'cleanup-linux','cleanup-pristine','interaction-linux','interaction-pristine','interaction-asan',
        'modules-output-linux','modules-output-pristine','modules-output-asan']
    summary=dict(runs={},comparisons={})
    for name in selected:
        directory=base/name
        (modules.verify if name.startswith('modules-') else tool.verify)(directory)
        summary['runs'][name]=record(directory)
    pairs=[('linux','pristine'),('linux','asan'),('modules-linux-complete','modules-pristine-complete'),
           ('modules-linux-complete','modules-asan-complete')]
    for left,right in pairs:
        tool.compare(base/left,base/right)
        summary['comparisons'][left+'__'+right]=json.loads((base/right/('comparison-'+left+'.json')).read_text())
    data=json.loads((base/'gcov/coverage.json').read_text())
    coverage={}
    for unit in data:
        for file in unit['files']:
            if '/admixtools-t04-coverage/src/' not in file['file']:continue
            coverage[Path(file['file']).name]={f['name']:f['execution_count'] for f in file['functions']}
    summary['coverage']=coverage
    library=ctypes.CDLL('libopenblas.so.0');library.openblas_get_config.restype=ctypes.c_char_p
    summary['openblas_config']=library.openblas_get_config().decode()
    summary['machine']=subprocess.check_output(['gcc','-dumpmachine'],text=True).strip()
    # Include full fixtures/streams, sanitizer stacks, gcov and probe build commands.
    archive=Path.home()/'t04-linux-evidence.tar.gz'
    metadata=base/'probe-builds';metadata.mkdir(exist_ok=True)
    for name in ('linux-complete','pristine-complete','asan-complete','coverage'):
        for filename in ('build.json','build.log'):
            shutil.copyfile(Path.home()/'t04-probes'/name/filename,metadata/(name+'-'+filename))
    # GNU sparse tar retains the logical 4-GiB failure-probe inputs without
    # reading/materializing gigabytes of holes as ordinary byte streams.
    subprocess.run(['tar','--sparse','-czf',str(archive),'-C',str(base),*selected,
        'qpwave-shared','gcov','probe-builds','-C',str(Path.home()/'t04-results'),'static-linux'],check=True)
    target=OUT/'linux-evidence.tar.gz';shutil.copyfile(archive,target)
    summary['archive']=dict(path=str(target.relative_to(ROOT)),sha256=tool.sha(target),bytes=target.stat().st_size)
    write(OUT/'linux-summary.json',summary)
    print('collected',len(selected),'runs',summary['archive'],flush=True)


def windows():
    linux=json.loads((OUT/'linux-summary.json').read_text())
    runs={name:record(OUT/name) for name in ('windows-complete','modules-windows-complete','modules-parser-windows','interaction-windows','modules-output-windows')}
    tool.verify(OUT/'windows-complete');modules.verify(OUT/'modules-windows-complete')
    modules.verify(OUT/'modules-parser-windows')
    tool.verify(OUT/'interaction-windows');modules.verify(OUT/'modules-output-windows')
    runs={name:record(OUT/name) for name in runs}
    frozen=json.loads((OUT/'builds/snapshot.json').read_text())
    changed=[path for path,digest in frozen['sources'].items() if tool.sha(ROOT/path)!=digest]
    if changed:raise RuntimeError('production source changed: '+str(changed))
    static=json.loads((OUT/'static-windows-final/inventory.json').read_text())
    module_inventory={}
    for mid,item in static['modules'].items():
        item['coverage_note']='Linux instrumented production functions; execution does not establish contract correctness. Windows-only M01 has no gcov instrumentation.'
        coverage=linux['coverage'].get(Path(item['source']).name,{})
        for function in item['functions']:
            function['linux_execution_count']=coverage.get(function['name'],None)
        module_inventory[mid]=item
    write(REPORTS/'T04_modules.inventory.json',dict(upstream=frozen['upstream'],working_head=frozen['head'],
        status='reviewed; incomplete independent contract coverage; no module certified',modules=module_inventory))
    comparisons={}
    a=linux['runs']['linux'];b=runs['windows-complete']
    raw=json.loads((OUT/'windows-complete/comparison-linux.json').read_text())
    shared=sorted(a['cases'].keys()&b['cases'].keys())
    successful=[n for n in shared if a['cases'][n].get('returncode')==b['cases'][n].get('returncode')==0]
    scientific=[n for n in successful if a['cases'][n].get('tool')=='qpDstat' and a['cases'][n].get('scientific_rows')]
    comparisons['linux_windows']=dict(shared_cases=len(shared),joint_successes=len(successful),
        normalized_terminal_exact=sum(raw[n]=='exact' for n in shared),
        successful_scientific_cases=len(scientific),scientific_exact=[n for n in scientific
            if a['cases'][n]['scientific_rows']==b['cases'][n]['scientific_rows']],
        scientific_differences=[n for n in scientific if a['cases'][n]['scientific_rows']!=b['cases'][n]['scientific_rows']],raw=raw)
    comparisons['linux_windows']['zero_exit_without_results']=[n for n in successful
        if a['cases'][n].get('tool')=='qpDstat' and not a['cases'][n].get('scientific_rows')]
    config_directory=OUT/'builds/snapshot/bin'
    with os.add_dll_directory(str(config_directory)):
        library=ctypes.CDLL(str(config_directory/'libopenblas.dll'))
        library.openblas_get_config.restype=ctypes.c_char_p
        config=library.openblas_get_config().decode()
    evidence=dict(id='T04',date='2026-11-10',status='reviewed with open defects; not passed',
        upstream_commit=frozen['upstream'],working_head=frozen['head'],branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
        production_changes=[],production_snapshot_mismatches=changed,
        source_sha256=frozen['sources'],
        windows_build=json.loads((config_directory/'windows-build.json').read_text()),
        windows_openblas_config=config,linux_openblas_config=linux['openblas_config'],linux_machine=linux['machine'],
        builds={name:json.loads((OUT/'builds'/('build-'+name+'.json')).read_text()) for name in ('pristine','linux','asan','coverage')},
        windows_runs=runs,linux_runs=linux['runs'],comparisons=comparisons,linux_comparisons=linux['comparisons'],
        linux_archive=linux['archive'],powershell=json.loads((OUT/'native-powershell-final/powershell.json').read_text(encoding='utf-8-sig')),
        module_inventory='tests/windows/audits/T04_modules.inventory.json',
        reused_findings=['F024','F044','F045','F048','F050','F051'],new_findings=[f'F{i:03d}' for i in range(56,73)],
        limitations=['No complete independent certification of the 18 modules or their headers: unexercised functions are explicit in each report/inventory.',
            'No macOS runtime, Windows ASan/MSan, full research dataset or end-to-end >4-GiB scientific analysis.',
            'No exhaustive storage/allocator/permission failure, process termination or graph rendering matrix.',
            'Coverage records the first instrumented production run plus the module run; aborting paths need sanitizer evidence and may not flush gcov.',
            'Pristine upstream gzip PED/BED and failures intentionally differ from previously corrected port behavior.'],
        runner_sha256={p.name:tool.sha(p) for p in (ROOT/'tests/windows').iterdir() if p.name in
            ('audit_qpdstat.py','audit_t04_modules.py','build_t04_audit.py','build_t04_probes.py',
             'inventory_t04_modules.py','collect_t04_evidence.py','qpdstat_module_probe.c','t04_argv_child.c','t04_native_checks.ps1')})
    evidence['findings']=[dict(id=m[1],severity_and_scope=m[2].strip(),reproducer_and_observation=m[3].strip(),
        classification_and_proposed_repair=m[4].strip()) for m in re.finditer(
            r'^\| (F\d+) / ([^|]+)\| ([^|]+)\| ([^|]+)\|$',(REPORTS/'T04_qpDstat.md').read_text(),re.M)]
    evidence['artifact_sha256']={str(p.relative_to(OUT)):tool.sha(p) for p in OUT.iterdir() if p.is_file() and p.suffix in ('.txt','.gz','.json')}
    write(REPORTS/'T04_qpDstat.evidence.json',evidence)
    for mid,(title,contract,limits) in MODULES.items():
        item=module_inventory[mid];functions=item['functions']
        executed=[f['name'] for f in functions if (f.get('linux_execution_count') or 0)>0]
        unexecuted=[f['name'] for f in functions if not (f.get('linux_execution_count') or 0)>0]
        case_names=[n for n in runs['modules-windows-complete']['cases'] if n.startswith(mid)]
        coverage='Not instrumented on Windows; Linux does not build M01.' if mid=='M01' else f'{len(executed)}/{len(functions)} Windows-inventory function names executed in the instrumented Linux run. Platform/compiler conditionals can change this denominator.'
        headers=', '.join(f'`{v or "uncatalogued"}` {k}' for k,v in item['header_contracts'].items())
        report=f'''# {mid}: {title} — independent review

Status: **reviewed; independent contract coverage incomplete; not passed**.
Date: 10 November 2026. No production repair was made.

## Contract and source

`{item['source']}`; SHA-256 `{item['sha256']}`.
{contract}

The pinned upstream and current port baseline, actual build commands, dependency
versions/ABI, environments, raw per-case statuses and archive hash are in
[T04 evidence](T04_qpDstat.evidence.json). Caller/reference candidates and every
compiler-recognized function are in [the function inventory](T04_modules.inventory.json).
Archive membership/reference matches do not establish runtime reachability.

Header closure: {headers}.
These headers compile in their real production contexts; standalone header
self-containment, every default/table and every inactive platform branch are
not thereby certified. H items remain open.

## Recorded checks

| Contract check | Evidence and limit |
| --- | --- |
| Ordinary and numerical behavior | Direct cases {', '.join('`'+n+'`' for n in case_names) or 'See platform/sibling/integration cases'}; ordinary/mode consumers in T04. Exact output comparison retains discrepancies. |
| Results, streams, files and exits | All raw stdout/stderr/statuses retained; RNG stdout is compared as binary bytes, packed files by SHA-256. OS abort codes are retained. No scientific tolerances. |
| Boundary/malformed input | Direct boundary cases plus T04 input/block/chromosome/format matrix. This is not exhaustive for unexecuted functions. |
| RNG and calculation order | Fixed fresh-process seeds, single-thread dependencies, no fast-math/reassociation; no algorithm change. For non-random functions this row applies only to their random-dependent callers. |
| Widths, ABI and large offsets | Native 64-bit build, 64-bit port offset type, 32-bit BLAS integers; >4-GiB service probe and ordinary genotype round trips. No end-to-end >4-GiB scientific run. |
| Paths, helpers and ownership | Native PowerShell/path/gzip matrix, shared qpWave helper regressions and relevant direct probes. No filesystem/process behavior is inferred for pure numerical functions. |
| Memory and lifetime | Linux ASan/UBSan, selected leak detection, native Windows ordinary/failure probes. First-failure aborts and missing Windows MSan/ASan limit conclusions. |
| Non-Windows and affected callers | Pristine Linux and current Linux builds, targeted sibling cases; macOS not executed. Caller tool IDs retain their independent audit status. |

## Coverage, findings and closure

{coverage}
Compiler warning inventory: {item['warning_count']} warnings under the recorded
extra review flags. Warnings alone are not findings or passes.

For findings, severity, reproducer, platform behavior and proposed repairs, see
[the T04 finding register](T04_qpDstat.md#findings). Existing corrected findings
retain their original IDs and scoped historical status.

**Remaining:** {limits}

Functions without a recorded positive Linux execution count:
{', '.join('`'+n+'`' for n in unexecuted) if unexecuted else 'None in this compiler-derived inventory; this does not prove all branches/contracts.'}

No module/header is closed by the T04 tool review. Completing the remaining
contracts requires additional evidence; these limitations are not a clean pass.
'''
        (REPORTS/(mid+'_'+Path(item['source']).stem+'.md')).write_text(report,encoding='utf-8',newline='\n')
    print(json.dumps(dict(matrix_counts={k:v['case_count'] for k,v in {**runs,**linux['runs']}.items()},comparisons={k:{x:y for x,y in v.items() if x not in ('raw','scientific_exact')} for k,v in comparisons.items()}),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--linux',action='store_true')
    a=p.parse_args();linux() if a.linux else windows()
