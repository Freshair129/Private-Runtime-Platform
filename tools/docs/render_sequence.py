#!/usr/bin/env python3
"""Render a PRP sequence JSON as SVG and Mermaid. CairoSVG enables optional PNG.
Example: python tools/render_sequence.py diagrams/source/D07.sequence.json --out /tmp/prp-preview
Outputs go to a new directory; the package is not modified unless chosen explicitly.
"""
from pathlib import Path
import json,html,textwrap,argparse
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();DI=a.out
for sub in ['svg','png','source']:(DI/sub).mkdir(parents=True,exist_ok=True)
def seq(id,title,desc,refs,actors,events,notes=''):
 # events: (from_id,to_id,label,style); NOTE full-width, return dashed
 w=max(1120, len(actors)*220); x0=105; gap=(w-210)/(len(actors)-1)
 xs={a[0]:x0+i*gap for i,a in enumerate(actors)}
 processed=[]; y=118
 for a,b,label,style in events:
  wrap=105 if a=='NOTE' else max(25,int(abs(xs[b]-xs[a])/7.7))
  lines=textwrap.wrap(label,width=min(wrap,105))
  h=max(57,len(lines)*18+25)
  processed.append((a,b,lines,style,y,h));y+=h
 H=y+70
 out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{H}" viewBox="0 0 {w} {H}"><defs><marker id="arr" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#405C70"/></marker></defs><rect width="100%" height="100%" fill="white"/>']
 for aid,label in actors:
  x=xs[aid]
  out.append(f'<rect x="{x-91}" y="18" width="182" height="58" rx="8" fill="#E9F3F8" stroke="#536779"/><line x1="{x}" y1="76" x2="{x}" y2="{H-28}" stroke="#97AAB8" stroke-dasharray="6 5"/>')
  for j,line in enumerate(label.split('\n')):
   out.append(f'<text x="{x}" y="{42+j*19}" text-anchor="middle" font-family="DejaVu Sans" font-size="15" fill="#17364A">{html.escape(line)}</text>')
 for a,b,lines,style,yy,hh in processed:
  if a=='NOTE':
   out.append(f'<rect x="16" y="{yy-19}" width="{w-32}" height="{hh-8}" rx="5" fill="#FFF4DB" stroke="#D3B56A"/>')
   for j,line in enumerate(lines):out.append(f'<text x="32" y="{yy+j*18}" font-family="DejaVu Sans" font-size="14" fill="#614D20">{html.escape(line)}</text>')
  else:
   x1,x2=xs[a],xs[b];dash='stroke-dasharray="7 4"' if style=='return' else ''
   ly=yy+len(lines)*18-7
   out.append(f'<line x1="{x1}" y1="{ly}" x2="{x2}" y2="{ly}" stroke="#405C70" stroke-width="1.4" {dash} marker-end="url(#arr)"/>')
   for j,line in enumerate(lines):
    out.append(f'<text x="{(x1+x2)/2}" y="{yy+j*18-13}" text-anchor="middle" font-family="DejaVu Sans" font-size="14" fill="#17364A">{html.escape(line)}</text>')
 out.append('</svg>')
 svg=''.join(out);(DI/'svg'/f'{id}.svg').write_text(svg)
 try:
  import cairosvg
  cairosvg.svg2png(bytestring=svg.encode(),write_to=str(DI/'png'/f'{id}.png'))
 except ImportError:
  print('CairoSVG not installed; SVG and Mermaid are still generated')
 dat={'actors':actors,'events':events}; (DI/'source'/f'{id}.sequence.json').write_text(json.dumps(dat,indent=2))
 m='sequenceDiagram\n'
 for a,label in actors:m+=f'    participant {a} as {label.replace(chr(10)," ")}\n'
 for a,b,label,style in events:
  if a=='NOTE':m+=f'    Note over {actors[0][0]},{actors[-1][0]}: {label}\n'
  else:m+=f'    {a}{"-->>" if style=="return" else "->>"}{b}: {label}\n'
 (DI/'source'/f'{id}.mmd').write_text(m)
 print(f'Rendered {id}: SVG, PNG and Mermaid')

data=json.loads(a.source.read_text(encoding='utf-8'))
seq(a.source.name.split('.')[0],'','','',data['actors'],data['events'])
