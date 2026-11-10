"""Build qp3Pop production-function probe in an isolated source tree."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import hashlib
from build_t04_probes import DEPENDENCIES, ROOT

def build(tree,output,toolchain=None,sanitizer=False,coverage=False,float_cast=False):
    output.mkdir(parents=True,exist_ok=False)
    tests=tree/'tests/windows';tests.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/'tests/windows/qp3pop_probe.c',tests/'qp3pop_probe.c')
    win=os.name=='nt';suffix='.exe' if win else ''
    flags=['-std=gnu11','-g','-O2','-ffp-contract=off','-fno-fast-math','-Isrc','-Isrc/nicksrc']
    if win:
        compiler=toolchain/'gcc.exe';obj=tree/'src/.windows'
        flags+=['-include','src/win32/compat.h','-D_FILE_OFFSET_BITS=64','-D__USE_MINGW_ANSI_STDIO=1']
        inputs=[obj/(s+'.o') for s in DEPENDENCIES]+[obj/'libnick.a',obj/'win32_compat.o',obj/'admixtools-resource.o']
        libs=['-lgsl','-lopenblas','-lz','-lm'];env=dict(os.environ,PATH=str(toolchain)+os.pathsep+os.environ['PATH'])
        for dll in (tree/'bin').glob('*.dll'):shutil.copyfile(dll,output/dll.name)
    else:
        compiler=Path('/usr/bin/gcc');inputs=[tree/'src'/(s+'.o') for s in DEPENDENCIES]+[tree/'src/nicksrc/libnick.a']
        libs=['-lgsl','-lopenblas','-lm'];env=os.environ.copy()
        if sanitizer:flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie']
    if coverage:flags+=['--coverage','-fprofile-abs-path']
    commands=[]
    if float_cast:
        flags+=['-fsanitize=float-cast-overflow']
        compile_cmd=[str(compiler),*flags,'-c','src/qpsubs.c','-o',str(output/'qpsubs-float.o')]
        commands.append(compile_cmd)
        inputs=[output/'qpsubs-float.o' if p.name=='qpsubs.o' else p for p in inputs]
    cmd=[str(compiler),*flags,str(tests/'qp3pop_probe.c'),*[str(p) for p in inputs],*libs,'-o',str(output/('qp3pop_probe'+suffix))]
    with (output/'build.log').open('w') as log:
        for command in commands:
            log.write(json.dumps(command)+'\n');log.flush()
            subprocess.run(command,cwd=tree,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        log.write(json.dumps(cmd)+'\n');log.flush()
        subprocess.run(cmd,cwd=tree,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    (output/'build.json').write_text(json.dumps(commands+[cmd],indent=2)+'\n')
    sources=[tests/'qp3pop_probe.c',tree/'src/qp3Pop.c',*[tree/'src'/(s+'.c') for s in DEPENDENCIES]]
    (output/'source-sha256.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tree',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--toolchain',type=Path);p.add_argument('--sanitizer',action='store_true');p.add_argument('--coverage',action='store_true')
    p.add_argument('--float-cast',action='store_true')
    a=p.parse_args();build(a.tree.resolve(),a.output.resolve(),a.toolchain.resolve() if a.toolchain else None,a.sanitizer,a.coverage,a.float_cast)
