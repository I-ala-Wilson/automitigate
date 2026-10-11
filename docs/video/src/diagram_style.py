import os, math, random
OUT = os.path.dirname(os.path.abspath(__file__))

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1600px;height:1000px;background:#fff;color:#000;font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;overflow:hidden}
body{padding:40px 48px}
h1{font-size:30px;font-weight:700;letter-spacing:-.2px}
h1 span{font-weight:700}
.sub{font-size:17px;color:#000;margin-top:6px}
.tag{display:inline-block;font-size:13px;font-weight:700;padding:3px 9px;border:1px solid #000;color:#000;margin-left:10px;vertical-align:middle}
.card{background:#fff;border:1px solid #000;border-radius:3px;padding:16px 18px}
.card h3{font-size:17px;margin-bottom:6px;font-weight:700}
.card p{font-size:15px;line-height:1.38;color:#000}
.mono{font-family:"SF Mono",Menlo,Consolas,monospace}
.chip{display:inline-block;font-family:"SF Mono",Menlo,monospace;font-size:13px;background:#f2f2f2;border:1px solid #000;border-radius:2px;padding:4px 8px;color:#000;margin-top:8px;white-space:pre}
.num{display:inline-flex;width:26px;height:26px;border-radius:50%;background:#000;color:#fff;font-weight:700;font-size:14px;align-items:center;justify-content:center;margin-right:8px}
.cy,.am,.gr,.pk,.pu{color:#000;font-weight:700}
table{border-collapse:collapse;width:100%}
th,td{border:1px solid #000;padding:6px 9px;font-size:14px;text-align:left;vertical-align:top;color:#000}
th{background:#e6e6e6;font-weight:700}
.foot{position:absolute;left:48px;bottom:22px;font-size:13px;color:#000}
.on{font-weight:700}.off{font-weight:400}
"""

def page(title, body, sub="", n=""):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<h1>{title}{f'<span class="tag">{n}</span>' if n else ''}</h1>{f'<div class="sub">{sub}</div>' if sub else ''}
{body}</body></html>"""

def arrow(x1,y1,x2,y2,color="#000",curve=0,w=2):
    mx,my=(x1+x2)/2,(y1+y2)/2
    if curve: d=f"M{x1},{y1} Q{mx},{my+curve} {x2},{y2}"
    else: d=f"M{x1},{y1} L{x2},{y2}"
    return f'<path d="{d}" stroke="{color}" stroke-width="{w}" fill="none" marker-end="url(#ah)"/>'

MARK='<defs><marker id="ah" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#000"/></marker></defs>'
