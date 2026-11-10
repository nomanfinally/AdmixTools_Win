"""T04: retain raw qpDstat modes, strict comparisons, and independent oracles.

--verify reports defects; a reproduced upstream defect is NOT a passing test.
Output directories must be new. No production code is repaired by this runner.
"""
import argparse
import difflib
import gzip
import hashlib
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def no_core():
    # Fatal-input matrices must not create multi-gigabyte OS core dumps.
    import resource
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))


def normal(data):
    # Lossless decoding: undecodable bytes must not collapse to replacement chars.
    text = data.decode('utf-8', errors='surrogateescape').replace('\r\n', '\n')
    text = re.sub(r'\b(qpDstat|convertf|transpose|qp3Pop|qp4diff|qpF4ratio|qpAdm|qpfstats|qpWave|qpdslow|qpDpart|module_probe)\.exe\b', r'\1', text)
    text = re.sub(r'(version: \d+)\.w\b', r'\1', text)
    text = re.sub(r'(mmfaddr: )(?:0x)?[0-9a-fA-F]+', r'\1<ADDRESS>', text)
    text = re.sub(r'[ ]*-?\d+\.\d+(?= seconds cpu)', ' <CPU>', text)
    text = re.sub(r'(?<=seconds cpu)[ ]*-?\d+\.\d+(?= Mbytes)', ' <MEMORY>', text)
    text = re.sub(r'(?m)^(time in dofstats:)[ ]*\d+\.\d+$', r'\1 <CPU>', text)
    # Only the generated gzip temporary operand, retaining command/diagnostic text.
    text = re.sub(r'(?:/var/tmp|tmp|[^\r\n\" ]+[/\\]tmp)[/\\]genotmp[:.]\d+(?:\.[A-Za-z0-9]{6})?', '<GENOTMP>', text)
    text = re.sub(r'"(<GENOTMP>(?:\.(?:ped|bed))?)"', r'\1', text)
    text = re.sub(r'(?m)^(unzip cmd: gunzip -c )"((?:input\.(?:geno|tgeno|ancestry)|output\.geno|plink\.(?:ped|bed))\.gz)"', r'\1\2', text)
    return text


def oracle(work, quads, f4=False, sizeweight=False):
    """Count alleles independently, then apply the published weighted jackknife.

    Explicit SNP->block fixtures avoid reproducing the production block builder.
    Compare formatted values, not a floating point tolerance.
    """
    people = [s.split()[2] for s in (work / 'input.ind').read_text().splitlines()]
    labels = dict(s.split() for s in (work / 'blocks').read_text().splitlines())
    rows = (work / 'input.geno').read_text().splitlines()
    answers = []
    for quad in quads:
        blocks, baba, abba, total = {}, 0.0, 0.0, 0
        for si, row in enumerate(rows):
            label = int(labels[f'rs{si:05d}'])
            if label < 0:
                continue
            groups = [[int(v) for p, v in zip(people, row) if p == pop and v != '9'] for pop in quad]
            if any(not g for g in groups):
                continue
            a, b, c, d = [sum(2-v for v in g) / (2*len(g)) for g in groups]
            ba = a*(1-b)*c*(1-d) + (1-a)*b*(1-c)*d
            ab = a*(1-b)*(1-c)*d + (1-a)*b*c*(1-d)
            weight = 1.0
            if sizeweight:
                na, nb, nc, nd = [2*len(g) for g in groups]
                weight = (1/(1/na + 1/nb)) * (1/(1/nc + 1/nd))
            entry = blocks.setdefault(label, [0.0, 0.0, 0])
            entry[0] += weight*(ba-ab)
            entry[1] += weight*(1 if f4 else ba+ab)
            entry[2] += 1
            baba += ba
            abba += ab
            total += 1
        values = [blocks[k] for k in sorted(blocks)]
        top, bot, count = [sum(v[i] for v in values) for i in range(3)]
        mean = top/(bot + 1e-20)
        leave = [(top-v[0])/(bot + 1e-20-v[1]) for v in values]
        estimate = sum(mean-j for j in leave) + sum(v[2]*j for v, j in zip(values, leave))/count
        variance = sum(((count/v[2])*mean-(count/v[2]-1)*j-estimate)**2/(count/v[2]-1)
                       for v, j in zip(values, leave))/len(values)
        sd = math.sqrt(max(0, variance))
        z = max(-100, min(100, estimate/(sd+1e-20)))
        answers.append([*quad, format(estimate, '.6f' if f4 else '.4f'),
                        format(sd, '.6f'), format(z, '.3f'),
                        str(math.floor(baba+.5)), str(math.floor(abba+.5)), str(total)])
    return answers


def result_rows(directory, name):
    data = (directory / f'{name}.stdout').read_text(encoding='utf-8', errors='surrogateescape')
    return [s.split()[1:] for s in data.splitlines() if s.startswith('result: ')]


def run(bindir, output, selection='.', probe=None):
    if os.name == 'nt':
        import ctypes
        ctypes.windll.kernel32.SetErrorMode(3)
    output.mkdir(parents=True, exist_ok=False)
    common = output / 'fixtures'
    parity.fixtures(common)
    (common / 'tmp').mkdir()
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
               OPENBLAS_CORETYPE='NEHALEM', LC_ALL='C', STMP='tmp',
               ASAN_OPTIONS='detect_leaks=0:abort_on_error=1',
               UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    env['PATH'] = str(bindir) + os.pathsep + env.get('PATH', '')
    manifest = dict(platform=sys.platform, binary_dir=str(bindir), completed=False,
                    environment={k:env[k] for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS',
                        'OPENBLAS_CORETYPE','LC_ALL','STMP','ASAN_OPTIONS','UBSAN_OPTIONS')},
                    cases={}, executables={}, oracles={})

    def invoke(name, tool, args, work, expected='success', executable=None):
        exe = executable or bindir / (tool + ('.exe' if os.name == 'nt' else ''))
        entry = dict(tool=tool, arguments=args, expected=expected, files={})
        # Only remove a generated Unix temporary absent before this invocation.
        # Never glob-delete leftovers from previous runs or other users.
        before = set(Path('/var/tmp').glob('genotmp:*')) if os.name!='nt' else set()
        if exe.is_file():
            manifest['executables'][tool] = sha(exe)
        try:
            p = subprocess.run([exe.name, *args], executable=str(exe), cwd=work, env=env,
                               capture_output=True, timeout=30,
                               preexec_fn=no_core if os.name!='nt' else None)
            entry['returncode'] = p.returncode
            streams = p.stdout, p.stderr
        except subprocess.TimeoutExpired as error:
            entry['timeout'] = True
            streams = error.stdout or b'', error.stderr or b''
        except OSError as error:
            entry['unavailable'] = str(error)
            streams = b'', str(error).encode()
        for stream, data in zip(('stdout','stderr'), streams):
            (output / f'{name}.{stream}').write_bytes(data)
        entry['external_temporaries']=[]
        if os.name!='nt':
            for token in set(re.findall(rb'/var/tmp/genotmp:\d+(?:\.(?:ped|bed|fam|pedind))?',streams[0])):
                candidate=Path(os.fsdecode(token))
                if candidate not in before and candidate.is_file():
                    entry['external_temporaries'].append(dict(path=str(candidate),sha256=sha(candidate),bytes=candidate.stat().st_size))
                    candidate.unlink()
        for filename in ('result.out', 'roundtrip.tgeno'):
            if (work / filename).is_file():
                entry['files'][filename] = sha(work / filename)
        entry['temporaries'] = sorted(p.name for p in (work / 'tmp').glob('*'))
        entry['inputs'] = {p.name:sha(p) for p in work.iterdir() if p.is_file()}
        manifest['cases'][name] = entry
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(name, entry.get('returncode', 'UNAVAILABLE/TIMEOUT'), flush=True)
        return entry

    invoke('prepare-packed', 'convertf', ['-p','par.convertf'], common)
    invoke('prepare-tgeno', 'transpose', ['output.geno','input.tgeno'], common)
    invoke('prepare-roundtrip', 'transpose', ['input.tgeno','roundtrip.geno'], common)
    manifest['packed_roundtrip_exact'] = ((common/'output.geno').is_file() and
        (common/'roundtrip.geno').is_file() and (common/'output.geno').read_bytes() == (common/'roundtrip.geno').read_bytes())
    invoke('prepare-binary-transpose', 'transpose', ['binary.tgeno','binary.normal'], common)
    invoke('prepare-binary-roundtrip', 'transpose', ['binary.normal','roundtrip.tgeno'], common)
    manifest['binary_roundtrip_exact'] = (common/'binary.tgeno').read_bytes() == (common/'roundtrip.tgeno').read_bytes()
    for kind, fmt in (('ped','PED'),('bed','PACKEDPED')):
        text = (common/'par.convertf').read_text().replace('PACKEDANCESTRYMAP',fmt)
        text = text.replace('output.geno',f'plink.{kind}').replace('output.snp',f'plink-{kind}.pedsnp').replace('output.ind',f'plink-{kind}.pedind')
        (common/f'par.{kind}').write_text(text+'outputgroup: YES\n')
        invoke('prepare-'+kind,'convertf',['-p',f'par.{kind}'],common)
    rows = (common/'input.geno').read_text().splitlines()
    people = (common/'input.ind').read_text().splitlines()
    (common/'input.ancestry').write_text(''.join(f'rs{s:05d} {person.split()[0]} {row[i]}\n'
        for s,row in enumerate(rows) for i,person in enumerate(people)))
    for filename in ('input.geno','output.geno','input.tgeno','input.ancestry','plink.ped','plink.bed'):
        data = (common/filename).read_bytes()
        (common/(filename+'.gz')).write_bytes(gzip.compress(data[:len(data)//2],mtime=0)+gzip.compress(data[len(data)//2:],mtime=0))
    base = (common/'par.qpDstat').read_text()
    modes = {
        'default':'', 'explicit-defaults':'f4mode: NO\nsizeweight: NO\nxmode: NO\n',
        'f4':'f4mode: YES\n', 'printsd':'printsd: YES\n', 'no-size':'printssize: NO\n',
        'sizeweight':'sizeweight: YES\n', 'inbreed':'inbreed: YES\n',
        'popsizelimit':'popsizelimit: 3\n', 'popsizelimit-repeat':'popsizelimit: 3\n',
        'popsizelimit-seed':'popsizelimit: 3\nseed: 123\n',
        'popsizelimit-zero':'popsizelimit: 3\nseed: 0\n',
        'popsizelimit-one':'popsizelimit: 3\nseed: 1\n',
        'popsizelimit-high':'popsizelimit: 3\nseed: -2147483648\n',
        'unlimited':'popsizelimit: 100\n', 'chrom':'chrom: 3\n', 'nochrom':'nochrom: 3\n',
        'numchrom':'numchrom: 21\n', 'numchrom-intmax':'numchrom: 2147483647\n',
        'xdata':'xdata: YES\n', 'noxdata-no':'noxdata: NO\n',
        'xmode':'chrom: 23\nxmode: YES\n', 'xmode-no':'chrom: 23\nxmode: NO\n',
        'xmode-all':'xdata: YES\nxmode: YES\n', 'gfromp':'gfromp: YES\n', 'physical-fallback':'',
        'blockfile':'blockname: blocks\n', 'blockfile-overflow':'blockname: blocks\n',
        'blockfile-intmax':'blockname: blocks\n', 'blockfile-partial':'blockname: blocks\n',
        'blockfile-negative':'blockname: blocks\n', 'blockfile-zero':'blockname: blocks\n',
        'blockfile-sparse':'blockname: blocks\n', 'blockfile-ignore':'blockname: blocks\n',
        'jack-unweighted':'jackweight: NO\n', 'jackquart':'jackquart: .5\n',
        'fourier':'fourierjack: YES\n', 'fourier-five':'fourierjack: YES\nblockname: blocks\n',
        'fourier-constant':'fourierjack: YES\nblockname: blocks\n',
        'few-blocks':'chrom: 1\nblgsize: 1\n', 'few-blocks-ok':'chrom: 1\nblgsize: 1\nfewblocksok: YES\n',
        'tree-four':'dotree: YES\n', 'tree-five':'dotree: YES\n',
        'tree-haploid':'dotree: YES\nchrom: 23\nxmode: YES\ninbreed: YES\n',
        'enumerate':'', 'enumerate-no-best':'bbestmode: NO\n', 'enumerate-five':'',
        'banker':'bankermode: YES\n', 'banker-force':'bankermode: YES\nforceclade: YES\n',
        'banker-type3':'bankermode: YES\n', 'banker-many':'bankermode: YES\n',
        'duplicate-pops':'', 'duplicate-ind':'', 'duplicate-snp':'', 'unknown-pop':'',
        'poplist-capacity':'', 'quad-capacity':'', 'empty-quads':'', 'bad-quads':'',
        'extra-quad-column':'', 'repeat-quad':'', 'colon-quads':'', 'no-pop':'', 'both-pop':'poplistname: pops4\n',
        'empty-poplist':'', 'three-poplist':'', 'line-low':'locount: 2\n', 'line-high':'hicount: 1\n',
        'line-cli':'', 'line-precedence':'locount: 2\n', 'line-reversed':'locount: 2\nhicount: 1\n',
        'zero-blocksize':'blgsize: 0\n', 'negative-blocksize':'blgsize: -1\n', 'nan-blocksize':'blgsize: nan\n',
        'infinite-blocksize':'blgsize: inf\n', 'negative-limit':'popsizelimit: -2\n',
        'output':'output: result.out\n', 'outputname':'outputname: result.out\n',
        'instem':'', 'id2pops':'id2pops: idpops\n', 'badsnp':'badsnpname: badsnps\n',
        'no-valid-snps':'chrom: 99\n', 'missing-geno':'', 'missing-par':'', 'empty-ind':'', 'empty-snp':'',
        'missing-data':'', 'all-missing':'', 'constant':'', 'zero-stat':'',
        'truncated-text':'', 'truncated-packed':'', 'truncated-tgeno':'', 'bad-genotype':'',
        'bom':'', 'crlf-macro':'', 'utf16':'', 'embedded-nul':'', 'space-unicode':'', 'forward-paths':'',
        'verbose':'', 'coredump-no':'coredump: NO\n',
    }
    for key,value in {'colcalc':'NO','fullmode':'YES','forceclade':'YES','nostatslim':'100000',
            'msjackname':'unused.jack','msjackweight':'NO','inbreed':'YES'}.items():
        modes['control-'+key] = key+': '+value+'\n'
    for fmt in ('text','packed','tgeno','ancestry','ped','bed'):
        modes['format-'+fmt] = ''
        modes['gzip-'+fmt] = ''
    for kind in ('corrupt','truncated','crc','length','empty','onebyte','reader-fatal'):
        modes['gzip-'+kind] = ''
    for kind in ('d','f4','weighted','missing','permutations','zero'):
        modes['oracle-'+kind] = 'blockname: blocks\nprintsd: YES\n'+('f4mode: YES\n' if kind=='f4' else '')+('sizeweight: YES\n' if kind in ('weighted','missing') else '')
    if probe:
        modes.update({'manual-subset-77':'','manual-subset-123':''})
    reject = {'numchrom-intmax','banker-type3','banker-many','poplist-capacity','quad-capacity',
        'bad-quads','duplicate-ind','duplicate-snp','unknown-pop','duplicate-pops','no-pop',
        'zero-blocksize','negative-blocksize','nan-blocksize','infinite-blocksize',
        'missing-geno','missing-par','empty-ind','empty-snp','no-valid-snps','all-missing',
        'truncated-text','truncated-packed','truncated-tgeno','bad-genotype',
        'blockfile-overflow','blockfile-intmax','blockfile-partial'}
    reject.update('gzip-'+k for k in ('corrupt','truncated','crc','length','empty','onebyte','reader-fatal'))
    reject.update(('output','outputname','banker-force','tree-haploid','empty-poplist','three-poplist'))
    reject.add('fourier-constant')
    reject.update('control-'+k for k in ('colcalc','fullmode','forceclade','nostatslim','msjackname','msjackweight'))
    for name, extra in modes.items():
        if not re.search(selection,name):
            continue
        work = output/name
        work.mkdir()
        needed={'input.geno','input.snp','input.ind','quads'}
        if name.startswith(('format-','gzip-','truncated-packed','truncated-tgeno')):
            kind=name.split('-',1)[1]
            filename={'text':'input.geno','packed':'output.geno','tgeno':'input.tgeno',
                'ancestry':'input.ancestry','ped':'plink.ped','bed':'plink.bed'}.get(kind,'input.geno')
            needed.add(filename+'.gz' if name.startswith('gzip-') else filename)
            if kind in ('ped','bed'):needed.update({f'plink-{kind}.pedsnp',f'plink-{kind}.pedind'})
        for filename in needed:shutil.copyfile(common/filename,work/filename)
        (work/'tmp').mkdir()
        (work/'pops4').write_text('Out\nA\nB\nX\n')
        (work/'result.out').unlink(missing_ok=True)
        text = base
        for key in re.findall(r'(?m)^([^:#\s]+):',extra):
            text=re.sub(r'(?m)^'+re.escape(key)+r':.*\n','',text)
        text, args = text+extra, ['-p','par']
        if name.startswith(('enumerate','banker')) or name in ('duplicate-pops','empty-poplist','three-poplist','poplist-capacity'):
            text = text.replace('popfilename: quads','poplistname: pops4')
            if name=='enumerate-five': (work/'pops4').write_text('Out\nA\nB\nX\nC\n')
            if name=='duplicate-pops': (work/'pops4').write_text('Out\nA\nA\nX\n')
            if name=='empty-poplist': (work/'pops4').write_text('')
            if name=='three-poplist': (work/'pops4').write_text('Out\nA\nX\n')
            if name=='poplist-capacity': (work/'pops4').write_text(''.join(f'unknown{i}\n' for i in range(60)))
            if name.startswith('banker'):
                (work/'pops4').write_text('Out 2\nA 2\nB 1\nX 0\n')
                if name=='banker-type3': (work/'pops4').write_text('Out 3\nA 2\nB 1\nX 0\n')
                if name=='banker-many':
                    (work/'input.ind').write_text(''.join(f'I{i} U P{i}\n' for i in range(101)))
                    (work/'input.snp').write_text(''.join((work/'input.snp').read_text().splitlines(True)[:5]))
                    (work/'input.geno').write_text(('02'*50+'0\n')*5)
                    # No legal quartet: reach the fixed-array boundary without
                    # emitting millions of result lines in a non-sanitized run.
                    (work/'pops4').write_text(''.join(f'P{i} 0\n' for i in range(101)))
                    text+='fewblocksok: YES\nbbestmode: NO\n'
        if name.startswith('tree'):
            (work/'quads').write_text('Out A B X\n'+('Out C A X\n' if name=='tree-five' else ''))
            if name=='tree-haploid':
                indices=[0,6,12,24]
                (work/'input.ind').write_bytes(''.join(people[i].replace(' U ',' M ')+'\n' for i in indices).encode())
                (work/'input.geno').write_bytes(''.join(''.join('2' if row[i]=='1' else row[i] for i in indices)+'\n' for row in rows).encode())
                (work/'input.snp').write_text((work/'input.snp').read_text().replace(' 22 ',' 23 '),newline='\n')
        if name=='quad-capacity': (work/'quads').write_text(''.join(f'U{i} V{i} W{i} Z{i}\n' for i in range(15)))
        quad_changes={'empty-quads':'','bad-quads':'Out A B\n', 'extra-quad-column':'Out A B X ignored\n',
            'repeat-quad':'Out A A X\n','colon-quads':'Out A : B X\n','unknown-pop':'Out Absent B X\n'}
        if name in quad_changes: (work/'quads').write_text(quad_changes[name])
        if name=='no-pop': text=text.replace('popfilename: quads\n','')
        if name=='line-cli': args+=['-L','2','-H','2']
        if name=='line-precedence': args+=['-L','1','-H','1']
        if name=='verbose': args+=['-V']
        if name=='instem': text=re.sub(r'(?m)^(genotypename|indivname|snpname):.*\n','',text)+'instem: input\n'
        if name=='badsnp': (work/'badsnps').write_text('rs00000\nrs00200\n')
        if name=='id2pops': (work/'idpops').write_text(''.join(f'{s.split()[0]} {s.split()[2]}\n' for s in people))
        if name.startswith('xmode') or name in ('xdata','noxdata-no'):
            (work/'input.snp').write_text((work/'input.snp').read_text().replace(' 22 ',' 23 '))
            (work/'input.ind').write_text(''.join(s.replace(' U ', ' M ' if i%2 else ' F ')+'\n' for i,s in enumerate(people)))
        if name=='physical-fallback': (work/'input.snp').write_text(''.join(' '.join(s.split()[:2]+['0']+s.split()[3:])+'\n' for s in (work/'input.snp').read_text().splitlines()))
        if name in ('duplicate-ind','duplicate-snp','empty-ind','empty-snp'):
            path=work/('input.ind' if name.endswith('ind') else 'input.snp')
            lines=path.read_text().splitlines()
            path.write_text('' if name.startswith('empty') else '\n'.join([lines[0],lines[0],*lines[2:]])+'\n')
        if name in ('missing-data','oracle-missing'):
            (work/'input.geno').write_text(''.join(''.join('9' if (s*7+i)%11==0 else v for i,v in enumerate(row))+'\n' for s,row in enumerate(rows)))
        if name in ('all-missing','constant','zero-stat'):
            (work/'input.geno').write_text(((('9' if name=='all-missing' else '0' if name=='constant' else '1')*54)+'\n')*2200)
        if name.startswith(('blockfile','oracle-','fourier-five','fourier-constant')):
            label=lambda s: str(s//100+1)
            if name=='blockfile-overflow': label=lambda s:'2221'
            if name=='blockfile-intmax': label=lambda s:'2147483647'
            if name=='blockfile-partial': label=lambda s:'1oops'
            if name=='blockfile-zero': label=lambda s:'0'
            if name=='blockfile-negative': label=lambda s:'-1'
            if name=='blockfile-ignore': label=lambda s:str(-1 if s%3==0 else s//100+1)
            if name=='blockfile-sparse': label=lambda s:str((s//100)*50+1)
            if name in ('fourier-five','fourier-constant'): label=lambda s:str(s//440+1)
            (work/'blocks').write_text(''.join(f'rs{s:05d} {label(s)}\n' for s in range(2200)))
        if name=='fourier-constant': (work/'input.geno').write_text(('002211'*9+'\n')*2200)
        if name.startswith('oracle-'):
            if name=='oracle-zero':
                pops=[p.split()[2] for p in people]
                (work/'input.geno').write_bytes(''.join(''.join(
                    ('0' if (s//100)%2==0 else '2') if p=='Out' else
                    ('2' if (s//100)%2==0 else '0') if p=='A' else
                    '0' if p=='B' else '2' for p in pops)+'\n' for s in range(2200)).encode())
            quads=[['Out','A','B','X']]
            if name=='oracle-permutations': quads=list(itertools.permutations(quads[0]))
            (work/'quads').write_text(''.join(' '.join(q)+'\n' for q in quads))
            manifest['oracles'][name]=oracle(work,quads,name=='oracle-f4',name in ('oracle-weighted','oracle-missing'))
        if name.startswith('manual-subset'):
            (work/'analysis-pops').write_text('Out\nA\nB\nX\nC\n')
            p=subprocess.run([str(probe),'sample','input.ind','analysis-pops','3',name.rsplit('-',1)[1]],cwd=work,env=env,capture_output=True,check=True)
            indices=[int(s) for s in p.stdout.splitlines() if s.isdigit()]
            if len(indices)!=15: raise RuntimeError('subset probe did not select 15 people')
            (work/'input.ind').write_text(''.join(people[i]+'\n' for i in indices))
            (work/'input.geno').write_text(''.join(''.join(row[i] for i in indices)+'\n' for row in rows))
        if name.startswith(('format-','gzip-','truncated-packed','truncated-tgeno')):
            kind=name.split('-',1)[1]
            filename={'text':'input.geno','packed':'output.geno','tgeno':'input.tgeno','ancestry':'input.ancestry','ped':'plink.ped','bed':'plink.bed'}.get(kind,'input.geno')
            if name.startswith('gzip-'): filename+='.gz'
            text=text.replace('genotypename: input.geno','genotypename: '+filename)
            if kind in ('ped','bed'): text=text.replace('input.ind',f'plink-{kind}.pedind').replace('input.snp',f'plink-{kind}.pedsnp')
            if name.startswith('truncated-'): (work/filename).write_bytes((work/filename).read_bytes()[:100])
            if name=='gzip-corrupt': (work/filename).write_bytes(b'bad gzip')
            if name=='gzip-truncated': (work/filename).write_bytes((work/filename).read_bytes()[:-9])
            if name=='gzip-empty': (work/filename).write_bytes(b'')
            if name=='gzip-onebyte': (work/filename).write_bytes(b'x')
            if name in ('gzip-crc','gzip-length'):
                data=bytearray(gzip.compress((work/'input.geno').read_bytes(),mtime=0)); data[-8 if name=='gzip-crc' else -4]^=1
                (work/filename).write_bytes(data)
            if name=='gzip-reader-fatal': (work/filename).write_bytes(gzip.compress(b'invalid genotypes\n',mtime=0))
        if name=='missing-geno': (work/'input.geno').unlink()
        if name=='truncated-text': (work/'input.geno').write_text('\n'.join(rows[:20])+'\n')
        if name=='bad-genotype': (work/'input.geno').write_text('x'+(work/'input.geno').read_text()[1:])
        if name in ('output','outputname'): (work/'result.out').write_bytes(b'preserve existing output\n')
        if name in ('space-unicode','forward-paths'):
            directory=work/('space # \u03b1' if name=='space-unicode' else 'paths')
            directory.mkdir()
            for f in ('input.geno','input.snp','input.ind','quads'):
                shutil.copyfile(work/f,directory/f)
                path=str(directory/f)
                if name=='forward-paths': path=path.replace('\\','/')
                if os.name=='nt': path='"'+path+'"'
                text=re.sub(r'(?m)(: )'+re.escape(f)+r'$',lambda m:m[1]+path,text)
        if name=='missing-par': args=['-p','absent']
        if name=='bom': (work/'par').write_bytes(b'\xef\xbb\xbf'+text.encode())
        elif name=='crlf-macro':
            text='DIR: .\n'+text.replace('genotypename: input.geno','genotypename: DIR/input.geno')
            (work/'par').write_bytes(text.replace('\n','\r\n').encode())
        elif name=='utf16': (work/'par').write_bytes(text.encode('utf-16'))
        elif name=='embedded-nul': (work/'par').write_bytes(text.encode()+b'x:\0bad\n')
        else: (work/'par').write_text(text,encoding='utf-8',newline='\n')
        expected='failure' if name in reject else 'observe' if name in ('few-blocks','blockfile-zero','blockfile-negative','empty-poplist','three-poplist','constant','zero-stat','utf16','embedded-nul') else 'success'
        invoke(name,'qpDstat',args,work,expected)
    for name,args,expected in [('help',['-h'],'success'),('version',['-v'],'success'),
            ('no-args',[],'failure'),('invalid-option',['-z'],'failure'),('missing-value',['-p'],'failure')]:
        if re.search(selection,'cli-'+name): invoke('cli-'+name,'qpDstat',args,common,expected)
    manifest['completed']=True
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


def verify(directory):
    m=json.loads((directory/'manifest.json').read_text()); failures=[]
    if not m['completed']: failures.append('incomplete matrix')
    for name,c in m['cases'].items():
        code=c.get('returncode'); expected=c['expected']
        if m['platform']!='win32' and name in ('space-unicode','bom'): expected='failure'
        if code is None or (expected!='observe' and (code!=0)!=(expected=='failure')): failures.append(name+': exit')
        err=(directory/f'{name}.stderr').read_bytes()
        if b'AddressSanitizer' in err or b'runtime error:' in err: failures.append(name+': sanitizer')
        if code is not None and ((code < 0 and code != -6) or
                (code >= 0x80000000 and code not in (3221226505,4294967295))):
            failures.append(name+': unexpected signal or system exception')
        if c['temporaries']: failures.append(name+': temporary retained')
        if c.get('external_temporaries'):failures.append(name+': Unix generated temporary retained by tool (runner cleaned its new file)')
        if name in ('output','outputname') and c['files'].get('result.out')!=hashlib.sha256(b'preserve existing output\n').hexdigest(): failures.append(name+': silently truncated result file')
        if code==0 and not name.startswith(('cli-','prepare-')):
            if expected=='success' and name not in ('empty-quads','line-reversed','line-precedence','repeat-quad'):
                raw=(directory/f'{name}.stdout').read_bytes()
                if not result_rows(directory,name) or b'##end of qpDstat:' not in raw:failures.append(name+': missing completed scientific output')
            if re.search(r'(?i)(?<![a-z])(nan|[+-]?inf)(?![a-z])',str(result_rows(directory,name))): failures.append(name+': nonfinite result')
        if name=='cli-version':
            out=(directory/f'{name}.stdout').read_bytes().strip()
            if err or out!=(b'version: 1160.w' if m['platform']=='win32' else b'version: 1160'): failures.append(name+': version-only contract')
    for name,expected in m['oracles'].items():
        if result_rows(directory,name)!=expected: failures.append(name+': independent oracle differs')
    for a,b in [('default','explicit-defaults'),('default','instem'),('default','unlimited'),
            ('default','id2pops'),('default','format-text'),('default','format-packed'),('default','format-tgeno'),
            ('default','format-ancestry'),('popsizelimit','manual-subset-77'),('popsizelimit-seed','manual-subset-123'),
            ('popsizelimit','popsizelimit-repeat'),('popsizelimit-zero','popsizelimit-one')]:
        if a in m['cases'] and b in m['cases'] and result_rows(directory,a)!=result_rows(directory,b): failures.append(a+'/'+b+': results differ')
    for a,b in [('default','popsizelimit'),('popsizelimit','popsizelimit-seed')]:
        if a in m['cases'] and b in m['cases'] and result_rows(directory,a)==result_rows(directory,b): failures.append(a+'/'+b+': limit or seed ineffective')
    if not m['packed_roundtrip_exact'] or not m['binary_roundtrip_exact']: failures.append('binary roundtrip')
    (directory/'verification.json').write_text(json.dumps(dict(failures=failures),indent=2)+'\n')
    print(json.dumps(failures,indent=2)); return bool(failures)


def compare(left,right):
    manifests=[json.loads((p/'manifest.json').read_text()) for p in (left,right)]
    results={}; diffs=[]
    for name in sorted(manifests[0]['cases'].keys()|manifests[1]['cases'].keys()):
        if not all(name in m['cases'] for m in manifests): results[name]=['not selected on both sides']; continue
        a,b=[m['cases'][name] for m in manifests]; errors=[]
        if a.get('returncode')!=b.get('returncode'): errors.append('exit')
        if a.get('returncode') is None or b.get('returncode') is None: errors.append('unavailable/timeout')
        for stream in ('stdout','stderr'):
            raw=[(p/f'{name}.{stream}').read_bytes() for p in (left,right)]
            if name=='M01-rng' and stream=='stdout':
                if raw[0]!=raw[1]:errors.append('binary RNG bytes')
                continue
            x,y=[normal(data) for data in raw]
            if x!=y:
                errors.append(stream)
                diffs.extend(difflib.unified_diff(x.splitlines(True),y.splitlines(True),fromfile=f'left/{name}.{stream}',tofile=f'right/{name}.{stream}'))
        if a['files']!=b['files']: errors.append('generated files')
        results[name]=errors or 'exact'
    (right/('comparison-'+left.name+'.json')).write_text(json.dumps(results,indent=2)+'\n')
    (right/('comparison-'+left.name+'.diff')).write_text(''.join(diffs),encoding='utf-8',errors='surrogateescape')
    print(json.dumps({k:v for k,v in results.items() if v!='exact'},indent=2))
    return any(v!='exact' for v in results.values())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bin',type=Path); p.add_argument('--output',type=Path)
    p.add_argument('--select',default='.'); p.add_argument('--probe',type=Path)
    p.add_argument('--verify',type=Path); p.add_argument('--compare',nargs=2,type=Path)
    a=p.parse_args()
    if a.verify: sys.exit(verify(a.verify.resolve()))
    if a.compare: sys.exit(compare(*[d.resolve() for d in a.compare]))
    if not a.bin or not a.output: p.error('use --bin DIR --output NEW_DIR, --verify DIR, or --compare DIR DIR')
    run(a.bin.resolve(),a.output.resolve(),a.select,a.probe.resolve() if a.probe else None)
