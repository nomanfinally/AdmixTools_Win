"""T06 hard audit: raw streams/statuses, input hashes and independent ratio oracles.

An audit records defects as observations; --verify deliberately fails on them.
Scientific rows are compared exactly, including nonfinite values and every row.
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

RATIO = 'Out A X B Out A C B'
SECOND = 'Out A B X Out A C X'


def rows(directory, name):
    return [s.split() for s in (directory/(name+'.stdout')).read_text(errors='surrogateescape').splitlines()
            if s.lstrip().startswith(('result:', 'q4rat A:', 'q4rat B:', 'diff:'))]


def oracle(work, ratios, fancy=True, difference=False, sex_aware=False):
    """Count alleles independently, apply overlap covariance, then weighted jackknife.

    The overlap correction is p(1-p)/(n-1) for each shared population,
    with the signs of its two contrast coefficients. Explicit block IDs remove
    the production block builder from this independent calculation.
    """
    records = [s.split() for s in (work/'input.ind').read_text().splitlines()]
    snps = [s.split() for s in (work/'input.snp').read_text().splitlines()]
    labels = dict(s.split() for s in (work/'blocks').read_text().splitlines())
    calls = (work/'input.geno').read_text().splitlines()

    def f4(groups, quad):
        if 'NULL' in quad: return 1.
        overlap = set(quad[:2]) & set(quad[2:])
        if any(not groups[p] for p in quad):
            zero_pair = any(groups[a] and groups[b] and
                sum(x for x,n in groups[a])/sum(n for x,n in groups[a]) ==
                sum(x for x,n in groups[b])/sum(n for x,n in groups[b])
                for a,b in (quad[:2],quad[2:]))
            return 0. if fancy and not overlap and zero_pair else None
        freq = {p:sum(x for x,n in groups[p])/sum(n for x,n in groups[p]) for p in quad}
        a,b,c,d = quad
        value = (freq[a]-freq[b])*(freq[c]-freq[d])
        for i,j in ((0,2),(0,3),(1,2),(1,3)):
            if quad[i]!=quad[j]: continue
            p=quad[i]; n=sum(n for x,n in groups[p])
            if n<2:return None
            value -= (1 if (i+j)%2==0 else -1)*freq[p]*(1-freq[p])/(n-1)
        return value

    def estimate(selected):
        blocks={}
        for si,row in enumerate(calls):
            chrom=int(snps[si][1])
            if sex_aware and chrom!=23: continue
            label=int(labels[snps[si][0]])
            if label<0: continue
            groups={p:[] for p in set(sum(selected,[])) if p!='NULL'}
            for rec,v in zip(records,row):
                if rec[2] not in groups or v=='9': continue
                if sex_aware and rec[1]!='F':
                    if v=='1': continue
                    groups[rec[2]].append((int(v)//2,1))
                else: groups[rec[2]].append((int(v),2))
            values=[f4(groups,q[i:i+4]) for q in selected for i in (0,4)]
            if any(v is None for v in values): continue
            entry=blocks.setdefault(label,[0.]*len(values)+[0.])
            for i,v in enumerate(values): entry[i]+=v
            entry[-1]+=1
        values=[blocks[k] for k in sorted(blocks)]
        totals=[sum(v[i] for v in values) for i in range(len(values[0]))]
        def ratio(v,epsilon=0.):
            answer=sum(v[i]/(v[i+1]+epsilon) for i in range(0,len(v)-1,2))
            return answer-(1 if len(selected)==2 else 0)
        mean=ratio(totals)
        leave=[ratio([a-b for a,b in zip(totals,v)],1e-10) for v in values]
        count=totals[-1]
        estimate=sum(mean-j for j in leave)+sum(v[-1]*j for v,j in zip(values,leave))/count
        variance=sum(((count/v[-1])*mean-(count/v[-1]-1)*j-estimate)**2/(count/v[-1]-1)
                     for v,j in zip(values,leave))/len(values)
        sd=math.sqrt(max(0,variance))
        return [f'{estimate:.6f}',f'{sd:.6f}',f'{estimate/sd:.3f}' if sd else 'undefined',str(int(count))]
    if difference:
        n=len(ratios)//2; result=[]
        for a,b in zip(ratios[:n],ratios[n:]):
            result += [['q4rat','A:',*a[:4],':',*a[4:],*estimate([a])[:3]],
                       ['q4rat','B:',*b[:4],':',*b[4:],*estimate([b])[:3]],
                       ['diff:',*estimate([a,b])[:3]]]
        return result
    return [['result:',*q[:4],':',*q[4:],*estimate([q])] for q in ratios]


def run(bindir, output, repairs=False, probe=None):
    output.mkdir(parents=True,exist_ok=False)
    if os.name=='nt':
        import ctypes
        ctypes.windll.kernel32.SetErrorMode(3)
    common=output/'fixtures';parity.fixtures(common);(common/'tmp').mkdir()
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_CORETYPE='NEHALEM',
             LC_ALL='C',STMP='tmp',ASAN_OPTIONS='detect_leaks=0:abort_on_error=1',
             UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    env['PATH']=str(bindir)+os.pathsep+env.get('PATH','')
    m=dict(platform=sys.platform,bin=str(bindir),environment={k:env[k] for k in
        ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','OPENBLAS_CORETYPE','LC_ALL','STMP','ASAN_OPTIONS','UBSAN_OPTIONS')},
        cases={},oracles={},executables={},completed=False,repairs=repairs)

    def invoke(name,tool,args,work,expect='success'):
        exe=bindir/(tool+('.exe' if os.name=='nt' else ''));m['executables'][tool]=sha(exe)
        c=dict(tool=tool,args=args,expect=expect,inputs={p.name:sha(p) for p in work.iterdir() if p.is_file()})
        before=set(Path('/var/tmp').glob('genotmp:*')) if os.name!='nt' else set()
        try:
            p=subprocess.run([exe.name,*args],executable=str(exe),cwd=work,env=env,capture_output=True,
                             timeout=15,preexec_fn=no_core if os.name!='nt' else None)
            c['returncode']=p.returncode;streams=p.stdout,p.stderr
        except subprocess.TimeoutExpired as e:
            c['timeout']=True;streams=e.stdout or b'',e.stderr or b''
        for s,data in zip(('stdout','stderr'),streams):(output/f'{name}.{s}').write_bytes(data)
        c['temporaries']=sorted(p.name for p in (work/'tmp').iterdir());c['external_temporaries']=[]
        if os.name!='nt':
            for token in set(re.findall(rb'/var/tmp/genotmp:\d+(?:\.[A-Za-z0-9]{6})?',streams[0])):
                path=Path(os.fsdecode(token))
                if path not in before and path.is_file():
                    c['external_temporaries'].append(dict(path=str(path),sha256=sha(path)));path.unlink()
        c['files']={f:dict(sha256=sha(work/f),bytes=(work/f).stat().st_size)
                    for f in ('result.out','output.geno','input.tgeno','roundtrip.geno') if (work/f).is_file()}
        c['rows']=rows(output,name)
        c['sanitizer']=bool(re.search(rb'AddressSanitizer|runtime error:|LeakSanitizer',streams[1]))
        m['cases'][name]=c

    for fmt,out in [('PACKEDANCESTRYMAP','output.geno'),('ANCESTRYMAP','input.ancestry'),('PED','plink.ped'),('PACKEDPED','plink.bed')]:
        (common/'par.convert').write_text('genotypename: input.geno\nsnpname: input.snp\nindivname: input.ind\noutputformat: '+fmt+'\ngenotypeoutname: '+out+'\nsnpoutname: '+fmt+'.pedsnp\nindivoutname: '+fmt+'.pedind\noutputgroup: YES\n',newline='\n')
        invoke('prepare-'+fmt,'convertf',['-p','par.convert'],common)
    invoke('prepare-transpose','transpose',['output.geno','input.tgeno'],common)
    invoke('prepare-roundtrip','transpose',['input.tgeno','roundtrip.geno'],common)
    m['packed_roundtrip_exact']=(common/'output.geno').read_bytes()==(common/'roundtrip.geno').read_bytes()
    for f in ('input.geno','output.geno','input.tgeno','input.ancestry','plink.ped','plink.bed'):
        (common/(f+'.gz')).write_bytes(gzip.compress((common/f).read_bytes(),mtime=0))
    base='genotypename: input.geno\nsnpname: input.snp\nindivname: input.ind\npopfilename: ratios\nblgsize: .005\n'
    modes={'default':'','explicit-defaults':'fancyf4: YES\ndiffmode: NO\nnoxdata: YES\nnumchrom: 22\n',
           'diff':'diffmode: YES\n','diff-multi':'diffmode: YES\n','diff-odd':'diffmode: YES\n','diff-single':'diffmode: YES\n',
           'diff-invalid':'diffmode: 2\n','fancy-no':'fancyf4: NO\n','chrom':'chrom: 2\n','no-valid-snps':'chrom: 99\n',
           'numchrom':'numchrom: 10\n','numchrom-intmax':'numchrom: 2147483647\n','numchrom-zero':'numchrom: 0\n',
           'xdata':'xdata: YES\n','noxdata-no':'noxdata: NO\n','x-explicit':'chrom: 23\n',
           'limit-3':'popsizelimit: 3\n','limit-1':'popsizelimit: 1\n','limit-77':'popsizelimit: 3\nseed: 77\n',
           'limit-123':'popsizelimit: 3\nseed: 123\n','unlimited':'popsizelimit: 100\n','physical-subset':'',
           'gfromp':'gfromp: YES\n','physical-fallback':'','badsnp':'badsnpname: badsnps\n',
           'zero-blocksize':'blgsize: 0\n','negative-blocksize':'blgsize: -1\n','nan-blocksize':'blgsize: nan\n',
           'inf-blocksize':'blgsize: inf\n','one-block':'chrom: 1\nblgsize: 1\n',
           'output':'output: result.out\n','outputname':'outputname: result.out\n','output-missing-parent':'output: absent/result.out\n',
           'nostatslim':'nostatslim: 999999\n','verbose':'','missing-data':'','all-missing':'','constant':'','one-snp':'','two-snps':'',
           'unknown-pop':'','null-top':'','null-bottom':'','null-partial-bottom':'','repeated-f2':'','repeated-f3':'','zero-bottom':'',
           'same-contrast':'','empty-ratios':'','short-ratios':'','extra-column':'','colon-ratios':'','comments':'','long-ratios':'',
           'long-comment':'','duplicate-ind':'','duplicate-snp':'','empty-ind':'','empty-snp':'','missing-geno':'','truncated-text':'',
           'bad-genotype':'','bom':'','crlf-macro':'','utf16':'','space-unicode':'','forward-paths':'','bad-number':'popsizelimit: 3oops\n',
           'missing-popfile':'','omitted-popfile':'','omitted-geno':'','packed-short':'','tgeno-short':''}
    for fmt in ('text','packed','tgeno','ancestry','ped','bed'):
        modes['format-'+fmt]='';modes['gzip-'+fmt]=''
    for kind in ('corrupt','truncated','crc','reader-fatal','concatenated'):modes['gzip-'+kind]=''
    for kind in ('overflow','intmax','negative','sparse','partial','missing','duplicate'):
        modes['block-'+kind]='blockname: blocks\n'
    for kind in ('ordinary','missing','fancy','strict','permutations','denominator-permutations','reciprocal','f2','f3','null','diff','diff-missing',
                 'x-mixed','x-male','x-female','x-unknown','x-mixed-f2','x-male-f2','x-female-f2'):
        modes['oracle-'+kind]='blockname: blocks\n'+('diffmode: YES\n' if kind.startswith('diff') else '')+('fancyf4: NO\n' if kind=='strict' else '')+('chrom: 23\n' if kind.startswith('x-') else '')
    if repairs:
        modes.update({'same-contrast-diff':'diffmode: YES\n','zero-bottom-diff':'diffmode: YES\n',
                      'diff-empty':'diffmode: YES\n','output-source-collision':'output: input.geno\n',
                      'numchrom-high':'numchrom: 2147483646\n','numchrom-max-safe':'numchrom: 2147483645\n',
                      'long-boundary':'','long-boundary-crlf':'','long-boundary-eof':'','many-ratios':'','malformed-late':'',
                      'limit-zero':'popsizelimit: 3\nseed: 0\n','limit-repeat':'popsizelimit: 3\nseed: 77\n',
                      'limit-seed-one':'popsizelimit: 3\nseed: 1\n','limit-high':'popsizelimit: 3\nseed: -2147483648\n',
                      'x-one-chromosome':'chrom: 23\n','oracle-x-male-partial-overlap':'chrom: 23\nblockname: blocks\n'})
        for seed in ('0','1','77','123','2147483648'):modes['physical-seed-'+seed]=''
        modes['physical-one']=''
        for fmt in ('packed','tgeno','ancestry','ped','bed'):
            modes['duplicate-'+fmt]=''
            for kind in ('mixed','male','female','unknown','male-f2','mixed-f2'):
                modes['oracle-x-'+kind+'-format-'+fmt]='chrom: 23\nblockname: blocks\n'
    reject=set('diff-odd diff-single diff-invalid numchrom-intmax numchrom-zero zero-blocksize negative-blocksize nan-blocksize inf-blocksize one-block one-snp two-snps output-missing-parent unknown-pop null-top zero-bottom empty-ratios short-ratios long-ratios long-comment duplicate-ind duplicate-snp empty-ind empty-snp missing-geno truncated-text bad-genotype utf16 bad-number no-valid-snps missing-popfile omitted-popfile omitted-geno packed-short tgeno-short all-missing constant'.split())
    reject.update('gzip-'+k for k in ('corrupt','truncated','crc','reader-fatal'))
    reject.update('block-'+k for k in ('overflow','intmax','partial','missing','negative'))
    if repairs:
        reject.update(('same-contrast','same-contrast-diff','zero-bottom-diff','diff-empty','output','outputname','nostatslim',
                       'output-source-collision','numchrom-high','malformed-late','x-one-chromosome'))
        reject.update('duplicate-'+fmt for fmt in ('packed','tgeno','ancestry','ped','bed'))
    for name,extra in modes.items():
        work=output/name;work.mkdir();(work/'tmp').mkdir()
        for p in common.iterdir():
            if p.is_file():shutil.copyfile(p,work/p.name)
        text=base
        for key in re.findall(r'(?m)^([^:\s]+):',extra):text=re.sub(r'(?m)^'+re.escape(key)+r':.*\n','',text)
        text+=extra;args=['-p','par']
        def write(f,s):(work/f).write_text(s,encoding='utf-8',newline='\n')
        genotypes=(work/'input.geno').read_text().splitlines();people=(work/'input.ind').read_text().splitlines()
        ratios=RATIO+'\n'
        if name.startswith('diff') or name in ('oracle-diff','oracle-diff-missing'):ratios+=SECOND+'\n'
        if name=='diff-odd':ratios+=RATIO+'\n'
        if name=='diff-single':ratios=RATIO+'\n'
        if name=='diff-multi':ratios=RATIO+'\n'+SECOND+'\n'+SECOND+'\n'+RATIO+'\n'
        if name=='diff-empty':ratios=''
        if name=='same-contrast-diff':ratios='Out Out X B Out A C B\n'+SECOND+'\n'
        if name=='zero-bottom-diff':ratios=RATIO+'\nOut A X B Out Out C B\n'
        changes={'unknown-pop':RATIO.replace('Out','Absent'), 'null-top':RATIO.replace('Out','NULL',1),
                 'null-bottom':'Out A X B NULL NULL NULL NULL','oracle-null':'Out A X B NULL NULL NULL NULL',
                 'null-partial-bottom':'Out A X B Out NULL C B','repeated-f2':'Out A Out A Out A C B',
                 'oracle-f2':'Out A Out A Out A C B','repeated-f3':'Out A X A Out A C B',
                 'oracle-f3':'Out A X A Out A C B','zero-bottom':'Out A X B Out Out C B',
                 'same-contrast':'Out Out X B Out A C B','empty-ratios':'','short-ratios':'Out A X B',
                 'extra-column':RATIO+' extra ignored','colon-ratios':'Out A : X B :: Out A : C B',
                 'comments':'# comment\n\n'+RATIO+' # trailing comment',
                 'long-ratios':(RATIO+' ')*70,'long-comment':'#'+(' comment'*200)+'\n'+RATIO}
        ratios=changes.get(name,ratios);write('ratios',ratios+'\n')
        if name=='oracle-permutations':
            write('ratios',''.join(' '.join(q)+' Out A C B\n' for q in itertools.permutations('Out A X B'.split())))
        if name=='oracle-denominator-permutations':
            write('ratios',''.join('Out A X B '+' '.join(q)+'\n' for q in itertools.permutations('Out A C B'.split())))
        if name=='oracle-reciprocal':write('ratios','Out A C B Out A X B\n')
        if name.startswith('oracle-x-') and name.endswith('-f2'):write('ratios','Out A Out A Out A C B\n')
        if name.startswith('oracle-x-') and '-f2-' in name:write('ratios','Out A Out A Out A C B\n')
        if name=='oracle-x-male-partial-overlap':write('ratios','Out A Out B Out A C B\n')
        if name=='x-one-chromosome':write('ratios','Out A Out A Out A C B\n')
        if name in ('long-boundary','long-boundary-crlf','long-boundary-eof'):
            payload=RATIO+' '*(512-len(RATIO)-(1 if name=='long-boundary-crlf' else 0))
            (work/'ratios').write_bytes(payload.encode()+(b'\r\n' if name=='long-boundary-crlf' else b'' if name=='long-boundary-eof' else b'\n'))
        if name=='many-ratios':write('ratios',(RATIO+'\n')*17)
        if name=='malformed-late':write('ratios',RATIO+'\nOut A\n')
        if name=='oracle-diff-missing':write('ratios',RATIO+'\nOut A B X Out A R1 X\n')
        if name in ('duplicate-ind','duplicate-snp','empty-ind','empty-snp'):
            f='input.ind' if name.endswith('ind') else 'input.snp';lines=(work/f).read_text().splitlines()
            if name.startswith('duplicate'):lines[1]=' '.join([lines[0].split()[0],*lines[1].split()[1:]])
            write(f,'' if name.startswith('empty') else '\n'.join(lines)+'\n')
        if name in ('all-missing','constant'):write('input.geno',(('9' if name=='all-missing' else '0')*54+'\n')*2200)
        if name in ('one-snp','two-snps'):
            n=1 if name=='one-snp' else 2;write('input.geno','\n'.join(genotypes[:n])+'\n')
            write('input.snp',''.join((work/'input.snp').read_text().splitlines(True)[:n]))
        if name in ('missing-data','oracle-missing','oracle-diff-missing'):
            write('input.geno',''.join(''.join('9' if (s*7+i)%11==0 else v for i,v in enumerate(row))+'\n' for s,row in enumerate(genotypes)))
        if name=='oracle-diff-missing':
            write('input.geno',''.join(''.join('9' if (i//6==3 and s%3==0) or (i//6==5 and s%5==0) else v
                      for i,v in enumerate(row))+'\n' for s,row in enumerate(genotypes)))
        if name in ('oracle-fancy','oracle-strict'):
            write('input.geno',''.join(('9'*6+'0'*6+'0'*6+row[18:])+'\n' if s%4==0 else row+'\n' for s,row in enumerate(genotypes)))
        if name=='physical-subset':
            indices=[i for i in range(54) if i%6<3];write('input.ind',''.join(people[i]+'\n' for i in indices))
            write('input.geno',''.join(''.join(row[i] for i in indices)+'\n' for row in genotypes))
        if name.startswith('physical-seed-') or name=='physical-one':
            seed=name.rsplit('-',1)[1] if name!='physical-one' else '0';limit=1 if name=='physical-one' else 3
            sampled=subprocess.run([str(probe),f'sampling-{seed}-{limit}'],env=env,cwd=work,capture_output=True,check=True)
            (work/'sampling.stdout').write_bytes(sampled.stdout)
            indices=[int(s) for s in sampled.stdout.splitlines() if s.isdigit()]
            if len(indices)!=5*limit:raise RuntimeError('incorrect physical subset size')
            write('input.ind',''.join(people[i]+'\n' for i in indices))
            write('input.geno',''.join(''.join(row[i] for i in indices)+'\n' for row in genotypes))
        if name in ('xdata','noxdata-no','x-explicit','x-one-chromosome') or name.startswith('oracle-x'):
            write('input.snp',(work/'input.snp').read_text().replace(' 22 ',' 23 '))
            write('input.ind',''.join(s.replace(' U ',' F ' if 'female' in name else ' U ' if 'unknown' in name else ' M ' if 'male' in name or i%2 else ' F ')+'\n' for i,s in enumerate(people)))
            if ('-f2' in name and 'female' not in name) or name in ('x-one-chromosome','oracle-x-male-partial-overlap'):
                # Keep >=2 observed haploid chromosomes at each population/site.
                # A single observed chromosome has no unbiased overlap correction.
                write('input.geno',''.join(row.replace('1','0')+'\n' for row in genotypes))
            if name in ('x-one-chromosome','oracle-x-male-partial-overlap'):
                records=(work/'input.ind').read_text().splitlines();calls=(work/'input.geno').read_text().splitlines()
                indices=[i for i in range(54) if i%6==0 or (name!='x-one-chromosome' and i//6!=1)]
                write('input.ind',''.join(records[i].replace(' F ',' M ')+'\n' for i in indices))
                write('input.geno',''.join(''.join(row[i] for i in indices)+'\n' for row in calls))
        if name in ('physical-fallback','gfromp'):
            if name=='physical-fallback':write('input.snp',''.join(' '.join(s.split()[:2]+['0']+s.split()[3:])+'\n' for s in (work/'input.snp').read_text().splitlines()))
        if name=='badsnp':write('badsnps','rs00000\nrs00200\n')
        if name.startswith(('block-','oracle-')):
            label=lambda i:str(i//100+1)
            if name.startswith('oracle-x'):label=lambda i:str((i%100)//10+1)
            if name=='block-overflow':label=lambda i:'2221'
            if name=='block-intmax':label=lambda i:'2147483647'
            if name=='block-negative':label=lambda i:'-1'
            if name=='block-sparse':label=lambda i:str((i//100)*50+1)
            if name=='block-partial':label=lambda i:'1oops'
            write('blocks',''.join(f'rs{i:05d} {label(i)}\n' for i in range(2200)))
            if name=='block-duplicate':write('blocks',(work/'blocks').read_text()+'rs00000 2\n')
            if name=='block-missing':(work/'blocks').unlink()
        if name.startswith('oracle-'):
            qs=[s.split() for s in (work/'ratios').read_text().splitlines() if s.strip()]
            m['oracles'][name]=oracle(work,qs,fancy=name!='oracle-strict',difference=name.startswith('oracle-diff'),sex_aware=name.startswith('oracle-x'))
        if name.startswith(('format-','gzip-','duplicate-')) and name not in ('duplicate-ind','duplicate-snp'):
            kind=name.split('-',1)[1];f={'text':'input.geno','packed':'output.geno','tgeno':'input.tgeno','ancestry':'input.ancestry','ped':'plink.ped','bed':'plink.bed'}.get(kind,'input.geno')
            if name.startswith('gzip-'):f+='.gz'
            text=text.replace('genotypename: input.geno','genotypename: '+f)
            if kind in ('ped','bed'):
                fmt='PED' if kind=='ped' else 'PACKEDPED';text=text.replace('input.snp',fmt+'.pedsnp').replace('input.ind',fmt+'.pedind')
            if kind=='corrupt':(work/f).write_bytes(b'invalid gzip')
            if kind=='truncated':(work/f).write_bytes((work/f).read_bytes()[:-9])
            if kind=='crc':
                data=bytearray((work/f).read_bytes());data[-8]^=1;(work/f).write_bytes(data)
            if kind=='reader-fatal':(work/f).write_bytes(gzip.compress(b'invalid genotypes\n',mtime=0))
            if kind=='concatenated':
                data=(work/'input.geno').read_bytes();(work/f).write_bytes(gzip.compress(data[:12001],mtime=0)+gzip.compress(data[12001:],mtime=0))
            if name.startswith('duplicate-'):
                f=({'ped':'PED.pedind','bed':'PACKEDPED.pedind'}.get(kind,'input.ind'))
                records=(work/f).read_text().splitlines();fields=records[1].split();first=records[0].split();fields[:2 if kind in ('ped','bed') else 1]=first[:2 if kind in ('ped','bed') else 1];records[1]=' '.join(fields)
                write(f,'\n'.join(records)+'\n')
        if '-format-' in name and name.startswith('oracle-x-'):
            kind=name.rsplit('-',1)[1];fmt={'packed':'PACKEDANCESTRYMAP','tgeno':'PACKEDANCESTRYMAP','ancestry':'ANCESTRYMAP','ped':'PED','bed':'PACKEDPED'}[kind]
            out={'packed':'x.geno','tgeno':'x.geno','ancestry':'x.ancestry','ped':'x.ped','bed':'x.bed'}[kind]
            xsn='x.pedsnp' if kind in ('ped','bed') else 'x.snp';xin='x.pedind' if kind in ('ped','bed') else 'x.ind'
            write('par.xconvert','genotypename: input.geno\nsnpname: input.snp\nindivname: input.ind\noutputformat: '+fmt+'\ngenotypeoutname: '+out+'\nsnpoutname: '+xsn+'\nindivoutname: '+xin+'\noutputgroup: YES\n')
            invoke('prepare-'+name,'convertf',['-p','par.xconvert'],work)
            if kind=='tgeno':
                invoke('transpose-'+name,'transpose',['x.geno','x.tgeno'],work);out='x.tgeno'
            text=text.replace('genotypename: input.geno','genotypename: '+out).replace('snpname: input.snp','snpname: '+xsn).replace('indivname: input.ind','indivname: '+xin)
        if name=='missing-geno':(work/'input.geno').unlink()
        if name=='truncated-text':write('input.geno','\n'.join(genotypes[:20])+'\n')
        if name=='bad-genotype':write('input.geno','x'+(work/'input.geno').read_text()[1:])
        if name=='missing-popfile':(work/'ratios').unlink()
        if name in ('omitted-popfile','omitted-geno'):
            text=re.sub(r'(?m)^'+('popfilename' if name=='omitted-popfile' else 'genotypename')+r':.*\n','',text)
        if name in ('packed-short','tgeno-short'):
            f='output.geno' if name=='packed-short' else 'input.tgeno';(work/f).write_bytes((work/f).read_bytes()[:50]);text=text.replace('genotypename: input.geno','genotypename: '+f)
        if name in ('output','outputname'):write('result.out','preserve existing output\n')
        if name=='verbose':args+=['-V']
        if name in ('space-unicode','forward-paths'):
            directory=work/('space # \u03b1' if name=='space-unicode' else 'paths');directory.mkdir()
            for f in ('input.geno','input.snp','input.ind','ratios'):
                shutil.copyfile(work/f,directory/f);path=str(directory/f)
                if name=='forward-paths':path=path.replace('\\','/')
                if os.name=='nt':path='"'+path+'"'
                text=re.sub(r'(?m)(: )'+re.escape(f)+r'$',lambda m:m[1]+path,text)
        if name=='bom':(work/'par').write_bytes(b'\xef\xbb\xbf'+text.encode())
        elif name=='utf16':(work/'par').write_bytes(text.encode('utf-16'))
        elif name=='crlf-macro':(work/'par').write_bytes(('DIR: .\n'+text.replace('genotypename: input.geno','genotypename: DIR/input.geno')).replace('\n','\r\n').encode())
        else:write('par',text)
        expected='failure' if name in reject or (repairs and os.name!='nt' and name in ('bom','space-unicode')) else 'success'
        invoke(name,'qpF4ratio',args,work,expected)
    for name,args,expect in [('help',['-h'],'success'),('version',['-v'],'success'),('no-args',[],'success'),
                             ('invalid-option',['-z'],'failure'),('missing-value',['-p'],'failure'),('missing-par',['-p','absent'],'failure'),
                             ('version-then-run',['-v','-p','par.qpF4ratio'],'success')]:
        invoke('cli-'+name,'qpF4ratio',args,common,expect)
    for name,args in [('default',['-p','par.qp4diff']),('block-overflow',['-p','par.qp4diff'])]:
        work=output/('sibling-'+name);shutil.copytree(common,work)
        if name=='block-overflow':
            (work/'par.qp4diff').write_text((work/'par.qp4diff').read_text()+'blockname: blocks\n',newline='\n')
            (work/'blocks').write_text(''.join(f'rs{i:05d} 2221\n' for i in range(2200)),newline='\n')
        invoke('sibling-'+name,'qp4diff',args,work,'success')
    m['completed']=True;(output/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    verify(output)


def verify(directory):
    m=json.loads((directory/'manifest.json').read_text());issues=[]
    if not m['completed']:issues.append('incomplete')
    if not m['packed_roundtrip_exact']:issues.append('packed roundtrip bytes differ')
    for name,c in m['cases'].items():
        code=c.get('returncode')
        if code is None or (code!=0)!=(c['expect']=='failure'):issues.append(name+': exit contract')
        if c['sanitizer']:issues.append(name+': sanitizer')
        if code is not None and ((code < 0 and code != -6) or
                (code >= 0x80000000 and code not in (3221226505,4294967295))):
            issues.append(name+': unexpected signal or system exception')
        if c['temporaries'] or c['external_temporaries']:issues.append(name+': retained temporary')
        for row in c['rows']:
            if any(re.fullmatch(r'[+-]?(?:inf|nan)',t,re.I) for t in row):issues.append(name+': nonfinite result');break
    for name,expected in m['oracles'].items():
        if rows(directory,name)!=expected:issues.append(name+': independent oracle differs')
    cases=m['cases'];default=cases['default']['rows']
    for name in ('limit-3','limit-1'):
        if cases[name]['rows']==default:issues.append(name+': limit has no effect')
    for name in ('output','outputname'):
        if cases[name]['files']['result.out']['bytes']==0:issues.append(name+': output file truncated/empty')
    if m.get('repairs'):
        for name in ('output','outputname'):
            if (directory/name/'result.out').read_bytes()!=b'preserve existing output\n':issues.append(name+': original output not preserved')
        if sha(directory/'output-source-collision/input.geno')!=cases['output-source-collision']['inputs']['input.geno']:
            issues.append('output-source-collision: input destroyed')
        for left,right in [('limit-3','physical-seed-0'),('limit-zero','physical-seed-0'),('limit-77','physical-seed-77'),
                           ('limit-repeat','physical-seed-77'),('limit-123','physical-seed-123'),('limit-seed-one','physical-seed-1'),
                           ('limit-high','physical-seed-2147483648'),('limit-1','physical-one')]:
            if cases[left]['rows']!=cases[right]['rows']:issues.append(left+': physical seeded subset differs')
        if cases['limit-77']['rows']==cases['limit-123']['rows']:issues.append('different seeds ineffective')
        version=(directory/'cli-version.stdout').read_text().splitlines()
        if len(version)!=1 or not version[0].startswith('version: 2010') or (directory/'cli-version.stderr').stat().st_size:
            issues.append('version does not exit cleanly')
        if cases['cli-version-then-run']['rows']:issues.append('version continued analysis')
        if len(cases['many-ratios']['rows'])!=17:issues.append('parser row growth lost results')
        for n,c in cases.items():
            if c['tool']=='qpF4ratio' and c['expect']=='failure' and c['rows']:
                if n!='zero-bottom-diff' or len(c['rows'])!=1 or c['rows'][0][:2]!=['q4rat','A:']:
                    issues.append(n+': undefined scientific output on rejection')
    (directory/'verification.json').write_text(json.dumps(dict(issues=issues),indent=2)+'\n')
    print(directory,len(cases),'cases;',len(issues),'audit observations',flush=True)
    return bool(issues)


def compare(left,right):
    a,b=[json.loads((p/'manifest.json').read_text()) for p in (left,right)]
    result={};diff=[]
    for name in sorted(a['cases'].keys()|b['cases'].keys()):
        if name not in a['cases'] or name not in b['cases']:result[name]=['absent'];continue
        x,y=a['cases'][name],b['cases'][name];errors=[]
        if x.get('returncode')!=y.get('returncode'):errors.append('exit')
        for stream in ('stdout','stderr'):
            u,v=[normal((p/f'{name}.{stream}').read_bytes()) for p in (left,right)]
            if u!=v:
                errors.append(stream);diff.extend(difflib.unified_diff(u.splitlines(True),v.splitlines(True),fromfile=f'left/{name}.{stream}',tofile=f'right/{name}.{stream}'))
        if x['rows']!=y['rows']:errors.append('scientific rows')
        for f in ('output.geno','input.tgeno','roundtrip.geno','result.out'):
            if x['files'].get(f)!=y['files'].get(f):errors.append(f)
        result[name]=errors
    target=right/('comparison-'+left.name)
    target.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    target.with_suffix('.diff').write_text(''.join(diff),encoding='utf-8',errors='surrogateescape')
    good=[n for n in result if not result[n]]
    scientific=[n for n in result if 'scientific rows' in result[n]]
    print('exact',len(good),'of',len(result),'scientific differences',scientific,flush=True)
    return any(result.values())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bin',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--compare',type=Path,nargs=2);p.add_argument('--verify',type=Path)
    p.add_argument('--repairs',action='store_true');p.add_argument('--probe',type=Path)
    a=p.parse_args()
    if a.compare:sys.exit(compare(*(v.resolve() for v in a.compare)))
    elif a.verify:sys.exit(verify(a.verify.resolve()))
    elif a.bin and a.output:
        if a.repairs and not a.probe:p.error('--repairs requires --probe for physical seeded subsets')
        run(a.bin.resolve(),a.output.resolve(),a.repairs,a.probe.resolve() if a.probe else None)
    else:p.error('use --bin DIR --output NEW_DIR')
