#!/usr/bin/env python3
"""Validate the living documentation tree (docs/) and contracts/, not a running PRP implementation.
Uses only the Python standard library. Run from any working directory.
Frozen packages under docs/releases/ are skipped; each carries its own validator copy and MANIFEST.
"""
from pathlib import Path
from collections import Counter
import json,re,sys,xml.etree.ElementTree as ET
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[2]/'docs'
REPO=ROOT.parent
errors=[]
def check(condition,message):
    if not condition: errors.append(message)
def read_json(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
requirements=read_json('registry/requirements.json')['requirements']
ids=[r['id'] for r in requirements]
check(len(ids)==len(set(ids)),'Duplicate requirement ID')
counts=Counter(re.match(r'PRP-([A-Z0-9]+)-',i).group(1) for i in ids)
check(counts=={'FR':56,'NFR':24,'SEC':12},f'Unexpected requirement counts: {counts}')
phase2=read_json('registry/requirements.json')['phase2_envelope']
check(len(phase2)==8 and len({r['id'] for r in phase2})==8,'Expected 8 Phase2 envelopes')
srs=(ROOT/'SRS-PRP.md').read_text(encoding='utf-8')
tests=(ROOT/'TEST-PRP.md').read_text(encoding='utf-8')
cat=read_json('diagrams/catalog.json');diagramids={d['id'] for d in cat}
for r in requirements:
    check(f'id="{r["id"]}"' in srs,f'Missing SRS anchor {r["id"]}')
    check(r['statement'] in srs,f'Derived registry drift {r["id"]}')
    check(r['diagram'] in diagramids,f'Unknown primary diagram for {r["id"]}')
    if r.get('test'):
        check(f'id="{r["test"]}"' in tests,f'Missing test {r["test"]}')
check(len(set(re.findall(r'<a id="(PRP-AT-\d+)"',tests)))==92,'Expected 92 acceptance anchors')
check(len(cat)==34 and len(diagramids)==34,'Expected 34 unique diagrams')
for d in cat:
    check((ROOT/d['source']).exists(),f'Missing source {d["id"]}')
    for ext in ['svg','png']:check((ROOT/f'diagrams/{ext}/{d["id"]}.{ext}').exists(),f'Missing {ext} {d["id"]}')
    try:ET.parse(ROOT/f'diagrams/svg/{d["id"]}.svg')
    except ET.ParseError as e:errors.append(f'Invalid SVG {d["id"]}: {e}')
# Validate explicit Markdown links and explicit anchors; ignore external links and fenced examples.
links=0
for p in ROOT.rglob('*.md'):
    if 'releases' in p.relative_to(ROOT).parts:continue
    text=re.sub(r'```.*?```','',p.read_text(encoding='utf-8'),flags=re.S)
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',text):
        if re.match(r'^[a-zA-Z]+:',target):continue
        target=unquote(target);filepart,sep,anchor=target.partition('#');dest=(p.parent/filepart).resolve() if filepart else p
        links+=1;check(dest.exists(),f'Broken link {p.relative_to(ROOT)} -> {target}')
        if sep and anchor and dest.exists() and dest.suffix=='.md':
            body=dest.read_text(encoding='utf-8');check(f'id="{anchor}"' in body or f"id='{anchor}'" in body,f'Broken explicit anchor {p.name} -> {target}')
roadmap=read_json('registry/roadmap.json')['work_packages'];wpids={w['id'] for w in roadmap}
check(len(roadmap)==25,'Expected 25 work packages')
adjacency={w['id']:re.findall(r'WP\d+',w['dependencies']) for w in roadmap}
for w,deps in adjacency.items():
    for dep in deps:check(dep in wpids,f'Unknown dependency {w} -> {dep}')
def walk(node,stack,done):
    if node in stack:errors.append('Roadmap dependency cycle: '+' -> '.join(stack+[node]));return
    if node in done:return
    for dep in adjacency.get(node,[]):walk(dep,stack+[node],done)
    done.add(node)
done=set()
for w in wpids:walk(w,[],done)
# Every OpenAPI export under contracts/openapi (YAML is canonical; tools/contracts/export_json.py --check enforces equality).
OPENAPI=REPO/'contracts/openapi';METHODS=['get','post','put','delete','patch','options','head']
yaml_docs={p.stem for p in OPENAPI.glob('*.yaml')};json_docs={p.stem for p in OPENAPI.glob('*.json')}
check(yaml_docs==json_docs and yaml_docs,f'OpenAPI YAML/JSON pairs mismatch: {sorted(yaml_docs^json_docs)}')
refs=[];specs={}
def scan(o,found):
    if isinstance(o,dict):
        if '$ref' in o:found.append(o['$ref'])
        for v in o.values():scan(v,found)
    elif isinstance(o,list):
        for v in o:scan(v,found)
for p in sorted(OPENAPI.glob('*.json')):
    spec=json.loads(p.read_text(encoding='utf-8'));specs[p.stem]=spec;found=[];scan(spec,found);refs+=found
    check(isinstance(spec.get('info',{}).get('version'),str),f'{p.name}: info.version missing')
    for ref in found:
        check(ref.startswith('#/'),f'{p.name}: unexpected external OpenAPI ref {ref}')
        if ref.startswith('#/'):
            obj=spec
            try:
                for key in ref[2:].split('/'):obj=obj[key.replace('~1','/').replace('~0','~')]
            except (KeyError,TypeError):errors.append(f'{p.name}: broken OpenAPI ref {ref}')
    ops=[o for item in spec['paths'].values() for method,o in item.items() if method in METHODS]
    check(len({o['operationId'] for o in ops})==len(ops),f'{p.name}: duplicate operationId')
    check(bool(spec.get('security')),f'{p.name}: auth not declared')
    for o in ops:check(o.get('security',spec.get('security'))!=[],f'{p.name}: unauthenticated operation {o.get("operationId")}')
    if p.stem!='prp-client':check(isinstance(spec.get('x-prp-status'),str),f'{p.name}: x-prp-status missing (DRAFT until freeze gate)')
spec=specs.get('prp-client',{'paths':{}})
ops=[o for item in spec['paths'].values() for method,o in item.items() if method in METHODS]
check(len(spec['paths'])==12 and len(ops)==14,'Unexpected client contract inventory')
# Verify one test per requirement and no reused acceptance anchors.
test_anchors=re.findall(r'<a id="(PRP-AT-\d+)"',tests)
check(len(test_anchors)==len(set(test_anchors))==92,'Repeated or missing test anchors')
check(set(test_anchors)=={r['test'] for r in requirements},'Requirement/test mapping mismatch')
trace=(ROOT/'TRACEABILITY-PRP.md').read_text(encoding='utf-8')
for r in requirements:
    check(r['id'] in trace and r['test'] in trace,f'Missing trace row {r["id"]}')
fitgap=read_json('registry/reuse-fit-gap-template.json')['rows']
check({r['requirement_id'] for r in fitgap}==set(ids) and len(fitgap)==92,'Fit-gap template coverage mismatch')
check(all(r['runtime_test_status']=='NOT_RUN' and r['disposition']=='UNASSESSED' for r in fitgap),'Template contains invented evidence')
# Acceptance status gate (SDD-PRP-REPO 9 item 4; ADR-PRP-012 action 5): leaving NOT_RUN needs a collected test and a complete receipt.
trace_path=ROOT/'registry/code-trace.json'
check(trace_path.exists(),'Missing registry/code-trace.json (run: python tools/trace/collect_trace.py)')
trace=read_json('registry/code-trace.json') if trace_path.exists() else {'acceptance':{},'projects':{},'errors':['missing']}
check(not trace.get('errors'),f'code-trace.json reports marker errors: {trace.get("errors")}')
receipts={}
for p in sorted((ROOT/'evidence').glob('*.json')):
    r=json.loads(p.read_text(encoding='utf-8'))
    check(isinstance(r.get('test_id'),str) and r.get('status') in {'PASS','FAIL','BLOCKED'},f'Evidence {p.name}: test_id/status invalid (a NOT_RUN receipt is not evidence)')
    receipts.setdefault(r.get('test_id'),[]).append(r)
statuses=dict(re.findall(r'<a id="(PRP-AT-\d+)"></a>.*?\*\*Status:\*\* ([A-Z_]+)',tests,flags=re.S))
check(len(statuses)==92,'Could not parse the status of every acceptance case')
proof_by_test={r['test']:str(r.get('proof','')) for r in requirements}
MOCK_OK={'contract','packaging','portability','design evidence','operations review','load mock'}
status_counts=Counter(statuses.values())
for at,status in statuses.items():
    check(status in {'NOT_RUN','PASS','FAIL','BLOCKED'},f'{at}: unknown status {status}')
    if status=='NOT_RUN':continue
    complete=[r for r in receipts.get(at,[]) if r.get('status')==status and r.get('evidence_id') and r.get('commit') and r.get('reviewer')]
    check(bool(complete),f'{at}: status {status} without a complete evidence receipt (evidence_id, commit, reviewer) in docs/evidence/')
    entry=trace.get('acceptance',{}).get(at) or {}
    check(bool(entry.get('tests')),f'{at}: status {status} without a collected test in registry/code-trace.json')
    components={c.strip().lower() for c in proof_by_test.get(at,'').replace('+',',').split(',') if c.strip()}
    if status=='PASS' and not components<=MOCK_OK:
        check(bool({'integration','hardware'}&set(entry.get('tiers',[]))),f'{at}: proof "{proof_by_test.get(at)}" cannot PASS from unit/contract tests alone')
roadtext=(ROOT/'ROADMAP-PRP.md').read_text(encoding='utf-8')
for w in roadmap:
    check(w['deliverable'] in roadtext,f'Roadmap deliverable drift {w["id"]}')
check('WP24' in adjacency['WP03'],'Selection does not depend on reuse evaluation')
check('WP25' in adjacency['WP04'],'Control implementation does not depend on Python baseline')
check(all(w.get('status','NOT_STARTED')=='NOT_STARTED' for w in roadmap),'Unverified implementation completion')
trace_diagram=(ROOT/'diagrams/source/D26.dot').read_text(encoding='utf-8')
check('WP01-WP25' in trace_diagram and 'AT001-AT092' in trace_diagram,'Trace diagram cardinality drift')
for p in ROOT.rglob('*'):
    if 'releases' in p.relative_to(ROOT).parts:continue
    if p.is_file():
        check(p.suffix.lower() not in {'.ttf','.otf','.woff','.woff2'},'Font file must not be distributed: '+str(p))
result={'kind':'DOCUMENT_STRUCTURE_ONLY','requirements':dict(counts),'phase2_envelopes':len(phase2),'acceptance_cases':92,'acceptance_status':dict(status_counts),'evidence_receipts':sum(len(v) for v in receipts.values()),'code_trace_tests':sum(int(p.get('tests_collected',0)) for p in trace.get('projects',{}).values()),'diagram_views':len(cat),'work_packages':len(roadmap),'relative_links_checked':links,'openapi_local_refs_checked':len(refs),'openapi_documents':len(specs),'openapi_paths':len(spec['paths']),'openapi_operations':len(ops),'errors':errors,'runtime_test_status':'NOT_RUN' if status_counts.get('NOT_RUN')==92 else 'PARTIAL'}
print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(1 if errors else 0)
