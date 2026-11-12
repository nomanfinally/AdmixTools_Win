"""Verify qpGraph ignores a child failure when usable fstats were produced."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
from audit_qpdstat import sha,no_core
from build_t04_audit import ROOT

def run(bindir,fixtures,output,toolchain=None):
    output.mkdir(parents=True,exist_ok=False)
    windows=os.name=='nt';suffix='.exe' if windows else ''
    compiler=str(toolchain/'gcc.exe') if windows else 'gcc'
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_CORETYPE='NEHALEM',LC_ALL='C',STMP='tmp')
    if windows: env['PATH']=str(toolchain)+os.pathsep+env.get('PATH','')
    source=ROOT/'tests/windows/t08_helper_child.c'
    cmd=[compiler,'-O2',str(source),'-o',str(output/('qpfstats'+suffix))]
    subprocess.run(cmd,env=env,check=True,capture_output=True)
    shutil.copyfile(bindir/('qpGraph'+suffix),output/('qpGraph'+suffix))
    if windows:
        for dll in bindir.glob('*.dll'): shutil.copyfile(dll,output/dll.name)
    work=output/'work';work.mkdir();(work/'tmp').mkdir()
    for f in ('graph','input.fstats'):shutil.copyfile(fixtures/f,work/f)
    (work/'par').write_text('graphname: graph\nseed: 77\ndiag: .0001\ninitmix: 12\ninbreed: NO\n')
    env['PATH']=str(output)+os.pathsep+env.get('PATH','')
    p=subprocess.run([str(output/('qpGraph'+suffix)),'-p','par'],cwd=work,env=env,capture_output=True,
                     timeout=30,preexec_fn=no_core if not windows else None)
    for s,data in zip(('stdout','stderr'),(p.stdout,p.stderr)):(output/('parent.'+s)).write_bytes(data)
    record=dict(command=cmd,source_sha256=sha(source),parent_sha256=sha(output/('qpGraph'+suffix)),returncode=p.returncode,
                stdout_sha256=sha(output/'parent.stdout'),stderr_sha256=sha(output/'parent.stderr'),
                final_score=[s for s in p.stdout.decode().splitlines() if 'final score:' in s],
                child_diagnostic=p.stderr.replace(b'\r\n',b'\n')==b'fixture qpfstats exit 7\n',temporaries=sorted(p.name for p in (work/'tmp').iterdir()))
    (output/'results.json').write_text(json.dumps(record,indent=2)+'\n');print(record)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bin',type=Path,required=True);p.add_argument('--fixtures',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--toolchain',type=Path)
    a=p.parse_args();run(a.bin.resolve(),a.fixtures.resolve(),a.output.resolve(),a.toolchain.resolve() if a.toolchain else None)
