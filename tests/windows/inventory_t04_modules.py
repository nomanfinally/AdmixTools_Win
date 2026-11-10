"""Compiler-derived function/header inventory and warning evidence for T04.

Reference/call matches are navigation aids, not proof of runtime reachability.
No function is marked audited merely because it compiles or appears here.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]
IDS=[f'M{i:02d}' for i in (*range(1,15),17,18,19,20)]


def run(tree,output,toolchain=None):
    output.mkdir(parents=True,exist_ok=False)
    entries=json.loads((ROOT/'tests/windows/audit_inventory.json').read_text())['entries']
    modules=[e for e in entries if e['id'] in IDS]
    compiler=str(toolchain/'gcc.exe') if os.name=='nt' else '/usr/bin/gcc'
    env=dict(os.environ)
    if toolchain:env['PATH']=str(toolchain)+os.pathsep+env.get('PATH','')
    flags=['-std=gnu11','-Isrc','-Isrc/nicksrc','-fsyntax-only','-Wall','-Wextra','-Wformat=2','-Wconversion']
    if os.name=='nt':flags+=['-include','src/win32/compat.h','-D_FILE_OFFSET_BITS=64','-D__USE_MINGW_ANSI_STDIO=1']
    result=dict(modules={},commands=[],platform=os.name,compiler=subprocess.check_output([compiler,'--version'],text=True).splitlines()[0])
    sources={str(p.relative_to(tree)).replace('\\','/'):p.read_text(errors='replace')
             for p in (tree/'src').rglob('*.c') if '.windows' not in p.parts}
    headers={e['paths'][0]:e['id'] for e in entries if e['category']=='header_contract'}
    for module in modules:
        mid=module['id'];source=module['paths'][0];path=tree/source
        aux=output/(mid+'.aux');warnings=output/(mid+'.warnings.txt')
        command=[compiler,*flags,'-aux-info',str(aux),source]
        with warnings.open('w') as log:p=subprocess.run(command,cwd=tree,env=env,stdout=log,stderr=subprocess.STDOUT)
        result['commands'].append(command)
        text=path.read_text();functions=[]
        for line in aux.read_text(errors='replace').splitlines() if aux.exists() else []:
            match=re.match(r'/\* (.+?):(\d+):[NO]F \*/ (.+?);',line)
            if not match or match[1].replace('\\','/')!=source:continue
            name=re.search(r'([A-Za-z_]\w*)\s*\(',match[3])
            if name:functions.append(dict(name=name[1],line=int(match[2]),declaration=match[3]))
        lines=text.splitlines()
        for i,function in enumerate(functions):
            end=functions[i+1]['line']-1 if i+1<len(functions) else len(lines)
            body='\n'.join(lines[function['line']-1:end])
            function['call_candidates']=sorted(set(re.findall(r'\b([A-Za-z_]\w*)\s*\(',body))-{'if','for','while','switch','sizeof','return',function['name']})
            function['reference_candidates']=[p for p,t in sources.items() if p!=source and re.search(r'\b'+re.escape(function['name'])+r'\s*\(',t)]
            function['contract_status']='not certified by inventory; see module report and runtime evidence'
        header_paths=set();pending=[path]
        visited=set()
        while pending:
            current=pending.pop()
            if current in visited:continue
            visited.add(current)
            for name in re.findall(r'^\s*#\s*include\s*[<\"]([^>\"]+)[>\"]',current.read_text(errors='replace'),re.M):
                found=next((p for p in (current.parent/name,tree/'src'/name,tree/'src/nicksrc'/name) if p.is_file()),None)
                if found:
                    rel=str(found.relative_to(tree)).replace('\\','/');header_paths.add(rel);pending.append(found)
        result['modules'][mid]=dict(source=source,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            functions=functions,line_count=len(lines),header_contracts={p:headers.get(p) for p in sorted(header_paths)},
            native_link_input_tools=module.get('native_link_input_tools',[]),compile_status=p.returncode,
            warning_count=warnings.read_text(errors='replace').count('warning:'),
            platform_directives=[dict(line=i+1,text=s.strip()) for i,s in enumerate(lines) if re.match(r'\s*#\s*(if|else|elif|endif)',s)])
    (output/'inventory.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:dict(functions=len(v['functions']),warnings=v['warning_count'],compile=v['compile_status']) for k,v in result['modules'].items()},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tree',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--toolchain',type=Path)
    a=p.parse_args();run(a.tree.resolve(),a.output.resolve(),a.toolchain.resolve() if a.toolchain else None)
