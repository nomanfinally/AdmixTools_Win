"""Build T04 production-function probes in the isolated build trees."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
DEPENDENCIES='qpsubs mcio mapfile ldsubs admutils egsubs regsubs geno'.split()


def build(tree, output, toolchain=None, sanitizer=False,coverage=False):
    output.mkdir(parents=True,exist_ok=False)
    tests=tree/'tests/windows'; tests.mkdir(parents=True,exist_ok=True)
    for filename in ('qpdstat_module_probe.c','platform_probe.c','largefile_probe.c','qpwave_map_probe.c','t04_argv_child.c'):
        shutil.copyfile(ROOT/'tests/windows'/filename,tests/filename)
    windows=os.name=='nt'
    compiler=toolchain/'gcc.exe' if windows else Path('/usr/bin/gcc')
    flags=['-std=gnu11','-ffp-contract=off','-fno-fast-math','-g','-O2','-Isrc','-Isrc/nicksrc',
           '-I'+str(ROOT/'src/nicksrc')]
    if windows:
        flags+=['-include','src/win32/compat.h','-D_FILE_OFFSET_BITS=64','-D__USE_MINGW_ANSI_STDIO=1']
        objects=[tree/'src/.windows'/ (s+'.o') for s in DEPENDENCIES]
        archive=tree/'src/.windows/libnick.a'
        extra=[tree/'src/.windows/win32_compat.o',tree/'src/.windows/admixtools-resource.o']; libs=['-lgsl','-lopenblas','-lz','-lm']
        suffix='.exe'; env=dict(os.environ,PATH=str(toolchain)+os.pathsep+os.environ['PATH'])
        for dll in (tree/'bin').glob('*.dll'): shutil.copyfile(dll,output/dll.name)
    else:
        objects=[tree/'src'/(s+'.o') for s in DEPENDENCIES]
        archive=tree/'src/nicksrc/libnick.a'; extra=[]; libs=['-lgsl','-lopenblas','-lm']
        suffix=''; env=os.environ.copy()
        if not (tree/'src/nicksrc/admix_types.h').exists(): flags+=['-DT04_PRISTINE']
        if sanitizer: flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie']
    if coverage:flags+=['--coverage','-fprofile-abs-path']
    commands=[]
    jobs=[('module_probe','qpdstat_module_probe.c',objects+[archive]+extra,[]),
          ('argv_child','t04_argv_child.c',extra,[]),
          ('platform_probe','platform_probe.c',[archive]+extra,[]),
          ('largefile_probe','largefile_probe.c',extra,[])]
    if windows:
        waveobjects=[tree/'src/.windows'/(s+'.o') for s in DEPENDENCIES if s!='mapfile']
        waveobjects += [tree/'src/.windows'/(s+'.o') for s in ('f4rank','eigsubs','eigx')]
        jobs.append(('map_failure_probe','qpwave_map_probe.c',waveobjects+[archive]+extra,['-DQPWAVE_FORCE_MAP_FAILURE']))
    else:
        jobs.append(('map_failure_probe','qpwave_map_probe.c',[archive],['-ffunction-sections','-fdata-sections','-Wl,--gc-sections']))
    with (output/'build.log').open('w') as log:
        for name,source,inputs,options in jobs:
            command=[str(compiler),*flags,*options,str(tests/source),*[str(x) for x in inputs],*libs,'-o',str(output/(name+suffix))]
            commands.append(command); log.write(json.dumps(command)+'\n'); log.flush()
            p=subprocess.run(command,cwd=tree,env=env,stdout=log,stderr=subprocess.STDOUT)
            if p.returncode: raise RuntimeError('probe build failed: '+name+'; '+str(log.name))
    (output/'build.json').write_text(json.dumps(commands,indent=2)+'\n')
    print(output,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tree',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--toolchain',type=Path);p.add_argument('--sanitizer',action='store_true')
    p.add_argument('--coverage',action='store_true')
    a=p.parse_args();build(a.tree.resolve(),a.output.resolve(),a.toolchain.resolve() if a.toolchain else None,a.sanitizer,a.coverage)
