"""Fail closed on implementation/binary leakage in the Git-index allowlist."""
from pathlib import Path
import json,re,subprocess,sys
root=Path(__file__).resolve().parents[1]
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
denied_suffix={'.so','.pyd','.dll','.dylib','.a','.lib','.exe','.o','.obj','.pyc','.zip','.gz','.7z'}
patterns=[r'\bdmmhm_state\b',r'\bdmmhm_advance_\w+',r'\bdmmhm_batch_avx\w*',
          r'\bM0[789]\b',r'[A-Za-z]:[/\\]Users[/\\]',r'/mnt/[a-z]/Users/',
          r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',r'gh[pousr]_[A-Za-z0-9]{20,}']
failures=[];checked=0
for name in tracked:
    if not name:continue
    p=root/name;checked+=1
    if name.split('/')[0] in ('oracle', 'spec', 'baselines') or p.name == 'oracle.py':
        failures.append({'file':name,'reason':'implementation or specification path'});continue
    if p.suffix.lower() in denied_suffix or '.so.' in p.name:
        failures.append({'file':name,'reason':'binary or archive'});continue
    if p.name in ('dmmhm.h','dmmhm.hpp','dmmhm.py','numpy_matcher.py'):
        failures.append({'file':name,'reason':'private implementation filename'});continue
    try:text=p.read_text(encoding='utf-8')
    except (UnicodeError,OSError):failures.append({'file':name,'reason':'non-text file'});continue
    if p.resolve()==Path(__file__).resolve():continue
    if re.search(r'(class\s+Oracle\b|def\s+(match_monotone|find_nearest)\b|\bstd::(min_element|lower_bound)\b)',text):
        failures.append({'file':name,'reason':'matching implementation construct'})
    for pattern in patterns:
        if re.search(pattern,text):failures.append({'file':name,'reason':'prohibited pattern','pattern':pattern})
print(json.dumps({'status':'PASS' if not failures else 'FAIL','files_checked':checked,'failures':failures},indent=2))
sys.exit(bool(failures))
