"""Record actual direct T07 statuses, streams and leak/UB diagnostics."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from audit_qpdstat import no_core, sha


def run(binary,output):
    output.mkdir(parents=True,exist_ok=False)
    if os.name=='nt':
        import ctypes
        ctypes.windll.kernel32.SetErrorMode(3)
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',LC_ALL='C',
             ASAN_OPTIONS='detect_leaks=1:abort_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    m=dict(executable_sha256=sha(binary),cases={})
    names=('f4','lifetime','lifetime-nonoverlap','one-block','one-block-nonoverlap',
           'upper-block','upper-block-nonoverlap','negative-block','negative-block-nonoverlap',
           'NULL-left','NULL-right','zero-rows')
    for name in names:
        p=subprocess.run([str(binary),name],cwd=output,env=env,capture_output=True,timeout=20,
                         preexec_fn=no_core if os.name!='nt' else None)
        for s,data in zip(('stdout','stderr'),(p.stdout,p.stderr)): (output/(name+'.'+s)).write_bytes(data)
        m['cases'][name]=dict(returncode=p.returncode,stdout=p.stdout.decode('utf-8','surrogateescape'),
             sanitizer=b'Sanitizer' in p.stderr or b'runtime error:' in p.stderr,
             streams={s:sha(output/(name+'.'+s)) for s in ('stdout','stderr')})
    suffix='.exe' if os.name=='nt' else ''
    for name,tool,args in [('platform','platform_probe',[]),('rng','platform_probe',['rng']),
                           ('largefile','largefile_probe',['sparse.bin'])]:
        executable=binary.parent/(tool+suffix)
        p=subprocess.run([str(executable),*args],cwd=output,env=env,capture_output=True,timeout=30,
                         preexec_fn=no_core if os.name!='nt' else None)
        for s,data in zip(('stdout','stderr'),(p.stdout,p.stderr)): (output/(name+'.'+s)).write_bytes(data)
        m['cases'][name]=dict(returncode=p.returncode,executable_sha256=sha(executable),
            sanitizer=b'Sanitizer' in p.stderr or b'runtime error:' in p.stderr,
            streams={s:sha(output/(name+'.'+s)) for s in ('stdout','stderr')})
    (output/'results.json').write_text(json.dumps(m,indent=2)+'\n')
    print(output,[(n,c['returncode']) for n,c in m['cases'].items()],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); run(a.binary.resolve(),a.output.resolve())
