"""Retain native statuses and streams from bounded T06 production-function probes."""
import argparse
from fractions import Fraction
import json
import os
from pathlib import Path
import subprocess
from audit_qpdstat import no_core, sha


def run(binary, output):
    output.mkdir(parents=True,exist_ok=False)
    if os.name=='nt':
        import ctypes
        ctypes.windll.kernel32.SetErrorMode(3)
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',LC_ALL='C',
             ASAN_OPTIONS='detect_leaks=1:abort_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    m=dict(executable_sha256=sha(binary),cases={},failures=[])
    a,b=Fraction(3,12),Fraction(7,12)
    expected=('ordinary 1 '+f'{float((a-b)*(Fraction(4,12)-Fraction(9,12))):.12f}'+'\n'
              'overlap 1 '+f'{float((a-b)**2-(a*(1-a)+b*(1-b))/11):.12f}'+'\n'
              'NULL 2 1.000000000000\nnegative 2 1.000000000000\n'
              'fancy-zero 1 0.000000000000\nstrict-missing -1 0.000000000000\n'
              'large-overlap 1 '+f'{float(-Fraction(1,2)/(2*2147483647-1)):.12f}'+'\n'
              'one-overlap -1 0.000000000000\n'
              'one-nonoverlap 1 '+f'{float((a-1)*(a-Fraction(4,12))-a*(1-a)/11):.12f}'+'\n'
              'one-second-overlap -1 0.000000000000\n')
    for name in ('f4-boundaries','count-selection','ratio-lifetime','block-upper','block-negative','zero-rows',
                 'diff-zero-denominator','diff-zero-se','banker-large','banker-index','banker-type'):
        p=subprocess.run([str(binary),name],cwd=output,env=env,capture_output=True,timeout=20,
                         preexec_fn=no_core if os.name!='nt' else None)
        for s,data in zip(('stdout','stderr'),(p.stdout,p.stderr)):(output/f'{name}.{s}').write_bytes(data)
        out=p.stdout.decode().replace('\r\n','\n');good=(p.returncode==0 and not p.stderr)
        if name=='f4-boundaries':good=good and out==expected
        elif name=='count-selection':good=good and out=='raw indexed counts 2 2\nploidy-aware indexed counts 2 1\nautosomal indexed counts 2 2\n'
        elif name=='ratio-lifetime':good=good and out.endswith('16 ratio/diff workspace lifetimes: finite\n')
        elif name=='banker-large':good=good and out=='101-population legacy helper: bounded\n'
        else:good=p.returncode!=0 and b'fatalx:' in p.stderr and b'Sanitizer' not in p.stderr and b'runtime error:' not in p.stderr
        m['cases'][name]=dict(returncode=p.returncode,passed=good,streams={s:sha(output/f'{name}.{s}') for s in ('stdout','stderr')})
        if not good:m['failures'].append(name)
    m['f4_independent_fraction_oracle']=expected
    (output/'results.json').write_text(json.dumps(m,indent=2)+'\n')
    print(output,m['failures'],flush=True)
    return bool(m['failures'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binary',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(run(a.binary.resolve(),a.output.resolve()))
