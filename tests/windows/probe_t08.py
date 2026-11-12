"""Build/run actual T08 graph, fitting, GSL, RNG and sparse-offset probes."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from audit_qpdstat import sha, no_core
from build_t04_audit import ROOT
from build_t04_probes import DEPENDENCIES
import parity


def run(tree,output,toolchain=None,sanitizer=False):
    output.mkdir(parents=True,exist_ok=False)
    tests=tree/'tests/windows'; tests.mkdir(parents=True,exist_ok=True)
    windows=os.name=='nt'; suffix='.exe' if windows else ''
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_CORETYPE='NEHALEM',LC_ALL='C',STMP='tmp',
             ASAN_OPTIONS='detect_leaks=1:abort_on_error=0',UBSAN_OPTIONS='halt_on_error=0:print_stacktrace=1')
    flags=['-std=gnu11','-O2','-g','-ffp-contract=off','-fno-fast-math','-Isrc','-Isrc/nicksrc','-I'+str(ROOT/'src/nicksrc')]
    compiler=toolchain/'gcc.exe' if windows else Path('/usr/bin/gcc')
    obj=tree/('src/.windows' if windows else 'src')
    archive=obj/'libnick.a' if windows else obj/'nicksrc/libnick.a'
    extra=[obj/'win32_compat.o',obj/'admixtools-resource.o'] if windows else []
    if windows:
        flags+=['-include','src/win32/compat.h','-D_FILE_OFFSET_BITS=64','-D__USE_MINGW_ANSI_STDIO=1']
        env['PATH']=str(toolchain)+os.pathsep+env.get('PATH','')
        for dll in (tree/'bin').glob('*.dll'): shutil.copyfile(dll,output/dll.name)
    if sanitizer: flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie']
    libs=['-lgsl','-lopenblas','-lm']+(['-lz'] if windows else [])
    inputs=[obj/(s+'.o') for s in ('gslqp','qpgsubs',*DEPENDENCIES)]+[archive,*extra]
    jobs=[('qpgraph_probe',inputs),('gslqp_probe',[obj/'gslqp.o',archive,*extra]),
          ('platform_probe',[archive,*extra]),('largefile_probe',extra)]
    manifest=dict(commands=[],cases={},sources={})
    with (output/'build.log').open('w') as log:
        for name,objects in jobs:
            source=tests/(name+'.c'); shutil.copyfile(ROOT/'tests/windows'/(name+'.c'),source)
            manifest['sources'][name]=sha(source)
            cmd=[str(compiler),*flags,str(source),*[str(p) for p in objects],*libs,'-o',str(output/(name+suffix))]
            manifest['commands'].append(cmd); log.write(json.dumps(cmd)+'\n');log.flush()
            subprocess.run(cmd,cwd=tree,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    work=output/'work'; parity.fixtures(work); (work/'tmp').mkdir()
    cases=[(n,'qpgraph_probe',[n]) for n in ('solve','graph','simplify','delete','lifetime')]
    cases += [('gsl','gslqp_probe',[]),('platform','platform_probe',[]),('rng','platform_probe',['binary']),
              ('largefile','largefile_probe',['sparse.bin'])]
    for name,exe,args in cases:
        before={p.name for p in work.iterdir()}
        p=subprocess.run([str(output/(exe+suffix)),*args],cwd=work,env=env,capture_output=True,timeout=30,
                         preexec_fn=no_core if not windows else None)
        for s,data in zip(('stdout','stderr'),(p.stdout,p.stderr)): (output/(name+'.'+s)).write_bytes(data)
        manifest['cases'][name]=dict(returncode=p.returncode,stdout_sha256=sha(output/(name+'.stdout')),
            stderr_sha256=sha(output/(name+'.stderr')),new_files=sorted({p.name for p in work.iterdir()}-before))
    (output/'results.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(output,{n:c['returncode'] for n,c in manifest['cases'].items()},flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tree',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--toolchain',type=Path);p.add_argument('--sanitizer',action='store_true')
    a=p.parse_args();run(a.tree.resolve(),a.output.resolve(),a.toolchain.resolve() if a.toolchain else None,a.sanitizer)
