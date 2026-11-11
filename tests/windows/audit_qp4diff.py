"""T07 port-only matrix. Preserve upstream failures, raw streams and exact rows.

No inherited scientific/interface defect is repaired or used as a new Windows
expectation. Comparisons retain exit/NaN/diagnostic differences for review.
"""
import argparse
import difflib
import gzip
import itertools
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import parity
from audit_qpdstat import sha, normal, no_core

OCTET = 'Out A B X Out C A X'


def oracle(work, octets, overlap=True, fancy=False, multiplier=1.):
    """Independent allele-frequency/covariance and weighted jackknife oracle.

    Oracle fixtures use .5-Morgan blocks and at most .1 Morgan per chromosome,
    so chromosome labels give known unequal blocks without production helpers.
    """
    people = [s.split()[2] for s in (work/'input.ind').read_text().splitlines()]
    chromosomes = [int(s.split()[1]) for s in (work/'input.snp').read_text().splitlines()]
    calls = (work/'input.geno').read_text().splitlines()

    def f4(groups, quad):
        if 'NULL' in quad:
            raise ValueError('NULL rejects in qp4diff')
        shared = set(quad[:2]) & set(quad[2:])
        if any(not groups[p] for p in quad):
            equal = any(groups[a] and groups[b] and sum(groups[a])/len(groups[a]) ==
                        sum(groups[b])/len(groups[b]) for a,b in (quad[:2],quad[2:]))
            return 0. if fancy and not shared and equal else None
        freq = {p:sum(groups[p])/(2*len(groups[p])) for p in quad}
        a,b,c,d = quad
        value = (freq[a]-freq[b])*(freq[c]-freq[d])
        for i,j in ((0,2),(0,3),(1,2),(1,3)):
            if quad[i] == quad[j]:
                p=quad[i]
                value -= (1 if (i+j)%2 == 0 else -1)*freq[p]*(1-freq[p])/(2*len(groups[p])-1)
        return value

    answers = []
    for octet in octets:
        blocks = {}
        union = 0
        for chrom, row in zip(chromosomes, calls):
            if not 1 <= chrom <= 22:
                continue
            groups = {p:[] for p in octet}
            for p, v in zip(people, row):
                if p in groups and v != '9': groups[p].append(int(v))
            a,b = f4(groups,octet[:4]), f4(groups,octet[4:])
            if overlap and (a is None or b is None): continue
            if a is None and b is None: continue
            union += 1
            entry = blocks.setdefault(chrom,[0.,0.,0.,0.])
            if a is not None: entry[0] += multiplier*a; entry[1] += 1
            if b is not None: entry[2] += b; entry[3] += 1
        entries = list(blocks.values())
        totals = [sum(v[i] for v in entries) for i in range(4)]
        mean = totals[0]/totals[1]-totals[2]/totals[3]
        if overlap:
            leave = [((totals[0]-totals[2])-(v[0]-v[2]))/(totals[1]-v[1]+1e-10) for v in entries]
            weights = [v[1] for v in entries]
        else:
            leave = [(totals[0]-v[0])/(totals[1]-v[1]+1e-10)-
                     (totals[2]-v[2])/(totals[3]-v[3]+1e-10) for v in entries]
            weights = [v[1]+v[3] for v in entries]
        count = sum(weights)
        estimate = sum(mean-j for j in leave)+sum(w*j for w,j in zip(weights,leave))/count
        variance = sum(((count/w)*mean-(count/w-1)*j-estimate)**2/(count/w-1)
                       for w,j in zip(weights,leave))/len(entries)
        sd = math.sqrt(max(0.,variance))
        answers.append(['result:',*octet[:4],':',*octet[4:],f'{estimate:.6f}',f'{sd:.6f}',
                        f'{estimate/sd:.3f}' if sd else 'undefined',str(union)])
    return answers


def run(bindir, output, ubsan_recover=False):
    output.mkdir(parents=True,exist_ok=False)
    if os.name == 'nt':
        import ctypes
        ctypes.windll.kernel32.SetErrorMode(3)
    common = output/'fixtures'
    parity.fixtures(common); (common/'tmp').mkdir()
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', OPENBLAS_CORETYPE='NEHALEM',
               LC_ALL='C', STMP='tmp', ASAN_OPTIONS='detect_leaks=0:abort_on_error=1',
               UBSAN_OPTIONS='halt_on_error='+('0' if ubsan_recover else '1')+':print_stacktrace=1')
    env['PATH'] = str(bindir)+os.pathsep+env.get('PATH','')
    m = dict(upstream=(Path(__file__).resolve().parents[2]/'UPSTREAM_BASELINE').read_text().strip(),
             platform=sys.platform, binary_dir=str(bindir), completed=False, cases={}, oracles={},
             environment={k:env[k] for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','OPENBLAS_CORETYPE',
                          'LC_ALL','STMP','ASAN_OPTIONS','UBSAN_OPTIONS')}, executables={})

    def invoke(name, tool, args, work):
        exe=bindir/(tool+('.exe' if os.name=='nt' else '')); m['executables'][tool]=sha(exe)
        entry=dict(tool=tool,arguments=args,inputs={str(p.relative_to(work)):sha(p)
                   for p in work.rglob('*') if p.is_file()},files={})
        before=set(Path('/var/tmp').glob('genotmp:*')) if os.name!='nt' else set()
        try:
            p=subprocess.run([exe.name,*args],executable=str(exe),cwd=work,env=env,capture_output=True,
                             timeout=90 if name.startswith('prepare-') else 20,
                             preexec_fn=no_core if os.name!='nt' else None)
            entry['returncode']=p.returncode; streams=p.stdout,p.stderr
        except subprocess.TimeoutExpired as e:
            entry['timeout']=True; streams=e.stdout or b'',e.stderr or b''
        for s,data in zip(('stdout','stderr'),streams): (output/(name+'.'+s)).write_bytes(data)
        entry['rows']=[s.split() for s in streams[0].decode('utf-8','surrogateescape').splitlines()
                       if s.startswith(('result:','badoctet:'))]
        entry['sanitizer']=bool(re.search(rb'AddressSanitizer|runtime error:|LeakSanitizer',streams[1]))
        entry['temporaries']=sorted(p.name for p in (work/'tmp').iterdir())
        entry['external_temporaries']=[]
        if os.name!='nt':
            for token in set(re.findall(rb'/var/tmp/genotmp:\d+(?:\.[A-Za-z0-9]{6})?',streams[0])):
                p=Path(os.fsdecode(token))
                if p not in before and p.is_file():
                    entry['external_temporaries'].append(dict(path=str(p),sha256=sha(p))); p.unlink()
        for f in ('result.out','output.geno','input.tgeno','roundtrip.geno','input.ancestry','plink.ped','plink.bed'):
            if (work/f).is_file(): entry['files'][f]=dict(bytes=(work/f).stat().st_size,sha256=sha(work/f))
        m['cases'][name]=entry
        (output/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')

    for fmt,out in [('PACKEDANCESTRYMAP','output.geno'),('ANCESTRYMAP','input.ancestry'),('PED','plink.ped'),('PACKEDPED','plink.bed')]:
        (common/'par.convert').write_text('genotypename: input.geno\nsnpname: input.snp\nindivname: input.ind\noutputformat: '+fmt+
            '\ngenotypeoutname: '+out+'\nsnpoutname: '+fmt+'.pedsnp\nindivoutname: '+fmt+'.pedind\noutputgroup: YES\n',newline='\n')
        invoke('prepare-'+fmt,'convertf',['-p','par.convert'],common)
    invoke('prepare-transpose','transpose',['output.geno','input.tgeno'],common)
    invoke('prepare-roundtrip','transpose',['input.tgeno','roundtrip.geno'],common)
    m['packed_roundtrip_exact']=(common/'output.geno').read_bytes()==(common/'roundtrip.geno').read_bytes()
    for f in ('input.geno','output.geno','input.tgeno','input.ancestry','plink.ped','plink.bed'):
        (common/(f+'.gz')).write_bytes(gzip.compress((common/f).read_bytes(),mtime=0))
    base='genotypename: input.geno\nsnpname: input.snp\nindivname: input.ind\npopfilename: diffs\nblgsize: .005\n'
    modes={'default':'','explicit-defaults':'overlap: YES\nfancyf4: NO\nnumchrom: 22\nfirstf4mult: 1\n',
           'allsnps':'allsnps: YES\n','nonoverlap':'overlap: NO\n','allsnps-overrides-yes':'overlap: YES\nallsnps: YES\n',
           'allsnps-overrides-no':'overlap: NO\nallsnps: NO\n','multiplier':'firstf4mult: 2.5\n',
           'multiplier-negative':'firstf4mult: -1\n','multiplier-zero':'firstf4mult: 0\n',
           'fancy':'fancyf4: YES\n','instem':'instem: input\n','limit-3':'popsizelimit: 3\n',
           'limit-1':'popsizelimit: 1\n','limit-77':'popsizelimit: 3\nseed: 77\n','limit-123':'popsizelimit: 3\nseed: 123\n',
           'physical-subset':'','numchrom':'numchrom: 10\n','numchrom-zero':'numchrom: 0\n',
           'numchrom-intmax':'numchrom: 2147483647\n','gfromp':'gfromp: YES\n','physical-fallback':'',
           'zero-blocksize':'blgsize: 0\n','negative-blocksize':'blgsize: -1\n','nan-blocksize':'blgsize: nan\n',
           'inf-blocksize':'blgsize: inf\n','one-block':'blgsize: 100\n','one-snp':'','two-snps':'',
           'badsnp':'badsnpname: badsnps\n','output':'output: result.out\n','outputname':'outputname: result.out\n',
           'output-missing-parent':'output: absent/result.out\n','nostatslim':'nostatslim: 999999\n',
           'unparsed-controls':'seed: 123\nchrom: 99\nxdata: YES\nnoxdata: NO\ninbreed: YES\njackweight: NO\nblockname: absent\n',
           'bad-number':'popsizelimit: 3oops\n','verbose':'','missing-data':'','all-missing':'','constant':'',
           'zero-difference':'','repeated-f2':'','repeated-f3':'','unknown-pop':'','null-left':'','null-right':'',
           'empty-list':'','short-list':'','extra-column':'','colon-list':'','comments':'','long-list':'','long-comment':'',
           'many-rows':'','duplicate-ind':'','duplicate-snp':'','empty-ind':'','empty-snp':'','missing-geno':'',
           'truncated-text':'','bad-genotype':'','missing-popfile':'','omitted-popfile':'','omitted-geno':'',
           'packed-short':'','tgeno-short':'','bom':'','crlf-macro':'','utf16':'','space-paths':'','forward-paths':'',
           'x-default':'','x-ignored-controls':'chrom: 23\nxdata: YES\nnoxdata: NO\n','x-enabled':'numchrom: 23\n',
           'x-enabled-male':'numchrom: 23\n','x-enabled-female':'numchrom: 23\n','x-enabled-unknown':'numchrom: 23\n'}
    for fmt in ('text','packed','tgeno','ancestry','ped','bed'):
        modes['format-'+fmt]=''; modes['gzip-'+fmt]=''
    for kind in ('corrupt','truncated','crc','reader-fatal','concatenated'): modes['gzip-'+kind]=''
    for kind in ('ordinary','missing','nonoverlap','nonoverlap-missing','fancy','strict','f2','f3','multiplier','permutations','unequal'):
        modes['oracle-'+kind]='blgsize: .5\n'+('overlap: NO\n' if kind.startswith('nonoverlap') else '')+(
            'fancyf4: YES\n' if kind=='fancy' else '')+('firstf4mult: 2.5\n' if kind=='multiplier' else '')
    if os.name=='nt': modes['unicode-paths']=''
    for name,extra in modes.items():
        work=output/name; work.mkdir(); (work/'tmp').mkdir()
        for p in common.iterdir():
            if p.is_file(): shutil.copyfile(p,work/p.name)
        text=base
        for key in re.findall(r'(?m)^([^:\s]+):',extra): text=re.sub(r'(?m)^'+re.escape(key)+r':.*\n','',text)
        text+=extra; args=['-p','par']
        def write(f,s): (work/f).write_text(s,encoding='utf-8',newline='\n')
        genotypes=(work/'input.geno').read_text().splitlines(); people=(work/'input.ind').read_text().splitlines()
        changes={'unknown-pop':OCTET.replace('Out','Absent'),'null-left':OCTET.replace('Out','NULL',1),
                 'null-right':'Out A B X NULL C A X','repeated-f2':'Out A Out A Out C A X',
                 'repeated-f3':'Out A X A Out C A X','oracle-f2':'Out A Out A Out C A X',
                 'oracle-f3':'Out A X A Out C A X','zero-difference':'Out A B X Out A B X',
                 'empty-list':'','short-list':'Out A B X','extra-column':OCTET+' extra ignored',
                 'colon-list':'Out A : B X :: Out C : A X','comments':'# comment\n\n'+OCTET+' # trailing comment',
                 'long-list':(OCTET+' ')*70,'long-comment':'#'+(' comment'*200)+'\n'+OCTET,
                 'many-rows':(OCTET+'\n')*31}
        write('diffs',changes.get(name,OCTET)+'\n')
        if name=='oracle-permutations': write('diffs',''.join(' '.join(q)+' Out C A X\n' for q in itertools.permutations('Out A B X'.split())))
        if name in ('all-missing','constant'): write('input.geno',(('9' if name=='all-missing' else '0')*54+'\n')*2200)
        if name in ('one-snp','two-snps','one-block'):
            n=1 if name=='one-snp' else 2 if name=='two-snps' else 100
            write('input.geno','\n'.join(genotypes[:n])+'\n'); write('input.snp',''.join((work/'input.snp').read_text().splitlines(True)[:n]))
        if name in ('missing-data','oracle-missing','oracle-nonoverlap-missing'):
            write('input.geno',''.join(''.join('9' if (i//6==3 and s%3==0) or (i//6==2 and s%5==0) else v
                  for i,v in enumerate(row))+'\n' for s,row in enumerate(genotypes)))
        if name in ('oracle-fancy','oracle-strict'):
            write('input.geno',''.join(('9'*6+'0'*6+'0'*6+row[18:])+'\n' if s%4==0 else row+'\n' for s,row in enumerate(genotypes)))
        if name=='oracle-unequal':
            indices=[i for i in range(2200) if i%100 < 15+(i//100)*3]
            write('input.geno',''.join(genotypes[i]+'\n' for i in indices))
            snps=(work/'input.snp').read_text().splitlines(); write('input.snp',''.join(snps[i]+'\n' for i in indices))
        if name=='physical-subset':
            indices=[i for i in range(54) if i%6<3]; write('input.ind',''.join(people[i]+'\n' for i in indices))
            write('input.geno',''.join(''.join(row[i] for i in indices)+'\n' for row in genotypes))
        if name.startswith('x-'):
            write('input.snp',re.sub(r'(?m)^(\S+) \d+ ',r'\1 23 ',(work/'input.snp').read_text()))
            write('input.ind',''.join(s.replace(' U ',' M ' if name.endswith('male') and not name.endswith('female') else
                ' F ' if name.endswith('female') else ' U ' if name.endswith('unknown') else ' M ' if i%2 else ' F ')+'\n' for i,s in enumerate(people)))
        if name in ('duplicate-ind','duplicate-snp','empty-ind','empty-snp'):
            f='input.ind' if name.endswith('ind') else 'input.snp'; lines=(work/f).read_text().splitlines()
            lines[1]=' '.join([lines[0].split()[0],*lines[1].split()[1:]])
            write(f,'' if name.startswith('empty') else '\n'.join(lines)+'\n')
        if name=='physical-fallback': write('input.snp',''.join(' '.join(s.split()[:2]+['0']+s.split()[3:])+'\n' for s in (work/'input.snp').read_text().splitlines()))
        if name=='badsnp': write('badsnps','rs00000\nrs00200\n')
        if name.startswith('oracle-'):
            m['oracles'][name]=oracle(work,[s.split() for s in (work/'diffs').read_text().splitlines()],
                overlap='nonoverlap' not in name,fancy=name=='oracle-fancy',multiplier=2.5 if name=='oracle-multiplier' else 1.)
        if name.startswith(('format-','gzip-')):
            kind=name.split('-',1)[1]; f={'text':'input.geno','packed':'output.geno','tgeno':'input.tgeno','ancestry':'input.ancestry','ped':'plink.ped','bed':'plink.bed'}.get(kind,'input.geno')
            if name.startswith('gzip-'): f+='.gz'
            text=text.replace('genotypename: input.geno','genotypename: '+f)
            if kind in ('ped','bed'):
                fmt='PED' if kind=='ped' else 'PACKEDPED'; text=text.replace('input.snp',fmt+'.pedsnp').replace('input.ind',fmt+'.pedind')
            if kind=='corrupt': (work/f).write_bytes(b'invalid gzip')
            if kind=='truncated': (work/f).write_bytes((work/f).read_bytes()[:-9])
            if kind=='crc':
                data=bytearray((work/f).read_bytes()); data[-8]^=1; (work/f).write_bytes(data)
            if kind=='reader-fatal': (work/f).write_bytes(gzip.compress(b'invalid genotypes\n',mtime=0))
            if kind=='concatenated':
                data=(work/'input.geno').read_bytes(); (work/f).write_bytes(gzip.compress(data[:12001],mtime=0)+gzip.compress(data[12001:],mtime=0))
        if name=='missing-geno': (work/'input.geno').unlink()
        if name=='truncated-text': write('input.geno','\n'.join(genotypes[:20])+'\n')
        if name=='bad-genotype': write('input.geno','x'+(work/'input.geno').read_text()[1:])
        if name=='missing-popfile': (work/'diffs').unlink()
        if name in ('omitted-popfile','omitted-geno'):
            text=re.sub(r'(?m)^'+('popfilename' if name=='omitted-popfile' else 'genotypename')+r':.*\n','',text)
        if name=='instem': text=re.sub(r'(?m)^(?:genotypename|snpname|indivname):.*\n','',text)
        if name in ('packed-short','tgeno-short'):
            f='output.geno' if name=='packed-short' else 'input.tgeno'; (work/f).write_bytes((work/f).read_bytes()[:50]); text=text.replace('genotypename: input.geno','genotypename: '+f)
        if name in ('output','outputname'): write('result.out','preserve existing output\n')
        if name=='verbose': args+=['-V']
        if name in ('space-paths','unicode-paths','forward-paths'):
            directory=work/('space # \u03b1' if name=='unicode-paths' else 'space # files'); directory.mkdir()
            for f in ('input.geno','input.snp','input.ind','diffs'):
                shutil.copyfile(work/f,directory/f); path=str(directory/f)
                if name=='forward-paths': path=path.replace('\\','/')
                if os.name=='nt': path='"'+path+'"'
                text=re.sub(r'(?m)(: )'+re.escape(f)+r'$',lambda m:m[1]+path,text)
        if name=='bom': (work/'par').write_bytes(b'\xef\xbb\xbf'+text.encode())
        elif name=='utf16': (work/'par').write_bytes(text.encode('utf-16'))
        elif name=='crlf-macro': (work/'par').write_bytes(('DIR: .\n'+text.replace('genotypename: input.geno','genotypename: DIR/input.geno')).replace('\n','\r\n').encode())
        else: write('par',text)
        invoke(name,'qp4diff',args,work)
    for name,args in [('help',['-h']),('version',['-v']),('no-args',[]),('invalid-option',['-z']),
                      ('missing-value',['-p']),('missing-par',['-p','absent']),('version-then-run',['-v','-p','par.qp4diff'])]:
        invoke('cli-'+name,'qp4diff',args,common)
    for tool in ('qpDstat','qp3Pop','qpF4ratio'):
        invoke('related-'+tool,tool,['-p','par.'+tool],common)
    m['completed']=True; (output/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    print(output,len(m['cases']),'cases; oracle differences:',
          [n for n,rows in m['oracles'].items() if rows!=m['cases'][n]['rows']],flush=True)


def compare(left,right):
    a,b=[json.loads((p/'manifest.json').read_text()) for p in (left,right)]
    assert a['completed'] and b['completed']
    result={}; diff=[]
    for name in sorted(a['cases'].keys()|b['cases'].keys()):
        if name not in a['cases'] or name not in b['cases']: result[name]=['absent']; continue
        x,y=a['cases'][name],b['cases'][name]; errors=[]
        if x.get('timeout') or y.get('timeout'): errors.append('timeout')
        if x.get('returncode')!=y.get('returncode'): errors.append('exit')
        for stream in ('stdout','stderr'):
            u,v=[normal((p/(name+'.'+stream)).read_bytes()) for p in (left,right)]
            if u!=v:
                errors.append(stream); diff.extend(difflib.unified_diff(u.splitlines(True),v.splitlines(True),
                    fromfile='left/'+name+'.'+stream,tofile='right/'+name+'.'+stream))
        if x['rows']!=y['rows']: errors.append('scientific rows')
        if x['files']!=y['files']: errors.append('files')
        result[name]=errors
    target=right/('comparison-'+left.name)
    target.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    target.with_suffix('.diff').write_text(''.join(diff),encoding='utf-8',errors='surrogateescape')
    print('exact',sum(not v for v in result.values()),'of',len(result),'scientific differences',
          [n for n,v in result.items() if 'scientific rows' in v],flush=True)
    return any(result.values())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bin',type=Path); p.add_argument('--output',type=Path)
    p.add_argument('--compare',type=Path,nargs=2)
    p.add_argument('--ubsan-recover',action='store_true',help='retain inherited UB diagnostics and continue to later checks')
    a=p.parse_args()
    if a.compare: sys.exit(compare(*(v.resolve() for v in a.compare)))
    elif a.bin and a.output: run(a.bin.resolve(),a.output.resolve(),a.ubsan_recover)
    else: p.error('use --bin DIR --output NEW_DIR or --compare LEFT RIGHT')
