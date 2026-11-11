"""Build T07 probes against the isolated production objects, without repairs."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
from build_t04_probes import ROOT, DEPENDENCIES
from audit_qpdstat import sha


def build(tree,output,toolchain=None,sanitizer=False):
    output.mkdir(parents=True,exist_ok=False)
    tests=tree/'tests/windows'; tests.mkdir(parents=True,exist_ok=True)
    source=tests/'qp4diff_probe.c'; shutil.copyfile(ROOT/'tests/windows/qp4diff_probe.c',source)
    flags=['-std=gnu11','-g','-O2','-ffp-contract=off','-fno-fast-math','-Isrc','-Isrc/nicksrc']
    if os.name=='nt':
        compiler=toolchain/'gcc.exe'; obj=tree/'src/.windows'
        flags+=['-include','src/win32/compat.h','-D_FILE_OFFSET_BITS=64','-D__USE_MINGW_ANSI_STDIO=1']
        inputs=[obj/(s+'.o') for s in DEPENDENCIES]+[obj/'libnick.a',obj/'win32_compat.o',obj/'admixtools-resource.o']
        libs=['-lgsl','-lopenblas','-lz','-lm']; env=dict(os.environ,PATH=str(toolchain)+os.pathsep+os.environ['PATH'])
        for dll in (tree/'bin').glob('*.dll'): shutil.copyfile(dll,output/dll.name)
    else:
        compiler=Path('/usr/bin/gcc'); inputs=[tree/'src'/(s+'.o') for s in DEPENDENCIES]+[tree/'src/nicksrc/libnick.a']
        libs=['-lgsl','-lopenblas','-lm']; env=dict(os.environ)
        if sanitizer: flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie']
    extra=inputs[-2:] if os.name=='nt' else []
    archive=tree/('src/.windows/libnick.a' if os.name=='nt' else 'src/nicksrc/libnick.a')
    jobs=[('qp4diff_probe',source,inputs)]
    for name in ('platform_probe','largefile_probe'):
        shared=tests/(name+'.c'); shutil.copyfile(ROOT/'tests/windows'/(name+'.c'),shared)
        jobs.append((name,shared,([archive] if name=='platform_probe' else [])+extra))
    commands=[]
    with (output/'build.log').open('w') as log:
        for name,selected,objects in jobs:
            command=[str(compiler),*flags,str(selected),*[str(p) for p in objects],*libs,'-o',
                     str(output/(name+('.exe' if os.name=='nt' else '')))]
            commands.append(command); log.write(json.dumps(command)+'\n'); log.flush()
            subprocess.run(command,cwd=tree,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    (output/'build.json').write_text(json.dumps(dict(commands=commands,
        source_sha256={str(p.relative_to(tree)):sha(p) for _,p,_ in jobs}),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tree',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    p.add_argument('--toolchain',type=Path); p.add_argument('--sanitizer',action='store_true')
    a=p.parse_args(); build(a.tree.resolve(),a.output.resolve(),a.toolchain.resolve() if a.toolchain else None,a.sanitizer)
