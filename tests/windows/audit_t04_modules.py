"""Independent M01-M14/M17-M20 probes and targeted sibling regressions.

Use the executables produced by build_t04_probes.py. Raw differences and known
upstream bugs remain failures/observations; they are never marked fixed here.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import audit_qpdstat as t04
import parity


def run(bindir,probes,output,selection):
    if os.name=='nt':
        import ctypes
        ctypes.windll.kernel32.SetErrorMode(3)
    output.mkdir(parents=True,exist_ok=False)
    common=output/'fixtures';parity.fixtures(common);(common/'tmp').mkdir()
    (common/'pops4').write_bytes(b'Out\nA\nB\nX\n')
    (common/'types').write_bytes(b'Out 2\nA 2\nB 1\nX 0\n')
    (common/'types-bad').write_bytes(b'Out 2\nA 2\nB 1\nX 0\nC 2\n')
    parameters=b'ROOT: alpha\ninteger: 7\nreal: .125\nfile: ROOT/data\n'
    (common/'parameters').write_bytes(parameters)
    (common/'parameters-crlf').write_bytes(parameters.replace(b'\n',b'\r\n'))
    (common/'parameters-empty').write_bytes(b'integer:\nreal: .125\nfile: alpha/data\n')
    (common/'parameters-invalid').write_bytes(b'integer: 7oops\nreal: nan\nfile: alpha/data\n')
    (common/'parameters-include').write_bytes(b'+++ parameters\n')
    (common/'parameters-loop').write_bytes(b'+++ parameters-loop\n')
    (common/'parameters-long').write_bytes(b'file: '+b'x'*6000+b'\n')
    (common/'parameters-many').write_bytes(b''.join(f'x{i}: 1\n'.encode() for i in range(401)))
    (common/'duplicate.ind').write_bytes(b'i U A\ni U A\n')
    (common/'short.matrix').write_bytes(b'TGENO')
    (common/'invalid.matrix').write_bytes(b'TGENO invalid'.ljust(48,b'\0'))
    (common/'empty.matrix').write_bytes(b'')
    for label,header in {'negative':'TGENO -1 2 0 0','zero':'TGENO 0 2 0 0',
            'huge':'TGENO 18446744073709551616 2 0 0','junk':'TGENO 1junk 2 0 0',
            'size':'TGENO 2 2 0 0','hash':'TGENO 1 2 ffffffffz 0'}.items():
        (common/(label+'.matrix')).write_bytes(header.encode().ljust(48,b'\0'))
    (common/'parameters-overflow').write_bytes(b'integer: 2147483648\n')
    (common/'parameters-real-junk').write_bytes(b'integer: 7\nreal: .125oops\n')
    vector=b'ints: -2147483648,0,2147483647\nreals: -.25,0,1.25\nlarge: 9223372036854775807\n'
    (common/'vector').write_bytes(vector)
    (common/'vector-junk').write_bytes(vector.replace(b',0,214',b',0junk,214'))
    (common/'vector-real-junk').write_bytes(vector.replace(b'1.25',b'1.25junk'))
    (common/'vector-long-overflow').write_bytes(vector.replace(b'9223372036854775807',b'9223372036854775808'))
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_CORETYPE='NEHALEM',
             LC_ALL='C',STMP='tmp',ASAN_OPTIONS='detect_leaks=0:abort_on_error=1',
             UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    env['PATH']=str(bindir)+os.pathsep+str(probes)+os.pathsep+env.get('PATH','')
    manifest=dict(binary_dir=str(bindir),probe_dir=str(probes),platform=sys.platform,environment={k:env[k]
        for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','OPENBLAS_CORETYPE','LC_ALL','STMP','ASAN_OPTIONS','UBSAN_OPTIONS')},
        completed=False,cases={},executables={})
    suffix='.exe' if os.name=='nt' else ''

    def invoke(name,tool,args,expected='success',probe=True,edit=None,timeout=15):
        if not re.search(selection,name):return
        work=output/name;shutil.copytree(common,work)
        # Each case gets independent file ownership and process-global state.
        (work/'probe.bytes').write_bytes(bytes(range(256)))
        if edit:edit(work)
        inputs={p.name:t04.sha(p) for p in work.iterdir() if p.is_file()}
        exe=(probes if probe else bindir)/(tool+suffix)
        entry=dict(tool=tool,arguments=args,expected=expected,files={})
        entry['inputs']=inputs
        if exe.is_file():manifest['executables'][tool]=t04.sha(exe)
        try:
            selected_env=env
            if name=='M06-median-leak':selected_env=dict(env,ASAN_OPTIONS='detect_leaks=1:abort_on_error=1')
            p=subprocess.run([exe.name,*args],executable=str(exe),cwd=work,env=selected_env,capture_output=True,
                             timeout=timeout,preexec_fn=t04.no_core if os.name!='nt' else None)
            entry['returncode']=p.returncode;streams=p.stdout,p.stderr
        except subprocess.TimeoutExpired as error:
            entry['timeout']=True;streams=error.stdout or b'',error.stderr or b''
        except OSError as error:
            entry['unavailable']=str(error);streams=b'',str(error).encode()
        for stream,data in zip(('stdout','stderr'),streams):(output/f'{name}.{stream}').write_bytes(data)
        for filename in ('probe.bytes','probe.geno','probe.tgeno','child.log','copied','filtered'):
            if (work/filename).is_file():entry['files'][filename]=t04.sha(work/filename)
        entry['temporaries']=sorted(p.name for p in (work/'tmp').glob('*'))
        manifest['cases'][name]=entry
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(name,entry.get('returncode','TIMEOUT/UNAVAILABLE'),flush=True)

    for name in ('M01-io','M02-strings','M04-gauss','M04-reseed','M05-distributions','M05-boundary',
            'M06-sort','M07-hash','M08-vector','M09-jack','M10-solver','M12-packing',
            'M14-bits','M19-ld','M19-empty','M20-regression','M20-singular','M10-singular'):
        invoke(name,'module_probe',[name])
    invoke('M12-small-normal','module_probe',['M12-small-normal'])
    for name in ('M06-empty','M09-one','M12-overflow'):
        invoke(name,'module_probe',[name],'failure')
    invoke('M12-map-leak','module_probe',['M12-map-leak'])
    invoke('M12-header-size','module_probe',['M12-header-size'],'failure')
    invoke('M12-write-missing','module_probe',['M12-write-missing'],'failure')
    if os.name!='nt':invoke('M12-write-full','module_probe',['M12-write-full'],'failure')
    invoke('M06-median-leak','module_probe',['M06-median-leak'])
    invoke('M18-file-leak','module_probe',['M18-file-leak'])
    for kind in ('short','invalid','empty','negative','zero','huge','junk','size','hash'):
        invoke('M12-read-'+kind,'module_probe',['M12-read',kind+'.matrix'],'failure')
    invoke('M02-legacy-shell','module_probe',['M02-legacy-shell'])
    if os.name=='nt':
        for name in ('M01-sibling','M01-process-errors','M01-services'):
            invoke(name,'module_probe',[name])
    for label,filename in (('valid','parameters'),('crlf','parameters-crlf'),('empty','parameters-empty'),
            ('invalid','parameters-invalid'),('include','parameters-include'),('loop','parameters-loop'),
            ('long','parameters-long'),('many','parameters-many'),
            ('overflow','parameters-overflow'),('real-junk','parameters-real-junk')):
        invoke('M03-parser-'+label,'module_probe',['M03-parser',filename],
               'success' if label in ('valid','crlf','include') else 'failure')
    invoke('M11-individuals','module_probe',['M11-individuals','input.ind'])
    for label in ('vector','vector-junk','vector-real-junk','vector-long-overflow'):
        invoke('M03-'+label,'module_probe',['M03-vector',label], 'success' if label=='vector' else 'failure')
    invoke('M11-duplicate','module_probe',['M11-individuals','duplicate.ind'],'failure')
    invoke('M13-map','module_probe',['M13-map','probe.bytes'])
    invoke('M13-missing','module_probe',['M13-map','absent'],'failure')
    invoke('M18-list','module_probe',['M18-list','types'])
    invoke('M18-capacity','module_probe',['M18-list','types-bad'],'failure')
    invoke('T04-banker-large','module_probe',['T04-banker-large'])
    invoke('T04-tree-oracle','module_probe',['T04-tree-oracle'])
    for n in (0,1,2,5,12,32):invoke('M17-fourier-'+str(n),'module_probe',['M17-fourier',str(n)],'observe')
    invoke('M01-M06-M08-platform','platform_probe',[])
    invoke('M01-rng','platform_probe',['rng'])
    invoke('M01-largefile','largefile_probe',['largefile.bin'],timeout=30)
    invoke('M13-map-failure','map_failure_probe',['map-failure.bin'],'failure',timeout=30)
    for seed in ('77','123','0','1','2147483648'):
        invoke('M14-sample-'+seed,'module_probe',['sample','input.ind','pops4','3',seed])
    invoke('caller-transpose-missing-output','transpose',['binary.tgeno','absent/output.geno'],'failure',probe=False)
    for tool in ('qp3Pop','qp4diff','qpF4ratio','qpAdm','qpfstats','qpWave','qpdslow','qpDpart'):
        def prepare(work,tool=tool,block=False):
            if tool in ('qpdslow','qpDpart'):
                text=(work/'par.qpDstat').read_text()
                if tool=='qpDpart':text+='pattern: BABA : ABBA\n'
            else:text=(work/('par.'+tool)).read_text()
            if block:text+='blockname: blocks\n'
            (work/'par').write_text(text,newline='\n')
            (work/'blocks').write_text(''.join(f'rs{s:05d} 2221\n' for s in range(2200)),newline='\n')
        invoke('caller-'+tool,tool,['-p','par'],probe=False,edit=prepare,timeout=30)
        # Only these consumers actually parse/use blockname in their sources.
        if tool in ('qpAdm','qpWave','qp3Pop','qpF4ratio','qpDpart'):
            invoke('caller-'+tool+'-block-overflow',tool,['-p','par'],'failure',probe=False,
                   edit=lambda work,tool=tool:prepare(work,tool,True),timeout=30)
    manifest['completed']=True
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


def verify(directory):
    m=json.loads((directory/'manifest.json').read_text());failures=[]
    if not m['completed']:failures.append('incomplete')
    for name,c in m['cases'].items():
        code=c.get('returncode')
        if code is None or (c['expected']!='observe' and (code!=0)!=(c['expected']=='failure')):failures.append(name+': exit')
        err=(directory/f'{name}.stderr').read_bytes()
        if b'AddressSanitizer' in err or b'runtime error:' in err:failures.append(name+': sanitizer')
        if code is not None and ((code < 0 and code != -6) or
                (code >= 0x80000000 and code not in (3221226505,4294967295))):
            failures.append(name+': unexpected signal or system exception')
        if c['temporaries']:failures.append(name+': retained temporaries')
        if name in ('M03-parser-valid','M03-parser-crlf','M03-parser-include'):
            out=(directory/f'{name}.stdout').read_bytes()
            if b'[alpha/data]' not in out:failures.append(name+': macro path was changed')
        if name=='M12-map-leak' and b'leaked handles: 0' not in (directory/f'{name}.stdout').read_bytes():failures.append(name+': leaked descriptors')
        if name=='M18-file-leak' and b'leaked handles: 0' not in (directory/f'{name}.stdout').read_bytes():failures.append(name+': leaked descriptors')
        if name=='M02-legacy-shell' and b'produced file: 1' not in (directory/f'{name}.stdout').read_bytes():failures.append(name+': legacy shell path')
        if name=='M01-sibling':
            args=['plain','space value','quote"inside','C:\\space\\','\u03b1','','end\\\\"tail']
            expected=''.join(f'arg {i}:{s.encode().hex()}\n' for i,s in enumerate(args,1)).encode()
            if (directory/name/'child.log').read_bytes()!=expected:failures.append(name+': argument bytes changed')
    (directory/'verification.json').write_text(json.dumps(dict(failures=failures),indent=2)+'\n')
    print(json.dumps(failures,indent=2));return bool(failures)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bin',type=Path);p.add_argument('--probes',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--select',default='.');p.add_argument('--verify',type=Path);p.add_argument('--compare',type=Path,nargs=2)
    a=p.parse_args()
    if a.verify:sys.exit(verify(a.verify.resolve()))
    if a.compare:sys.exit(t04.compare(*[x.resolve() for x in a.compare]))
    if not a.bin or not a.probes or not a.output:p.error('use --bin DIR --probes DIR --output NEW_DIR')
    run(a.bin.resolve(),a.probes.resolve(),a.output.resolve(),a.select)
