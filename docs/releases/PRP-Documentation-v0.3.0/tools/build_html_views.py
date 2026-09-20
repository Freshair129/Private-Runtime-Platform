#!/usr/bin/env python3
"""Rebuild reading HTML views from authored Markdown/catalog. Not application code.
Requires markdown-it-py and beautifulsoup4. DOCX/PDF exports are separate artifacts.
"""
from pathlib import Path
import json,re,html,os,sys,copy
from markdown_it import MarkdownIt
from bs4 import BeautifulSoup, NavigableString, Tag
ROOT=Path(__file__).resolve().parents[1]
MD=MarkdownIt('commonmark',{'html':True}).enable('table')
ORDER=['docs/PRD-PRP.md','docs/SRS-PRP.md','docs/ROADMAP-PRP.md','docs/ARCH-PRP.md','docs/API-PRP.md','docs/STACK-EVALUATION-PRP.md','standards/Coding-Standards.md','docs/SECURITY-DATA-PRP.md','docs/OPS-PRP.md','docs/ADR-PRP.md','docs/TEST-PRP.md','docs/TRACEABILITY-PRP.md','docs/BASELINE-CHANGES-PRP.md','docs/CHANGELOG-PRP.md','docs/SOURCES-PRP.md']

def body_md(path):
 s=path.read_text(encoding='utf-8')
 return re.sub(r'^---\n.*?\n---\n','',s,count=1,flags=re.S)

def title_of(path):
 s=body_md(path);return re.search(r'^# (.+)$',s,re.M).group(1)

def render_md(path):return MD.render(body_md(path))

CSS='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f3f6f8;color:#183449;font:16px/1.75 "Noto Sans Thai","Noto Sans",Tahoma,Arial,sans-serif}a{color:#12677b}header{background:#17364b;color:white;padding:42px max(26px,calc((100vw - 1150px)/2))}header h1{font:700 40px/1.1 Arial,sans-serif;letter-spacing:-1px;margin:10px 0}header p{max-width:920px;color:#d7e6ee;margin:14px 0}header a{color:#c0e9ef}main{max-width:1200px;margin:auto;padding:26px}.toolbar{position:sticky;top:0;z-index:10;background:#fff;padding:15px 24px;border-bottom:1px solid #d1dee5;display:flex;gap:12px;flex-wrap:wrap;align-items:center}.toolbar input{min-width:240px;flex:1}.toolbar input,.toolbar select,button{font:inherit;border:1px solid #b9cbd4;border-radius:8px;padding:8px 13px;background:white;color:#183449}button{cursor:pointer}button:hover{background:#e4f0f4}.document,.card,.intro{background:white;border:1px solid #dbe5eb;border-radius:12px;padding:30px;margin:0 0 24px}h1,h2,h3,h4{line-height:1.35;scroll-margin-top:95px}h1{font-size:30px}h2{font-size:23px;border-bottom:1px solid #dde7ed;padding-bottom:9px;margin-top:36px}h3{font-size:19px;margin-top:27px}h4{font-size:17px}table{width:100%;border-collapse:collapse;font-size:14px;display:block;overflow:auto;margin:18px 0}td,th{border:1px solid #dbe5eb;padding:10px;min-width:90px;vertical-align:top}th{background:#eaf2f6;text-align:left}pre{padding:20px;background:#f2f6f8;border:1px solid #d5e1e7;border-radius:8px;overflow:auto;line-height:1.5}code{font-family:Consolas,"Liberation Mono",monospace;font-size:.9em}p{margin:12px 0}nav{columns:2;column-gap:30px}nav a{display:block;break-inside:avoid;padding:5px 0}small,.muted{color:#607581}.pill{display:inline-block;border-radius:30px;background:#e7f3f0;padding:5px 13px;color:#176c60;font-size:13px}.svgwrap{border:1px solid #d9e5eb;border-radius:7px;overflow:auto;margin:18px 0;background:white}.svgwrap svg{width:100%;height:auto;display:block;max-height:800px}.card h2{margin:0;border:0}.actions{display:flex;gap:12px;flex-wrap:wrap}.doclinks{font-size:13px}.noresults{text-align:center;padding:35px}.hidden{display:none!important}dialog{width:95vw;height:94vh;max-width:none;max-height:none;border:1px solid #cadbe4;border-radius:12px;padding:18px}dialog::backdrop{background:#10202abd}.modalbar{display:flex;gap:10px;align-items:center;position:sticky;top:0;background:white;z-index:2}.modalbody{height:calc(100% - 75px);overflow:auto;margin-top:20px;border:1px solid #d2e1e8}.modalbody svg{display:block;width:100%;height:auto}.note{border-left:4px solid #18758b;padding:10px 18px;background:#edf6f8}@media(max-width:700px){nav{columns:1}main{padding:12px}.document,.card{padding:18px}header h1{font-size:32px}h1{font-size:25px}}@media print{.toolbar,.actions{display:none}body{background:white}header{background:white;color:#183449;padding:20px}header p{color:#183449}.document,.card{break-before:page;border:0;margin:0;padding:15px}table{display:table}nav{columns:1}}'''

def build_docs():
 idmap={(ROOT/rel).resolve():Path(rel).stem if 'standards/' not in rel else 'CODING-STANDARDS-PRP' for rel in ORDER}
 parts=[];nav=[]
 for rel in ORDER:
  path=ROOT/rel;id=idmap[path.resolve()];title=title_of(path);soup=BeautifulSoup(render_md(path),'html.parser')
  for a in soup.find_all('a',href=True):
   href=a['href']
   if re.match(r'^[A-Za-z]+:',href):continue
   filepart,_,anchor=href.partition('#');dest=(path.parent/filepart).resolve() if filepart else path.resolve()
   if dest in idmap:a['href']='#'+(anchor or idmap[dest])
   else:
    a['href']=os.path.relpath(dest,ROOT).replace(os.sep,'/')+('#'+anchor if anchor else '')
  for img in soup.find_all('img',src=True):img['src']=os.path.relpath((path.parent/img['src']).resolve(),ROOT).replace(os.sep,'/')
  # Replace bare source URLs with clickable references, without changing authored text.
  for txt in list(soup.find_all(string=True)):
   if isinstance(txt,NavigableString) and txt.parent.name not in {'a','code','pre','script'} and re.search(r'https?://',str(txt)):
    frag=re.sub(r'(https?://[^\s<]+)',lambda m:'<a href="'+html.escape(m.group(1),quote=True)+'" target="_blank" rel="noreferrer">'+html.escape(m.group(1))+'</a>',html.escape(str(txt)))
    txt.replace_with(BeautifulSoup(frag,'html.parser'))
  parts.append(f'<section class="document" id="{id}"><p class="doclinks">Canonical Markdown: <a href="{rel}">{rel}</a></p>{soup}</section>')
  nav.append(f'<a href="#{id}">{html.escape(title)}</a>')
 head='''<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PRP Documentation v0.3.0</title><style>'''+CSS+'''</style></head><body><header><span class="pill">v0.3.0 · Python-first / Reuse-before-build</span><h1>PRP — Private Runtime Platform</h1><p>ชุดเอกสารฉบับแก้ไข: PRD · SRS · Roadmap · Architecture · Python Standards · Runtime Evaluation<br>Independent platform. Chat &amp; Voice first. Framework selection and runtime qualification remain open.</p><a href="PRP-Diagram-Atlas.html">Diagram Atlas · 34 views</a> · <a href="README.md">Package README</a></header><div class="toolbar"><label for="docsearch">กรองเอกสาร</label><input id="docsearch" placeholder="Python, SRS, key, cancellation …"><button id="clearsearch">ล้าง</button><span id="doccount"></span></div><main><div class="intro"><h2>สารบัญ</h2><nav>'''+''.join(nav)+'''</nav><p class="note">SRS เป็นแหล่งข้อกำหนดหลัก ภาพและ HTML เป็นมุมมองอ่าน ไม่ใช่ผลทดสอบ runtime ทุก AT ยังคง NOT_RUN; เอกสารนี้ไม่ได้เลือก framework หรือ deploy ระบบจริง</p></div>'''
 script='''<script>const docs=[...document.querySelectorAll('.document')],q=document.querySelector('#docsearch'),count=document.querySelector('#doccount');function filter(){let n=0;for(const d of docs){const yes=d.textContent.toLowerCase().includes(q.value.toLowerCase());d.classList.toggle('hidden',!yes);if(yes)n++}count.textContent=n+' / '+docs.length+' documents'}q.addEventListener('input',filter);document.querySelector('#clearsearch').onclick=()=>{q.value='';filter()};window.addEventListener('hashchange',()=>{q.value='';filter();const el=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(el)el.scrollIntoView()});filter();</script>'''
 (ROOT/'PRP-Documentation.html').write_text(head+''.join(parts)+'</main>'+script+'</body></html>',encoding='utf-8')

def build_atlas():
 cat=json.loads((ROOT/'diagrams/catalog.json').read_text());cards=[]
 for d in cat:
  d['svg']=(ROOT/f'diagrams/svg/{d["id"]}.svg').read_text();d['svg']=re.sub(r'<\?xml.*?\?>|<!DOCTYPE.*?\]>|<!DOCTYPE[^>]+>','',d['svg'],flags=re.S)
  id=d['id'];cards.append(f'''<article class="card" id="{id}" data-type="{html.escape(d['type'],quote=True)}"><span class="pill">{id} · {html.escape(d['type'])}</span><h2>{html.escape(d['title'])}</h2><p>{html.escape(d['description'])}</p><p class="muted">{html.escape(d['requirements'])}</p><div class="svgwrap">{d['svg']}</div><p class="muted">{html.escape(d.get('notes',''))}</p><div class="actions"><button data-open="{id}">ขยายภาพ</button><button data-download="{id}">บันทึก SVG</button><a href="{d['source']}">Editable source</a><a href="diagrams/png/{id}.png">PNG</a></div></article>''')
 types=sorted({d['type'] for d in cat});opts=''.join(f'<option value="{html.escape(t,quote=True)}">{html.escape(t)}</option>' for t in types)
 dat=json.dumps(cat,ensure_ascii=False).replace('</','<\\/')
 page='''<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PRP Diagram Atlas v0.3.0</title><style>'''+CSS+'''</style></head><body><header><span class="pill">34 views · v0.3.0</span><h1>PRP Diagram Atlas</h1><p>Python-first architecture, reuse decision, model processes, authority binding และ flow เดิมครบ<br>ทุกภาพเป็นแบบออกแบบ ไม่ใช่หลักฐานว่าระบบติดตั้งหรือทดสอบแล้ว</p><a href="PRP-Documentation.html">เอกสารรวม</a> · <a href="PRP-Diagram-Atlas.pdf">Atlas PDF</a></header><div class="toolbar"><input id="search" aria-label="ค้นหาแผนภาพ" placeholder="ค้นหา D32, Python, PRP-NFR, voice …"><select id="type"><option value="">ทุกประเภท</option>'''+opts+'''</select><button id="reset">ล้าง</button><span id="count"></span></div><main>'''+''.join(cards)+'''<p class="noresults hidden" id="none">ไม่พบแผนภาพที่ตรงคำค้น</p></main><dialog id="viewer"><div class="modalbar"><strong id="vtitle"></strong><button id="zoomout">−</button><button id="zoomin">+</button><button id="fit">พอดี</button><button id="close">ปิด</button></div><div class="modalbody" id="vbody"></div></dialog><script id="diagram-data" type="application/json">'''+dat+'''</script><script>
const data=JSON.parse(document.getElementById('diagram-data').textContent),map=new Map(data.map(d=>[d.id,d])),cards=[...document.querySelectorAll('.card')],q=document.querySelector('#search'),type=document.querySelector('#type'),dlg=document.querySelector('#viewer'),vb=document.querySelector('#vbody');let zoom=100;
function filter(){let n=0;for(const c of cards){const yes=(!type.value||type.value===c.dataset.type)&&c.textContent.toLowerCase().includes(q.value.toLowerCase());c.classList.toggle('hidden',!yes);n+=yes}document.querySelector('#count').textContent=n+' / '+cards.length;document.querySelector('#none').classList.toggle('hidden',n!==0)}
q.oninput=filter;type.onchange=filter;document.querySelector('#reset').onclick=()=>{q.value='';type.value='';filter()};document.querySelectorAll('[data-open]').forEach(b=>b.onclick=()=>{const d=map.get(b.dataset.open);vb.innerHTML=d.svg;document.querySelector('#vtitle').textContent=d.id+' · '+d.title;zoom=100;dlg.showModal()});function setzoom(z){zoom=Math.max(35,Math.min(400,z));vb.querySelector('svg').style.width=zoom+'%';vb.querySelector('svg').style.maxWidth='none'}document.querySelector('#zoomin').onclick=()=>setzoom(zoom+25);document.querySelector('#zoomout').onclick=()=>setzoom(zoom-25);document.querySelector('#fit').onclick=()=>setzoom(100);document.querySelector('#close').onclick=()=>dlg.close();document.querySelectorAll('[data-download]').forEach(b=>b.onclick=()=>{const d=map.get(b.dataset.download),url=URL.createObjectURL(new Blob([d.svg],{type:'image/svg+xml'})),a=document.createElement('a');a.href=url;a.download='PRP-'+d.id+'.svg';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});filter();</script></body></html>'''
 (ROOT/'PRP-Diagram-Atlas.html').write_text(page,encoding='utf-8')


if __name__=='__main__':
 build_docs();build_atlas();print('Rebuilt PRP documentation and diagram HTML views')
