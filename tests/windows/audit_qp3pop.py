"""T05 qp3Pop: raw streams, exact comparisons and independent f3 oracles.

This is an audit runner, not a passing-test wrapper: observed defects remain
visible in verification.json. Each output directory must be new.
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


def rows(directory, name):
    text = (directory / (name + '.stdout')).read_text(errors='surrogateescape')
    return [s.split() for s in text.splitlines()
            if s.lstrip().startswith(('result:', 'no data'))]


def oracle(work, triples, inbreed=False, outgroup=False, weighted=False):
    """Independent allele/sample counts and unequal-block delete jackknife.

    Inbred correction counts pairs of chromosomes from DIFFERENT individuals;
    ordinary correction counts all distinct chromosomes. Explicit fixture block
    IDs avoid relying on the production block constructor. Compare printed tokens.
    """
    records = [s.split() for s in (work/'input.ind').read_text().splitlines()]
    people = [s[2] for s in records]
    chromosomes = [int(s.split()[1]) for s in (work/'input.snp').read_text().splitlines()]
    xonly = (work/'par').exists() and 'chrom: 23\n' in (work/'par').read_text()
    labels = dict(s.split() for s in (work/'blocks').read_text().splitlines())
    answers = []
    for triple in triples:
        blocks, polymorphic = {}, 0
        for si, row in enumerate((work/'input.geno').read_text().splitlines()):
            label = int(labels[f'rs{si:05d}'])
            if label < 0: continue
            if xonly and chromosomes[si]!=23: continue
            groups = [[(int(v),2) if chromosomes[si]!=23 or rec[1]=='F' else (int(v)//2,1)
                       for rec,v in zip(records,row) if rec[2]==pop and v!='9'
                       and not (chromosomes[si]==23 and rec[1]!='F' and v=='1')] for pop in triple]
            if any(not g for g in groups): continue
            freq = [sum(a for a,n in g)/sum(n for a,n in g) for g in groups]
            target = groups[2]
            n = sum(n for a,n in target)
            if inbreed:
                if len(target)<2: continue
                pairs = [(a,b) for i,a in enumerate(target) for j,b in enumerate(target) if i!=j]
                h = sum(a[0]*(b[1]-b[0]) for a,b in pairs)/sum(a[1]*b[1] for a,b in pairs)
            else:
                if n<2:continue
                count=sum(a for a,n in target)
                h = count*(n-count)/(n*(n-1))
            top = (freq[2]-freq[0])*(freq[2]-freq[1])+freq[2]*(1-freq[2])-h
            bot = .001 if outgroup else 2*h
            wt = 1.
            if weighted:
                sizes = [len(g) if inbreed else sum(n for a,n in g) for g in groups]
                wt = 1/(1/sizes[2]+1/sizes[0])/(1/sizes[2]+1/sizes[1])
            v = blocks.setdefault(label,[0.,0.,0])
            v[0] += top*wt; v[1] += bot*wt; v[2] += 1
            if 0.0001 <= sum(freq)/3 <= .9999: polymorphic += 1
        values = [blocks[k] for k in sorted(blocks)]
        top,bot,count = [sum(v[i] for v in values) for i in range(3)]
        mean = top/(bot+1e-10)
        leave = [(top-v[0])/(bot-v[1]+1e-10) for v in values]
        estimate = sum(mean-j for j in leave)+sum(v[2]*j for v,j in zip(values,leave))/count
        variance = sum(((count/v[2])*mean-(count/v[2]-1)*j-estimate)**2/(count/v[2]-1)
                       for v,j in zip(values,leave))/len(values)
        sd = math.sqrt(max(0,variance))
        answers.append(['result:',*triple,f'{estimate:.6f}',f'{sd:.6f}',f'{estimate/sd:.3f}',str(polymorphic)])
    return answers


def run(bindir, output, probe=None, repairs=False):
    output.mkdir(parents=True,exist_ok=False)
    if os.name=='nt':
        import ctypes
        ctypes.windll.kernel32.SetErrorMode(3)
    common=output/'fixtures'; parity.fixtures(common); (common/'tmp').mkdir()
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_CORETYPE='NEHALEM',
             LC_ALL='C',STMP='tmp',ASAN_OPTIONS='detect_leaks=0:abort_on_error=1',
             UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    env['PATH']=str(bindir)+os.pathsep+env.get('PATH','')
    m=dict(platform=sys.platform,bin=str(bindir),environment={k:env[k] for k in
        ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','OPENBLAS_CORETYPE','LC_ALL','STMP','ASAN_OPTIONS','UBSAN_OPTIONS')},
        cases={},oracles={},executables={},completed=False,repairs=repairs)
    (output/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')

    def invoke(name,tool,args,work,expect='success',exe=None):
        exe=exe or bindir/(tool+('.exe' if os.name=='nt' else ''))
        m['executables'][tool]=sha(exe)
        c=dict(tool=tool,args=args,expect=expect,inputs={p.name:sha(p) for p in work.iterdir() if p.is_file()})
        before=set(Path('/var/tmp').glob('genotmp:*')) if os.name!='nt' else set()
        try:
            p=subprocess.run([exe.name,*args],executable=str(exe),cwd=work,env=env,capture_output=True,
                             timeout=12,preexec_fn=no_core if os.name!='nt' else None)
            c['returncode']=p.returncode; streams=p.stdout,p.stderr
        except subprocess.TimeoutExpired as e:
            c['timeout']=True; streams=e.stdout or b'',e.stderr or b''
        for s,data in zip(('stdout','stderr'),streams): (output/f'{name}.{s}').write_bytes(data)
        c['temporaries']=sorted(p.name for p in (work/'tmp').iterdir())
        c['external_temporaries']=[]
        if os.name!='nt':
            # Only remove a file named by THIS child's output, absent beforehand.
            for token in set(re.findall(rb'/var/tmp/genotmp:\d+(?:\.[A-Za-z0-9]{6})?',streams[0])):
                path=Path(os.fsdecode(token))
                if path not in before and path.is_file():
                    c['external_temporaries'].append(dict(path=str(path),sha256=sha(path))); path.unlink()
        c['files']={f:sha(work/f) for f in ('details.out','result.out','output.geno','input.tgeno','roundtrip.geno') if (work/f).is_file()}
        c['rows']=rows(output,name)
        c['sanitizer']=bool(re.search(rb'AddressSanitizer|runtime error:|LeakSanitizer',streams[1]))
        m['cases'][name]=c

    for fmt,out in [('PACKEDANCESTRYMAP','output.geno'),('ANCESTRYMAP','input.ancestry'),('PED','plink.ped'),('PACKEDPED','plink.bed')]:
        par='genotypename: input.geno\nsnpname: input.snp\nindivname: input.ind\noutputformat: '+fmt+'\ngenotypeoutname: '+out+'\nsnpoutname: '+fmt+'.pedsnp\nindivoutname: '+fmt+'.pedind\noutputgroup: YES\n'
        (common/'par.convert').write_text(par)
        invoke('prepare-'+fmt,'convertf',['-p','par.convert'],common)
    invoke('prepare-transpose','transpose',['output.geno','input.tgeno'],common)
    invoke('prepare-roundtrip','transpose',['input.tgeno','roundtrip.geno'],common)
    m['packed_roundtrip_exact']=(common/'output.geno').read_bytes()==(common/'roundtrip.geno').read_bytes()
    for f in ('input.geno','output.geno','input.tgeno','input.ancestry','plink.ped','plink.bed'):
        (common/(f+'.gz')).write_bytes(gzip.compress((common/f).read_bytes(),mtime=0))
    base='genotypename: input.geno\nsnpname: input.snp\nindivname: input.ind\npopfilename: triples\nseed: 77\nblgsize: .005\n'
    modes={'default':'','explicit-defaults':'inbreed: NO\noutgroupmode: NO\nsizeweight: NO\njackweight: YES\npubjack: NO\njackquart: -1\nnoxdata: YES\nnumchrom: 22\n',
           'inbreed':'inbreed: YES\n','outgroup':'outgroupmode: YES\n','outgroup-inbreed':'outgroupmode: YES\ninbreed: YES\n',
           'weighted':'sizeweight: YES\n','weighted-inbreed':'sizeweight: YES\ninbreed: YES\n',
           'jack-unweighted':'jackweight: NO\n','jackquart':'jackquart: .1\n','pubjack':'pubjack: YES\njackquart: .1\n',
           'quart-half':'jackquart: .5\n','quart-large':'jackquart: 2\n','quart-nan':'jackquart: nan\n','quart-inf':'jackquart: inf\n',
           'chrom':'chrom: 2\n','nochrom':'nochrom: 2\n','xdata':'xdata: YES\n','noxdata-no':'noxdata: NO\n',
           'x-mixed':'chrom: 23\ninbreed: YES\noutgroupmode: YES\n','x-male':'chrom: 23\ninbreed: YES\noutgroupmode: YES\n',
           'numchrom':'numchrom: 10\n','numchrom-intmax':'numchrom: 2147483647\n','numchrom-zero':'numchrom: 0\n',
           'limit-77':'popsizelimit: 3\n','limit-123':'popsizelimit: 3\nseed: 123\n','limit-repeat':'popsizelimit: 3\n',
           'limit-one':'popsizelimit: 1\ninbreed: YES\noutgroupmode: YES\n','unlimited':'popsizelimit: 100\n',
           'zero-blocksize':'blgsize: 0\n','negative-blocksize':'blgsize: -1\n','nan-blocksize':'blgsize: nan\n','inf-blocksize':'blgsize: inf\n',
           'one-block':'chrom: 1\nblgsize: 1\n','instem':'','badsnp':'badsnpname: badsnps\n',
           'details':'snpdetailsname: details.out\n','details-multi':'snpdetailsname: details.out\n',
           'details-cli':'','details-missing-parent':'snpdetailsname: absent/details.out\n',
           'no-hets':'','no-hets-outgroup':'outgroupmode: YES\n','no-hets-inbreed':'inbreed: YES\noutgroupmode: YES\n',
           'no-hets-override':'inbreed_override: YES\noutgroupmode: YES\n','fixed-target':'inbreed_override: YES\n',
           'missing-data':'','all-missing':'inbreed_override: YES\n','constant':'inbreed_override: YES\n',
           'one-snp':'inbreed_override: YES\n','two-snps':'','no-valid-snps':'chrom: 99\n','physical-fallback':'gfromp: YES\n',
           'unknown-source':'','unknown-target':'inbreed_override: YES\n','same-sources':'','source-target':'','repeat-triple':'',
           'empty-triples':'','bad-triples':'','extra-column':'','colon-triples':'','line-cli':'','line-reversed':'',
           'duplicate-ind':'','duplicate-snp':'','empty-ind':'','empty-snp':'','missing-geno':'','truncated-text':'','bad-genotype':'',
           'bom':'','crlf-macro':'','utf16':'','space-unicode':'','forward-paths':'','verbose':'','cli-seed':'popsizelimit: 3\n',
           'bad-number':'popsizelimit: 3oops\n'}
    for k,v in {'gfromp':'YES','details':'YES','output':'result.out','f3log':'result.out','outpop':'Absent','nostatslim':'999999',
                'baseval':'99','dumpname':'absent','loadname':'absent'}.items(): modes['control-'+k]=k+': '+v+'\n'
    for fmt in ('text','packed','tgeno','ancestry','ped','bed'):
        modes['format-'+fmt]='';modes['gzip-'+fmt]=''
    for k in ('corrupt','truncated','crc','reader-fatal'): modes['gzip-'+k]=''
    for k in ('overflow','intmax','negative','sparse','partial'): modes['block-'+k]='blockname: blocks\n'
    for k in ('ordinary','inbreed','outgroup','weighted','missing','permutations','x-mixed','x-male'):
        modes['oracle-'+k]='blockname: blocks\n'+('inbreed: YES\n' if k=='inbreed' or k.startswith('x-') else '')+('outgroupmode: YES\n' if k=='outgroup' or k.startswith('x-') else '')+('sizeweight: YES\n' if k in ('weighted','missing') else '')+('chrom: 23\n' if k.startswith('x-') else '')
    if probe:
        modes.update({'physical-subset-77':'','physical-subset-123':''})
    if repairs:
        modes.update({'fixed-target-inbreed':'inbreed: YES\n','fixed-target-outgroup':'inbreed: YES\noutgroupmode: YES\n',
                      'limit-zero':'popsizelimit: 3\nseed: 0\n','limit-implicit':'popsizelimit: 3\n',
                      'limit-1':'popsizelimit: 3\nseed: 1\n','limit-high':'popsizelimit: 3\nseed: -2147483648\n',
                      'outputname':'outputname: result.out\n','details-low-data':'snpdetailsname: details.out\ninbreed_override: YES\n'})
        for k in ('female','weighted','unknown'):
            modes['oracle-x-'+k]='blockname: blocks\nchrom: 23\ninbreed: YES\noutgroupmode: YES\n'+('sizeweight: YES\n' if k=='weighted' else '')
        if probe:modes.update({'physical-subset-1':'','physical-subset-2147483648':''})
    reject={'quart-half','quart-large','quart-nan','quart-inf','numchrom-intmax','numchrom-zero','zero-blocksize','negative-blocksize','nan-blocksize','inf-blocksize','one-block',
            'details-missing-parent','bad-triples','duplicate-ind','duplicate-snp','empty-ind','empty-snp','missing-geno','truncated-text','bad-genotype','two-snps','source-target',
            'no-hets','no-hets-outgroup','bad-number','block-overflow','block-intmax','block-partial','no-valid-snps','utf16'}
    reject.update('gzip-'+k for k in ('corrupt','truncated','crc','reader-fatal'))
    if repairs:
        reject.update(n for n in modes if n.startswith('control-'))
        reject.update(('physical-fallback','fixed-target','fixed-target-inbreed','outputname'))
    for name,extra in modes.items():
        work=output/name; work.mkdir();(work/'tmp').mkdir()
        for p in common.iterdir():
            if p.is_file():shutil.copyfile(p,work/p.name)
        text=base
        for key in re.findall(r'(?m)^([^:\s]+):',extra): text=re.sub(r'(?m)^'+re.escape(key)+r':.*\n','',text)
        text+=extra;args=['-p','par']
        def write(f,s): (work/f).write_text(s,encoding='utf-8',newline='\n')
        genotype=(work/'input.geno').read_text().splitlines()
        people=(work/'input.ind').read_text().splitlines()
        if name in ('details','details-cli'):write('triples','A B X\n')
        if name in ('details-cli','details-multi'):args+=['-f','details.out']
        if name=='cli-seed':text=text.replace('seed: 77\n','');args+=['-s','123']
        if name=='limit-implicit':text=text.replace('seed: 77\n','')
        if name=='verbose':args+=['-V']
        if name=='instem':text=re.sub(r'(?m)^(genotypename|snpname|indivname):.*\n','',text)+'instem: input\n'
        if name=='badsnp':write('badsnps','rs00000\nrs00200\n')
        if name=='physical-fallback':write('input.snp',''.join(' '.join(s.split()[:2]+['0']+s.split()[3:])+'\n' for s in (work/'input.snp').read_text().splitlines()))
        changes={'unknown-source':'Absent B X\n','unknown-target':'A B Absent\n','same-sources':'A A X\n','source-target':'A B A\n',
                 'repeat-triple':'A B X\nA B X\n','empty-triples':'','bad-triples':'A B\n','extra-column':'A B X ignored\n','colon-triples':'A : B X\n'}
        if name in changes:write('triples',changes[name])
        if name=='line-cli':args+=['-L','2','-H','2']
        if name=='line-reversed':args+=['-L','2','-H','1']
        if name in ('duplicate-ind','duplicate-snp','empty-ind','empty-snp'):
            f='input.ind' if name.endswith('ind') else 'input.snp';lines=(work/f).read_text().splitlines()
            if name.startswith('duplicate'):lines[1]=' '.join([lines[0].split()[0],*lines[1].split()[1:]])
            write(f,'' if name.startswith('empty') else '\n'.join(lines)+'\n')
        if name.startswith('no-hets') or name.startswith('fixed-target'):
            write('input.geno',''.join(''.join(('0' if name.startswith('fixed-target') else '2') if 24<=i<30 and (v=='1' or name.startswith('fixed-target')) else v for i,v in enumerate(row))+'\n' for row in genotype))
        if name in ('constant','all-missing'):
            write('input.geno',(('0' if name=='constant' else '9')*54+'\n')*2200)
        if name in ('one-snp','two-snps','details-low-data'):
            n=2 if name=='two-snps' else 1
            write('input.geno','\n'.join(genotype[:n])+'\n');write('input.snp',''.join((work/'input.snp').read_text().splitlines(True)[:n]))
        if name in ('missing-data','oracle-missing'):
            write('input.geno',''.join(''.join('9' if (s*7+i)%11==0 else v for i,v in enumerate(row))+'\n' for s,row in enumerate(genotype)))
        if name.startswith('physical-subset-'):
            sampled=subprocess.run([str(probe),'sampling-'+name.rsplit('-',1)[1]],cwd=work,env=env,capture_output=True,check=True)
            indices=[int(s) for s in sampled.stdout.splitlines() if s.isdigit()]
            if len(indices)!=12:raise RuntimeError('physical subset requires 12 selected people')
            (work/'sampling.stdout').write_bytes(sampled.stdout)
            write('input.ind',''.join(people[i]+'\n' for i in indices))
            write('input.geno',''.join(''.join(row[i] for i in indices)+'\n' for row in genotype))
        if name in ('xdata','noxdata-no','x-mixed','x-male') or name.startswith('oracle-x'):
            write('input.snp',(work/'input.snp').read_text().replace(' 22 ',' 23 '))
            write('input.ind',''.join(s.replace(' U ',' U ' if name.endswith('x-unknown') else ' F ' if name.endswith('x-female') else ' M ' if name.endswith('x-male') or i%2 else ' F ')+'\n' for i,s in enumerate(people)))
        if name.startswith(('block-','oracle-')):
            label=lambda i:str(i//100+1)
            if name.startswith('oracle-x'):label=lambda i:str((i%100)//10+1)
            if name=='block-overflow':label=lambda i:'2221'
            if name=='block-intmax':label=lambda i:'2147483647'
            if name=='block-negative':label=lambda i:'-1'
            if name=='block-sparse':label=lambda i:str((i//100)*50+1)
            if name=='block-partial':label=lambda i:'1oops'
            write('blocks',''.join(f'rs{i:05d} {label(i)}\n' for i in range(2200)))
        if name.startswith('oracle-'):
            triples=[['A','B','X']]
            if name=='oracle-permutations':triples=list(itertools.permutations(triples[0]))
            write('triples',''.join(' '.join(t)+'\n' for t in triples))
            write('par',text)
            m['oracles'][name]=oracle(work,triples,name=='oracle-inbreed' or name.startswith('oracle-x'),name=='oracle-outgroup' or name.startswith('oracle-x'),name in ('oracle-weighted','oracle-missing','oracle-x-weighted'))
        if name.startswith(('format-','gzip-')):
            kind=name.split('-',1)[1];f={'text':'input.geno','packed':'output.geno','tgeno':'input.tgeno','ancestry':'input.ancestry','ped':'plink.ped','bed':'plink.bed'}.get(kind,'input.geno')
            if name.startswith('gzip-'):f+='.gz'
            text=text.replace('genotypename: input.geno','genotypename: '+f)
            if kind in ('ped','bed'):
                fmt='PED' if kind=='ped' else 'PACKEDPED';text=text.replace('input.snp',fmt+'.pedsnp').replace('input.ind',fmt+'.pedind')
            if name=='gzip-corrupt':(work/f).write_bytes(b'invalid gzip')
            if name=='gzip-truncated':(work/f).write_bytes((work/f).read_bytes()[:-9])
            if name=='gzip-crc':
                data=bytearray((work/f).read_bytes());data[-8]^=1;(work/f).write_bytes(data)
            if name=='gzip-reader-fatal':(work/f).write_bytes(gzip.compress(b'invalid genotypes\n',mtime=0))
        if name=='missing-geno':(work/'input.geno').unlink()
        if name=='truncated-text':write('input.geno','\n'.join(genotype[:20])+'\n')
        if name=='bad-genotype':write('input.geno','x'+(work/'input.geno').read_text()[1:])
        if name in ('control-output','control-f3log','outputname'):write('result.out','preserve existing output\n')
        if name in ('space-unicode','forward-paths'):
            directory=work/('space # \u03b1' if name=='space-unicode' else 'paths');directory.mkdir()
            for f in ('input.geno','input.snp','input.ind','triples'):
                shutil.copyfile(work/f,directory/f);path=str(directory/f)
                if name=='forward-paths':path=path.replace('\\','/')
                if os.name=='nt':path='"'+path+'"'
                text=re.sub(r'(?m)(: )'+re.escape(f)+r'$',lambda m:m[1]+path,text)
        if name=='bom':(work/'par').write_bytes(b'\xef\xbb\xbf'+text.encode())
        elif name=='utf16':(work/'par').write_bytes(text.encode('utf-16'))
        elif name=='crlf-macro':(work/'par').write_bytes(('DIR: .\n'+text.replace('genotypename: input.geno','genotypename: DIR/input.geno')).replace('\n','\r\n').encode())
        else:write('par',text)
        invoke(name,'qp3Pop',args,work,'failure' if name in reject else 'observe' if name in ('all-missing','constant','one-snp','block-negative','fixed-target','details-low-data') else 'success')
    for name,args,expect in [('help',['-h'],'success'),('version',['-v'],'success'),('no-args',[],'failure'),('invalid-option',['-z'],'failure'),('missing-value',['-p'],'failure'),('missing-par',['-p','absent'],'failure')]:
        invoke('cli-'+name,'qp3Pop',args,common,expect)
    if repairs:invoke('cli-inactive-b','qp3Pop',['-b','1'],common,'failure')
    if repairs:
        # Exercise both metadata readers and every genotype reader with actual X
        # sexes, rather than comparing only autosomal format round trips.
        for kind,fmt in [('packed','PACKEDANCESTRYMAP'),('ancestry','ANCESTRYMAP'),('ped','PED'),('bed','PACKEDPED')]:
            work=output/('xformat-'+kind);shutil.copytree(output/'oracle-x-mixed',work)
            ped=kind in ('ped','bed')
            geno='xout.'+('ped' if kind=='ped' else 'bed' if kind=='bed' else 'geno')
            snp='xout.'+('pedsnp' if ped else 'snp');ind='xout.'+('pedind' if ped else 'ind')
            par='genotypename: input.geno\nsnpname: input.snp\nindivname: input.ind\noutputformat: '+fmt+'\noutputgroup: YES\noutputall: YES\ngenotypeoutname: '+geno+'\nsnpoutname: '+snp+'\nindivoutname: '+ind+'\n'
            (work/'convert.par').write_text(par)
            invoke('prepare-x-'+kind,'convertf',['-p','convert.par'],work)
            text=(work/'par').read_text().replace('genotypename: input.geno','genotypename: '+geno).replace('snpname: input.snp','snpname: '+snp).replace('indivname: input.ind','indivname: '+ind)
            (work/'par').write_text(text)
            invoke('xformat-'+kind,'qp3Pop',['-p','par'],work)
            if kind=='packed':
                trans=output/'xformat-tgeno';shutil.copytree(work,trans)
                invoke('prepare-x-tgeno','transpose',['xout.geno','xout.tgeno'],trans)
                (trans/'par').write_text(text.replace('genotypename: xout.geno','genotypename: xout.tgeno'))
                invoke('xformat-tgeno','qp3Pop',['-p','par'],trans)
    bound=output/'sibling-qpBound';shutil.copytree(common,bound)
    (bound/'bound.triples').write_text(''.join(' '.join([*r[1:4],r[4],r[6]])+'\n' for r in m['cases']['default']['rows']))
    (bound/'par').write_text(base.replace('popfilename: triples','popfilename: bound.triples')+'outpop: Out\n')
    invoke('sibling-qpBound','qpBound',['-p','par'],bound)
    if probe:
        probes=['early-return','negative-type','inbreed-large','sampling-77','sampling-123','jackknife','f3-boundaries']
        if repairs:probes+=['upper-type','inbreed-large-x','jack-half','jack-nan','jack-trim-boundary','details-write-failure']
        for mode in probes:
            work=output/('probe-'+mode);work.mkdir();(work/'tmp').mkdir()
            invoke('probe-'+mode,'qp3pop_probe',[mode],work,'failure' if mode.startswith('jack-') or mode=='details-write-failure' else 'success' if repairs else 'observe',probe)
    m['completed']=True
    (output/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    verify(output)


def verify(directory):
    m=json.loads((directory/'manifest.json').read_text());issues=[]
    for name,c in m['cases'].items():
        rc=c.get('returncode');expect=c['expect']
        if m['platform']!='win32' and name in ('bom','space-unicode'):expect='failure'
        if rc is None or (expect!='observe' and (rc!=0)!=(expect=='failure')):issues.append(name+': exit contract')
        if c['sanitizer']:issues.append(name+': sanitizer')
        if c['temporaries'] or c['external_temporaries']:issues.append(name+': retained temporary')
        if (m.get('repairs') and c['tool']=='qp3Pop' and rc==0 and not name.startswith('cli-')
                and name not in ('empty-triples','line-reversed')):
            if not c['rows'] or b'##end of qp3Pop:' not in (directory/f'{name}.stdout').read_bytes():
                issues.append(name+': missing completed scientific/no-data output')
        if any(re.search(r'(?i)^[+-]?(?:nan|inf)$',token) for row in c['rows'] for token in row):issues.append(name+': nonfinite scientific row')
        if name in m['oracles'] and c['rows']!=m['oracles'][name]:issues.append(name+': independent oracle differs')
    for a,b in [('default','explicit-defaults'),('default','instem'),('default','unlimited'),('default','format-text'),('default','format-packed'),('default','format-tgeno'),('default','format-ancestry'),('limit-77','limit-repeat')]:
        if m['cases'][a]['rows']!=m['cases'][b]['rows']:issues.append(a+'/'+b+': rows differ')
    if m['cases']['limit-77']['rows']==m['cases']['limit-123']['rows']:issues.append('limit-77/limit-123: seed ignored')
    for seed in ('77','123'):
        physical='physical-subset-'+seed
        if physical in m['cases'] and m['cases'][physical]['rows']!=m['cases']['limit-'+seed]['rows']:
            issues.append('limit-'+seed+': differs from seeded physical subset')
    for name in ('control-output','control-f3log'):
        sentinel=__import__('hashlib').sha256(b'preserve existing output\n').hexdigest()
        if m.get('repairs'):
            if m['cases'][name]['files']['result.out']!=sentinel:issues.append(name+': sentinel overwritten')
        elif m['cases'][name]['files']['result.out']==sentinel:issues.append(name+': requested output ignored')
    if 'probe-early-return' in m['cases'] and b'extra open handles: 0' not in (directory/'probe-early-return.stdout').read_bytes():
        issues.append('probe-early-return: leaked SNP-details handles and workspaces')
    if 'probe-inbreed-large' in m['cases']:
        text=(directory/'probe-inbreed-large.stdout').read_text()
        actual=re.search(r'ret=\d+ top=(\S+) bot=(\S+)',text)
        expected=re.search(r'expected top=(\S+) bot=(\S+)',text)
        if not actual or not expected or actual.groups()!=expected.groups():issues.append('probe-inbreed-large: independent pair-count oracle differs')
    details=directory/'details-multi/details.out'
    if details.exists() and len(details.read_bytes().splitlines())!=4400:issues.append('details-multi: earlier triple details overwritten')
    out=(directory/'cli-version.stdout').read_bytes().replace(b'\r\n',b'\n')
    if out!=(b'version: 710.w\n' if m['platform']=='win32' else b'version: 710\n') or (directory/'cli-version.stderr').read_bytes():issues.append('cli-version: version-only contract')
    if not m['packed_roundtrip_exact']:issues.append('packed roundtrip differs')
    if m.get('repairs'):
        if b'error writing SNP details: closed details pipe' not in (directory/'probe-details-write-failure.stderr').read_bytes():issues.append('native write-failure injection did not reach checked details output')
        for kind in ('packed','ancestry','ped','bed','tgeno'):
            if m['cases']['xformat-'+kind]['rows']!=m['oracles']['oracle-x-mixed']:issues.append('xformat-'+kind+': mixed-X oracle differs')
        for a,b in [('default','format-ped'),('default','format-bed'),('default','gzip-ped'),('default','gzip-bed'),
                    ('limit-123','cli-seed'),('limit-zero','limit-1'),('limit-zero','limit-implicit'),
                    ('limit-1','physical-subset-1'),('limit-high','physical-subset-2147483648')]:
            if a in m['cases'] and b in m['cases'] and m['cases'][a]['rows']!=m['cases'][b]['rows']:issues.append(a+'/'+b+': rows differ')
        for name in ('probe-inbreed-large-x',):
            text=(directory/(name+'.stdout')).read_text()
            actual=re.search(r'ret=\d+ top=(\S+) bot=(\S+)',text);expected=re.search(r'expected top=(\S+) bot=(\S+)',text)
            if not actual or not expected or actual.groups()!=expected.groups():issues.append(name+': pair-count oracle differs')
        if (directory/'details-low-data/details.out').stat().st_size==0:issues.append('details-low-data: buffered row lost')
    (directory/'verification.json').write_text(json.dumps(dict(issues=issues),indent=2)+'\n')
    print(directory,len(m['cases']),'cases;',len(issues),'audit observations',flush=True)
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
            u=u.replace('qp3pop_probe.exe','qp3pop_probe');v=v.replace('qp3pop_probe.exe','qp3pop_probe')
            u=u.replace('qpBound.exe','qpBound');v=v.replace('qpBound.exe','qpBound')
            if u!=v:
                errors.append(stream);diff.extend(difflib.unified_diff(u.splitlines(True),v.splitlines(True),fromfile=f'left/{name}.{stream}',tofile=f'right/{name}.{stream}'))
        if x['rows']!=y['rows']:errors.append('scientific rows')
        # Details are text: retain all data/precision/order, permit CRLF only.
        for f in ('details.out','roundtrip.geno'):
            paths=[p/name/f for p in (left,right)]
            if any(p.exists() for p in paths):
                if not all(p.exists() for p in paths):errors.append(f+': absent')
                else:
                    data=[p.read_bytes() for p in paths]
                    if f.endswith('.out'):data=[s.replace(b'\r\n',b'\n') for s in data]
                    if data[0]!=data[1]:errors.append(f+': data')
        result[name]=errors
    target=right/('comparison-'+left.name)
    target.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    target.with_suffix('.diff').write_text(''.join(diff),errors='surrogateescape')
    print('exact',sum(not v for v in result.values()),'of',len(result),'scientific differences',[n for n,v in result.items() if 'scientific rows' in v])
    return any(result.values())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bin',type=Path);p.add_argument('--output',type=Path);p.add_argument('--probe',type=Path)
    p.add_argument('--compare',nargs=2,type=Path);p.add_argument('--verify',type=Path)
    p.add_argument('--repairs',action='store_true',help='enforce the corrected contracts and additional regressions')
    a=p.parse_args()
    if a.compare:sys.exit(compare(*(d.resolve() for d in a.compare)))
    elif a.verify:sys.exit(verify(a.verify.resolve()))
    elif a.bin and a.output:run(a.bin.resolve(),a.output.resolve(),a.probe.resolve() if a.probe else None,a.repairs)
    else:p.error('use --bin DIR --output NEW_DIR')
