"""T08 strict qpGraph mode/CLI/file comparison against unmodified Linux.

New output directories only. Failures, timeouts and scientific differences are
retained; this runner does not treat reproducing an upstream defect as a pass.
"""
import argparse
import difflib
import gzip
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import parity
from audit_qpdstat import sha, no_core, normal as shared_normal


def normal(data):
    text = shared_normal(data)
    text = re.sub(r'\b(qpGraph|qpreroot)\.exe\b', r'\1', text)
    text = re.sub(r'(## end of qpGraph time:)[ ]*\d+\.\d+( seconds memory:)[ ]*\d+\.\d+',
                  r'\1 <CPU>\2 <MEMORY>', text)
    # Generated names alone, including optional collision suffix; preserve labels.
    text = re.sub(r'(?:/tmp|tmp|[^\r\n" ]+[/\\]tmp)[/\\](fsx|ppp|pops|fstpar|fslog)\.\d+(?:\.[A-Za-z0-9]{6})?',
                  r'<TMP>/\1.<PID>', text)
    return text


def run(bindir, output, recover=False, only=None):
    output.mkdir(parents=True, exist_ok=False)
    if os.name == 'nt':
        import ctypes
        ctypes.windll.kernel32.SetErrorMode(3)
    common = output/'fixtures'
    parity.fixtures(common)
    (common/'tmp').mkdir()
    (common/'graphpops').write_text('Out\nA\nB\nC\nX\n')
    base = 'genotypename: input.geno\nsnpname: input.snp\nindivname: input.ind\nseed: 77\nblgsize: .005\ninbreed: NO\nhires: YES\n'
    (common/'par.fstats').write_text(base+'poplistname: graphpops\nfstatsoutname: input.fstats\n')
    env = dict(os.environ, PATH=str(bindir)+os.pathsep+os.environ.get('PATH',''),
               OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', OPENBLAS_CORETYPE='NEHALEM', LC_ALL='C', STMP='tmp',
               ASAN_OPTIONS='detect_leaks=0:abort_on_error=1',
               UBSAN_OPTIONS='halt_on_error='+('0' if recover else '1')+':print_stacktrace=1')
    manifest = dict(completed=False, platform=sys.platform, binary_dir=str(bindir), cases={},
                    environment={k:env[k] for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','OPENBLAS_CORETYPE',
                       'LC_ALL','STMP','ASAN_OPTIONS','UBSAN_OPTIONS')}, executables={})

    def invoke(name, tool, args, work):
        exe=bindir/(tool+('.exe' if os.name=='nt' else ''))
        manifest['executables'][tool]=sha(exe)
        entry=dict(tool=tool, arguments=args, inputs={str(p.relative_to(work)).replace('\\','/'):sha(p)
                   for p in work.rglob('*') if p.is_file()})
        try:
            p=subprocess.run([exe.name,*args], executable=str(exe), cwd=work, env=env, capture_output=True,
                             timeout=35, preexec_fn=no_core if os.name!='nt' else None)
            entry['returncode']=p.returncode
            streams=p.stdout,p.stderr
        except subprocess.TimeoutExpired as e:
            entry['timeout']=True
            streams=e.stdout or b'',e.stderr or b''
        for s,data in zip(('stdout','stderr'),streams):
            (output/(name+'.'+s)).write_bytes(data)
        entry['sanitizer']=bool(re.search(rb'AddressSanitizer|runtime error:|LeakSanitizer', streams[1]))
        # Complete numerical streams are compared separately; these identify fitting results.
        entry['scores']=[line for line in streams[0].decode('utf-8','surrogateescape').splitlines()
                         if re.search(r'final score:|worst f-stat:|gslans:|final vg:|number of graph evaluations:',line)]
        entry['files']={f:dict(bytes=(work/f).stat().st_size,sha256=sha(work/f)) for f in
                       ('graph.out','graph.dot','f3.log','fit.dump','mix.out','outliers','generated.fstats','helper.log','unused.out','halfjack')
                       if (work/f).is_file()}
        entry['temporaries']=sorted(p.name for p in (work/'tmp').iterdir())
        manifest['cases'][name]=entry
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

    invoke('prepare-fstats','qpfstats',['-p','par.fstats'],common)
    for fmt,out in [('PACKEDANCESTRYMAP','output.geno')]:
        (common/'par.convert').write_text(base+'outputformat: '+fmt+'\ngenotypeoutname: '+out+
            '\nsnpoutname: output.snp\nindivoutname: output.ind\n')
        invoke('prepare-packed','convertf',['-p','par.convert'],common)
    invoke('prepare-transpose','transpose',['output.geno','input.tgeno'],common)
    invoke('prepare-roundtrip','transpose',['input.tgeno','roundtrip.geno'],common)
    manifest['packed_roundtrip_exact']=(common/'output.geno').read_bytes()==(common/'roundtrip.geno').read_bytes()
    for f in ('input.geno','output.geno','input.tgeno'):
        (common/(f+'.gz')).write_bytes(gzip.compress((common/f).read_bytes(),mtime=0))
    # Each mode starts with the same upstream defaults except fixed seed and short initialization.
    modes={
        'default':'', 'no-diag':'diag: 0\n', 'auto':'', 'auto-output':'fstatsoutname: generated.fstats\nfstatslog: helper.log\n',
        'no-opt':'optit: NO\n','init-zero':'initmix: 0\n','init-one':'initmix: 1\n',
        'seed-123':'seed: 123\n','seed-negative':'seed: -1\n',
        'lsq':'lsqmode: YES\n','diag':'diag: .0001\n','f2diag':'f2diag: .1\n',
        'minvar':'minvar: .000001\n','precision':'precision: .001\n',
        'lambda':'lambdascale: 2\n','sizeweight':'sizeweight: YES\n',
        'allsnps':'allsnps: YES\n','inbreed':'inbreed: YES\n','oldallsnps':'oldallsnps: YES\n',
        'halfscore':'halfscore: YES\n','fullvar':'fullvar: YES\n','halfjack':'halfscore: YES\nhalfjackname: halfjack\n',
        'quartet':'quartet: YES\n','no-analysis':'doanalysis: NO\n','no-analysis-poplist':'doanalysis: NO\npoplistname: graphpops\n',
        'fulloutlier':'fulloutlier: YES\nzthresh: 1\n','terse':'terse: YES\n','details':'details: YES\n',
        'gsl-details':'gsldetails: YES\n','init-verbose':'initverbose: YES\n',
        'tree':'','multiple-ancestors':'','locked-edge':'','locked-admix':'','zero-edge':'','legacy':'','legacy-zero':'','legacy-lock':'',
        'interior-admix':'','two-admix':'',
        'three-way-admix':'','duplicate-edge':'','duplicate-admix':'','graph-cycle':'','missing-root':'',
        'empty-graph':'','missing-graph':'','short-edge':'','bad-keyword':'','long-graph-line':'',
        'bad-lock':'','unknown-root':'root: Absent\n','reroot':'root: O\n',
        'bad-pair':'badpop2name: badpairs\n','base-bad-pair':'badpop2name: badpairs\n',
        'load':'loadname: saved.dump\n','admixin':'admixin: saved.mix\n','bad-load':'loadname: absent\n',
        'missing-fstats':'fstatsname: absent\n','empty-fstats':'','short-fstats':'','nan-fstats':'',
        'missing-base':'','unknown-pop':'','base-order':'','output':'output: unused.out\n',
        'auto-limit':'popsizelimit: 3\n','auto-allsnps':'allsnps: YES\n','auto-inbreed':'inbreed: YES\n',
        'auto-text-gzip':'','auto-packed':'','auto-transposed':'','auto-packed-gzip':'','auto-transposed-gzip':'',
        'auto-gzip-crc':'','auto-gzip-truncated':'','auto-missing-geno':'','auto-bad-output':'fstatsoutname: absent/generated.fstats\n',
        'auto-bad-log':'fstatslog: absent/helper.log\n','auto-helper-failure':'',
        'ignored-data-controls':'chrom: 99\npopsizelimit: 1\nblgsize: -1\ngfromp: YES\n',
        'cli-precedence':'seed: 123\n','space-paths':'','forward-paths':'', 'crlf':'','bom':'',
    }
    if os.name=='nt': modes['unicode-paths']=''
    for name,extra in modes.items():
        if only and name not in only: continue
        work=output/name; work.mkdir(); (work/'tmp').mkdir()
        for p in common.iterdir():
            if p.is_file(): shutil.copyfile(p,work/p.name)
        text=base+'graphname: graph\nfstatsname: input.fstats\ndiag: .0001\ninitmix: 12\ngraphoutname: graph.out\ngraphdotname: graph.dot\nf3log: f3.log\ndumpname: fit.dump\nadmixout: mix.out\noutliername: outliers\n'
        if name.startswith('auto'): text=text.replace('fstatsname: input.fstats\n','')
        for key in re.findall(r'(?m)^([^:\s]+):',extra): text=re.sub(r'(?m)^'+re.escape(key)+r':.*\n','',text)
        text+=extra
        graph=(work/'graph').read_text()
        def write(f,s): (work/f).write_text(s,encoding='utf-8',newline='\n')
        if name=='tree': graph=graph.replace('admix XX AB C 60 40\nedge x XX X','edge x C X')
        if name=='interior-admix': graph=graph.replace('admix XX AB C 60 40','admix XX A B 60 40')
        if name=='two-admix': graph=graph.replace('admix XX AB C 60 40','admix YY B C 50 50\nadmix XX AB YY 60 40')
        if name=='multiple-ancestors': graph=graph.replace('edge c Q C','edge c S C')
        if name=='locked-edge': graph+='edgelock a .001\n'
        if name=='locked-admix': graph+='lock XX\n'
        if name=='zero-edge': graph=graph.replace('edge a AB A','edge a AB A zero')
        if name.startswith('legacy'):
            graph=''.join('vertex '+v+'\n' for v in 'R O Q AB A B C XX X'.split())
            graph+=''.join('label '+v+' '+p+'\n' for v,p in [('O','Out'),('A','A'),('B','B'),('C','C'),('X','X')])
            graph+='ledge o R O\nredge q R Q\nledge ab Q AB\nledge a AB A\nredge b AB B\nredge c Q C\n'
            graph+='admix XX AB C 60 40\nledge x XX X\n'
            if name=='legacy-zero': graph=graph.replace('ledge a AB A','ledge a AB A zero')
            if name=='legacy-lock': graph=graph.replace('ledge a AB A','ledge a AB A .001 lock').replace('admix XX AB C 60 40','admix XX AB C 60 40 lock')
        if name=='three-way-admix': graph=graph.replace('admix XX AB C 60 40','admix XX AB C O 40 40 20')
        if name=='duplicate-edge': graph+='edge a AB A\n'
        if name=='duplicate-admix': graph+='admix XX AB C 60 40\n'
        if name=='graph-cycle': graph=graph.replace('edge ab Q AB','edge ab AB Q')
        if name=='missing-root': graph=graph.replace('root R\n','')
        if name=='empty-graph': graph=''
        if name=='short-edge': graph+='edge alone\n'
        if name=='bad-keyword': graph+='unknown line\n'
        if name=='bad-lock': graph+='edgelock absent .1\n'
        if name=='long-graph-line': graph+='#'+'x'*600+'\n'
        if name=='unknown-pop': graph=graph.replace('label X X','label Missing X')
        if name=='base-order': graph=graph.replace('label Out O\nlabel A A','label A A\nlabel Out O')
        write('graph',graph)
        if name=='missing-graph': (work/'graph').unlink()
        if name=='empty-fstats': write('input.fstats','')
        if name=='short-fstats': write('input.fstats',(work/'input.fstats').read_text().splitlines()[0]+'\n')
        if name=='missing-base': write('input.fstats',(work/'input.fstats').read_text().replace('Out','Absent'))
        if name=='nan-fstats':
            original=(work/'input.fstats').read_text()
            changed,count=re.subn(r'(?m)^(\s*A\s+A\s+)\S+',r'\1nan',original,count=1)
            assert count==1 and changed!=original
            write('input.fstats',changed)
        if name in ('bad-pair','base-bad-pair'): write('badpairs','A B\n' if name=='bad-pair' else 'Out A\n')
        if name in ('load','admixin'):
            source=output/'default'/('fit.dump' if name=='load' else 'mix.out')
            if source.exists(): shutil.copyfile(source,work/('saved.dump' if name=='load' else 'saved.mix'))
        if name=='output': write('unused.out','sentinel must be accounted for\n')
        selected={'auto-text-gzip':'input.geno.gz','auto-packed':'output.geno','auto-transposed':'input.tgeno',
                  'auto-packed-gzip':'output.geno.gz','auto-transposed-gzip':'input.tgeno.gz',
                  'auto-gzip-crc':'input.geno.gz','auto-gzip-truncated':'input.geno.gz'}
        if name in selected: text=text.replace('genotypename: input.geno\n','genotypename: '+selected[name]+'\n')
        if name in ('auto-gzip-crc','auto-gzip-truncated'):
            data=bytearray((work/'input.geno.gz').read_bytes())
            if name.endswith('crc'): data[-8]^=1
            else: data=data[:-5]
            (work/'input.geno.gz').write_bytes(data)
        if name=='auto-missing-geno': (work/'input.geno').unlink()
        if name=='auto-helper-failure': write('input.ind',(work/'input.ind').read_text().replace(' U X',' U Missing'))
        args=['-p','par']
        if name=='cli-precedence': args+=['-s','999','-l','99','-z','99']
        if name in ('space-paths','forward-paths','unicode-paths'):
            folder=work/('data with spaces' if name!='unicode-paths' else 'data Å Ω'); folder.mkdir()
            for f in ('input.fstats','graph'): shutil.copyfile(work/f,folder/f)
            # Relative quoted Windows paths; Linux upstream parser does not unquote.
            for key,f in (('fstatsname','input.fstats'),('graphname','graph')):
                path=str(Path(folder.name)/f)
                if name=='forward-paths': path=path.replace('\\','/')
                text=text.replace(key+': '+f+'\n',key+': "'+path+'"\n')
        if name=='crlf': (work/'par').write_bytes(text.replace('\n','\r\n').encode())
        elif name=='bom': (work/'par').write_bytes(b'\xef\xbb\xbf'+text.encode())
        else: write('par',text)
        invoke(name,'qpGraph',args,work)
    for name,args in {'no-args':[], 'version':['-v'], 'help':['-h'], 'invalid':['-?'],
                      'missing-value':['-p'], 'missing-parameter-file':['-p','absent'],
                      'graph-only':['-g','graph'], 'version-analysis':['-v','-p','par.qpGraph','-g','graph'],
                      'verbose':['-V','-p','par.qpGraph','-g','graph']}.items():
        invoke('cli-'+name,'qpGraph',args,common)
    # Connected executable smoke paths are explicit; this does not close T09.
    for name,args in {'reroot-default':['-g','graph','-o','graph.out'],
                      'reroot-root':['-g','graph','-r','O','-o','graph.out','-d','graph.dot'],
                      'reroot-help':['-h']}.items(): invoke(name,'qpreroot',args,common)
    manifest['completed']=True
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(output,len(manifest['cases']),'cases',flush=True)


def compare(left,right):
    a,b=[json.loads((p/'manifest.json').read_text()) for p in (left,right)]
    assert a['completed'] and b['completed']
    results={}; diffs=[]
    for name in sorted(a['cases'].keys()|b['cases'].keys()):
        if name not in a['cases'] or name not in b['cases']: results[name]=['absent']; continue
        x,y=a['cases'][name],b['cases'][name]; errors=[]
        if x.get('timeout') or y.get('timeout'): errors.append('timeout')
        if x.get('returncode')!=y.get('returncode'): errors.append('exit')
        for stream in ('stdout','stderr'):
            u,v=[normal((p/(name+'.'+stream)).read_bytes()) for p in (left,right)]
            if u!=v:
                errors.append(stream)
                diffs.extend(difflib.unified_diff(u.splitlines(True),v.splitlines(True),fromfile='left/'+name+'.'+stream,tofile='right/'+name+'.'+stream))
        if x['scores']!=y['scores']: errors.append('scores')
        # Text artifacts permit CRLF alone; original bytes/hashes are retained.
        for f in x['files'].keys()|y['files'].keys():
            if f not in x['files'] or f not in y['files']: errors.append('file:'+f); continue
            xp,yp=left/name/f,right/name/f
            if not xp.exists(): xp=left/'fixtures'/f
            if not yp.exists(): yp=right/'fixtures'/f
            if xp.read_bytes().replace(b'\r\n',b'\n')!=yp.read_bytes().replace(b'\r\n',b'\n'): errors.append('file:'+f)
        results[name]=errors
    target=right/('comparison-'+left.name)
    target.with_suffix('.json').write_text(json.dumps(results,indent=2)+'\n')
    target.with_suffix('.diff').write_text(''.join(diffs),encoding='utf-8',errors='surrogateescape')
    print('exact',sum(not e for e in results.values()),'/',len(results),'score differences:',[n for n,e in results.items() if 'scores' in e])
    return any(results.values())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bin',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--compare',type=Path,nargs=2);p.add_argument('--ubsan-recover',action='store_true')
    p.add_argument('--only',nargs='+',help='run named analysis modes plus preparation and CLI smoke cases')
    a=p.parse_args()
    if a.compare: sys.exit(compare(*(v.resolve() for v in a.compare)))
    elif a.bin and a.output: run(a.bin.resolve(),a.output.resolve(),a.ubsan_recover,a.only)
    else: p.error('supply --bin/--output or --compare LEFT RIGHT')
