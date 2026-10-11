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

# ---------- 1. the loop ----------
def img1():
    nodes_top=[("1","Your circuit","GHZ-4, QFT-3, Grover-3,<br>or one you paste","QuantumCircuit  (4 qubits, 4 gates)"),
               ("2","Mirror twin","circuit, barrier, a random Pauli layer, then the<br>gates undone with the frame corrected.<br>Right answer is one known bitstring","QuantumCircuit  (8 gates + measure)"),
               ("3","Arm recipe","the learner's chosen arm turns<br>the twin into 1 / 3 / 8 / 24<br>circuits (ZNE folds, twirls)","list of 24 circuits, 50 shots each"),
               ("4","Simulator with that day's noise","Qiskit Aer, loaded with the IonQ-like<br>model or one ibm_fez calibration day;<br>runs them all as one job","24 count dicts")]
    nodes_bot=[("7","Learner picks next arm","updates its tally for that arm,<br>then chooses again","int, the next arm id, e.g. 2"),
               ("6","Score","fraction of the target bitstring,<br>readout-corrected if REM is on,<br>averaged over twirls,<br>extrapolated to zero noise","float, 0.99"),
               ("5","Counts","{\"0000\": 46, \"0001\": 2,<br>\"1000\": 1, \"0011\": 1}","dict per circuit")]
    def card(n,t,p,chip,x,y,w=330,h=215,col="#000"):
        return f'<div class="card" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;border-color:{col}"><h3><span class="num" style="background:{col}">{n}</span>{t}</h3><p>{p}</p><div class="chip">{chip}</div></div>'
    html='<div style="position:relative;width:1504px;height:840px;margin-top:18px">'
    xs=[0,380,760,1140]
    for i,(n,t,p,c) in enumerate(nodes_top): html+=card(n,t,p,c,xs[i],40)
    xb=[0,380,760]
    cols=["#000","#000","#000"]
    for i,(n,t,p,c) in enumerate(nodes_bot): html+=card(n,t,p,c,xb[i],470,col=cols[i])
    svg=f'<svg style="position:absolute;left:0;top:0" width="1504" height="840">{MARK}'
    for i in range(3): svg+=arrow(xs[i]+332,147,xs[i+1]-6,147)
    svg+=arrow(1305,257,1305,310)+f'<path d="M1305,312 L1305,400 Q1305,420 1285,420 L1110,420 Q1090,420 1090,440 L1090,470" stroke="#000" stroke-width="2" fill="none" marker-end="url(#ah)"/>'
    for i in range(2): svg+=arrow(xb[i+1]-6,577,xb[i]+332,577)
    svg+=f'<path d="M165,470 L165,420 Q165,400 185,400 L905,400 Q925,400 925,380 L925,260" stroke="#000" stroke-width="2" stroke-dasharray="8 5" fill="none" marker-end="url(#ah)"/>'
    svg+='<text x="420" y="390" fill="#000" font-size="15" font-weight="700">next pull, the chosen arm goes back to step 3</text>'
    svg+='</svg>'
    html+=svg
    html+='<div class="card" style="position:absolute;left:1140px;top:470px;width:364px;height:215px;border-color:#000;background:#f2f2f2"><h3 class="pu">One pull is steps 3 to 7</h3><p>Repeated ~200 times per run. The learner never sees the circuit, the counts, or the noise. It only ever receives pairs like <span class="mono gr">(arm 5, 0.99)</span>. That blindness is why it works on any circuit.</p></div>'
    html+='</div><div class="foot">AutoMitigate · Qollab + IonQ hackathon, Oct 9–11 2026 · diagram 1 of 14</div>'
    return page("What goes in and what comes out",html,"One pull of the bandit and the shape of the data at every step")

# ---------- 2. eight arms ----------
def img2():
    arms=[(1,0,0,0,1,"Nothing on. The baseline, and the 'do nothing' fixed policy."),
          (2,0,0,1,"1 + 2","Readout mitigation alone. Same circuit; counts corrected with 2 calibration circuits shared by every arm that day."),
          (3,0,1,0,8,"Twirling alone. 8 random Pauli-dressed copies, averaged. Helps only against coherent errors."),
          (4,0,1,1,"8 + 2","Twirling, then readout correction on the averaged counts."),
          (5,1,0,0,3,"ZNE alone. Run at 1×, 3×, 5× noise, extrapolate to 0×."),
          (6,1,0,1,"3 + 2","ZNE on readout-corrected counts."),
          (7,1,1,0,24,"ZNE and twirling, the common pairing. 8 copies × 3 scales."),
          (8,1,1,1,"24 + 2","Everything on. The practitioner's default, and the 'do everything' fixed policy.")]
    def sketch(z,t,m):
        # mini circuit sketch: rows of bars
        n = (3 if z else 1)*(8 if t else 1)
        rows=min(n,8); L=70
        s='<svg width="290" height="70">'
        for r in range(rows):
            y=6+r*8
            s+=f'<rect x="0" y="{y}" width="{L}" height="5" rx="2" fill="{"#555" if t else "#000"}"/>'
            if z:
                s+=f'<rect x="{L+6}" y="{y}" width="{L}" height="5" rx="2" fill="#999"/><rect x="{2*L+12}" y="{y}" width="{L}" height="5" rx="2" fill="#ccc"/>'
        if m:
            s+='<rect x="250" y="6" width="30" height="5" rx="2" fill="none" stroke="#000"/><rect x="250" y="16" width="30" height="5" rx="2" fill="none" stroke="#000"/>'
        s+='</svg>'
        return s
    html='<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:18px">'
    for a,z,t,m,c,desc in arms:
        html+=f'''<div class="card" style="height:300px"><h3><span class="num">{a}</span>Arm {a} <span class="mono" style="font-size:13px;float:right;margin-top:6px">{c} circuits / pull</span></h3>
<table style="margin:8px 0"><tr><td>ZNE</td><td class="{'on' if z else 'off'}">{'● on' if z else '○ off'}</td></tr><tr><td>Pauli twirling</td><td class="{'on' if t else 'off'}">{'● on' if t else '○ off'}</td></tr><tr><td>Readout mitigation</td><td class="{'on' if m else 'off'}">{'● on' if m else '○ off'}</td></tr></table>
<p>{desc}</p><div style="margin-top:8px">{sketch(z,t,m)}</div></div>'''
    html+='</div>'
    html+='''<div style="display:flex;gap:16px;margin-top:16px">
<div class="card" style="flex:1"><h3 class="am">Bars are the circuits actually sent to the simulator</h3><p><span style="color:#000">■</span> plain copy &nbsp; <span style="color:#555">■</span> twirled copy &nbsp; <span style="color:#999">■</span> 3× folded &nbsp; <span style="color:#ccc">■</span> 5× folded. Two outlined bars are the readout-calibration circuits (all-zeros and all-ones), run once per day and shared by every readout-mitigation arm.</p></div>
<div class="card" style="flex:1"><h3 class="gr">Same shot budget for every arm</h3><p>1,200 shots per pull, split across the arm's circuits. Arm 8 gets 50 shots per circuit; arm 1 gets 1,200. Heavy arms pay in precision. The bandit discovers whether that trade is worth it.</p></div>
<div class="card" style="flex:1"><h3 class="pu">An arm never looks at anything</h3><p>It is a fixed recipe applied to the mirror twin. The only thing that decides is the learner, and the only thing it decides is which recipe to run next.</p></div></div>
<div class="foot">8 arms is ZNE {off,on} × twirling {off,on} × readout mitigation {off,on}: one axis per noise source (incoherent gate error, coherent error, readout error), each of which drifts on its own in the calibration data. Transpile level is fixed at 1. · diagram 2 of 14</div>'''
    return page("The eight arms",html,"Each arm is a combination of three on/off tricks. Pick one and the mirror twin becomes this many circuits.")

# ---------- 3. one pull ----------
def img3():
    tbl_before="".join(f"<tr><td>{a}</td><td>{n}</td><td>{m:.2f}</td></tr>" for a,n,m in [(1,12,.74),(2,11,.78),(3,13,.88),(4,12,.86),(5,12,.81),(6,11,.83),(7,40,.91),(8,14,.90)])
    tbl_after=tbl_before.replace("<td>7</td><td>40</td><td>0.91</td>",'<td style="background:#e6e6e6"><b>7</b></td><td style="background:#e6e6e6"><b>41</b></td><td style="background:#e6e6e6"><b>0.912</b></td>')
    # extrapolation svg
    pts=[(1,.92),(3,.78),(5,.62)]
    def X(s): return 50+s*62
    def Y(p): return 150-(p-.5)*220
    svg='<svg width="470" height="170"><line x1="40" y1="150" x2="380" y2="150" stroke="#000"/><line x1="40" y1="10" x2="40" y2="150" stroke="#000"/>'
    svg+=f'<line x1="{X(0)}" y1="{Y(.99)}" x2="{X(5)}" y2="{Y(.62)}" stroke="#000" stroke-width="1.5" stroke-dasharray="6 4"/>'
    for s,p in pts: svg+=f'<circle cx="{X(s)}" cy="{Y(p)}" r="6" fill="#000"/><text x="{X(s)+10}" y="{Y(p)-12}" fill="#000" font-size="13">{s}× {p:.2f}</text>'
    svg+=f'<circle cx="{X(0)}" cy="{Y(.99)}" r="7" fill="#fff" stroke="#000" stroke-width="2"/><text x="{X(0)+14}" y="{Y(.99)-12}" fill="#000" font-size="15" font-weight="700">0× → 0.99</text>'
    svg+='<text x="300" y="166" fill="#000" font-size="12">noise scale</text></svg>'
    html=f'''<div style="display:grid;grid-template-columns:300px 1fr 1fr;gap:16px;margin-top:16px;height:820px">
<div class="card"><h3><span class="num">1</span>Learner's tally</h3><p>All it knows is times pulled and average score per arm.</p>
<table style="margin-top:8px"><tr><th>arm</th><th>n</th><th>mean</th></tr>{tbl_before}</table>
<p style="margin-top:10px">Thompson draws a random guess around each mean, picks the highest. <b class="gr">Picks arm 7.</b></p>
<div class="chip">returns 7</div></div>
<div style="display:flex;flex-direction:column;gap:16px">
<div class="card" style="flex:1"><h3><span class="num">2</span>Arm 7 runs its recipe on the mirror twin</h3><p>Input, the GHZ-4 randomised mirror twin (random Pauli layer in the middle, inverse half frame-corrected; net effect is a Pauli, so the ideal outcome is a known bitstring)</p>
<div class="chip">h q0; cx q0,q1; cx q1,q2; cx q2,q3;
barrier; x q1; z q3;              # random Pauli layer Q
cx q2,q3; cx q1,q2; cx q0,q1; h q0;   # frame-corrected inverse
measure all                      # target = 0100</div>
<p style="margin-top:8px">transpile once (opt 1) → twin → 8 twirled copies → fold each at 1×, 3×, 5× → drift kicks injected after each CZ → basis-translate at opt 0.</p>
<div class="chip">returns 24 circuits, 50 shots each</div></div>
<div class="card" style="flex:1"><h3><span class="num">3</span>Simulator returns counts</h3><p>Three of the 24, the same twirl copy at the three scales</p>
<div class="chip">1×  {{"0100": 46, "0101": 2, "1100": 1, "0111": 1}}
3×  {{"0100": 39, "0101": 4, "0010": 3, "1011": 2, "1100": 2}}
5×  {{"0100": 31, "0101": 6, "1000": 4, "1011": 5, "0110": 4}}</div>
<p style="margin-top:8px">More noise → fewer hits on the target bitstring. That slope is the whole information content.</p></div></div>
<div style="display:flex;flex-direction:column;gap:16px">
<div class="card" style="flex:1"><h3><span class="num">4</span>Score, 24 dicts become one number</h3><p>Fraction of the target "0100" per circuit → average the 8 twirl copies at each scale → fit a line → read it at 0× noise. (Readout-mitigation arms correct the counts first; the per-scale values are stored so an exponential fit can be run later.)</p>{svg}<div class="chip">returns 0.99</div></div>
<div class="card" style="flex:1"><h3><span class="num">5</span>Learner updates its tally</h3><p>Input is just the pair <span class="mono gr">(7, 0.99)</span>. Arm 7's row moves (Thompson flips a coin with p = 0.99 and adds the result to its Beta counts). Nothing else changes.</p>
<table style="margin-top:8px"><tr><th>arm</th><th>n</th><th>mean</th></tr>{tbl_after}</table>
<p style="margin-top:8px">Back to step 1. Two hundred times.</p></div></div></div>
<div class="foot">Numbers are illustrative but the shapes are exact. int → circuits → dicts → float → int. · diagram 3 of 14</div>'''
    return page("One pull with the real objects",html,"What each module actually receives and returns. Nothing is fed into an arm. The learner is the only decision maker. Arm 7 = ZNE + twirling.")

# ---------- 4. four learners ----------
def regret_curve(kind, w=330, h=150):
    random.seed(1)
    T=200; pts=[]; r=0
    for t in range(T):
        drift = t>=100
        if kind=="eps":   rate = 0.06 if t<30 else (0.025 if not drift else 0.09)
        if kind=="ucb":   rate = 0.08 if t<20 else (0.01 if not drift else (0.12 if t<170 else 0.09))
        if kind=="ts":    rate = 0.07 if t<20 else (0.008 if not drift else (0.11 if t<150 else 0.05))
        if kind=="dts":   rate = 0.07 if t<20 else (0.018 if not drift else (0.10 if t<118 else 0.02))
        r+=rate; pts.append(r)
    mx=18
    def X(t): return 10+t*(w-20)/T
    def Y(v): return h-10-v*(h-25)/mx
    s=f'<svg width="{w}" height="{h}"><rect x="{X(100)}" y="5" width="{X(200)-X(100)}" height="{h-15}" fill="#000" opacity="0.06"/>'
    s+=f'<line x1="{X(100)}" y1="5" x2="{X(100)}" y2="{h-10}" stroke="#000" stroke-width="1" stroke-dasharray="4 3"/>'
    s+=f'<text x="{X(100)+5}" y="18" fill="#000" font-size="12" font-weight="700">drift</text>'
    s+=f'<line x1="10" y1="{h-10}" x2="{w-10}" y2="{h-10}" stroke="#000"/><line x1="10" y1="5" x2="10" y2="{h-10}" stroke="#000"/>'
    poly=" ".join(f"{X(t):.1f},{Y(v):.1f}" for t,v in enumerate(pts))
    s+=f'<polyline points="{poly}" fill="none" stroke="#000" stroke-width="2.5"/>'
    s+=f'<text x="{w-70}" y="{h-14}" fill="#000" font-size="11">pulls →</text><text x="14" y="16" fill="#000" font-size="11">regret ↑</text></svg>'
    return s
DASH={"eps":"2 4","ucb":"10 6","ts":"14 5 3 5","dts":"none"}
def overlay_row():
    W,H=760,200; mx=18; T=200
    curves={}
    for k,rates in {"eps":(0.06,0.025,0.09),"ucb":(0.08,0.01,0.12),"ts":(0.07,0.008,0.11),"dts":(0.07,0.018,0.10)}.items():
        r=0;pts=[]
        for t in range(T):
            if t<25: rate=rates[0]
            elif t<100: rate=rates[1]
            else:
                if k=="dts": rate=rates[2] if t<118 else 0.02
                elif k=="ts": rate=rates[2] if t<150 else 0.05
                elif k=="ucb": rate=rates[2] if t<170 else 0.09
                else: rate=rates[2]
            r+=rate; pts.append(r)
        curves[k]=pts
    def X(t): return 40+t*(W-60)/T
    def Y(v): return H-24-v*(H-40)/mx
    dash=DASH
    svg=f'<svg width="{W}" height="{H}"><rect x="{X(100)}" y="8" width="{X(200)-X(100)}" height="{H-32}" fill="#000" opacity="0.06"/><line x1="{X(100)}" y1="8" x2="{X(100)}" y2="{H-24}" stroke="#000" stroke-width="1" stroke-dasharray="4 3"/><line x1="40" y1="{H-24}" x2="{W-20}" y2="{H-24}" stroke="#000"/><line x1="40" y1="8" x2="40" y2="{H-24}" stroke="#000"/>'
    for k,pts in curves.items():
        poly=" ".join(f"{X(t):.1f},{Y(v):.1f}" for t,v in enumerate(pts)); svg+=f'<polyline points="{poly}" fill="none" stroke="#000" stroke-width="{2.8 if k=="dts" else 1.8}" stroke-dasharray="{dash[k]}"/>'
    svg+=f'<text x="{X(100)+6}" y="24" fill="#000" font-size="13" font-weight="700">drift at pull 100</text><text x="{W-50}" y="{H-6}" fill="#000" font-size="12">pulls</text>'
    lx=50
    for k,nm in [("eps","ε-greedy"),("ucb","UCB1"),("ts","Thompson"),("dts","Discounted Thompson")]:
        svg+=f'<line x1="{lx}" y1="{H-12}" x2="{lx+30}" y2="{H-12}" stroke="#000" stroke-width="{2.8 if k=="dts" else 1.8}" stroke-dasharray="{dash[k]}"/><text x="{lx+36}" y="{H-8}" fill="#000" font-size="12">{nm}</text>'; lx+=60+len(nm)*7
    svg+='</svg>'
    return f'''<div style="display:grid;grid-template-columns:800px 1fr;gap:16px;margin-top:16px">
<div class="card"><h3>All four on one chart</h3>{svg}</div>
<div class="card"><h3 class="am">How to read it</h3><p style="margin-top:6px"><b>Before the drift line</b>, every curve bends flat. Each learner found arm 5 and is mostly pulling it. The three stationary ones flatten slightly faster because they commit harder.</p>
<p style="margin-top:8px"><b>At the drift line</b>, arm 5 stops being best. All four curves kink upward because they are still pulling it.</p>
<p style="margin-top:8px"><b>After the line</b>, only the <b>solid heavy</b> curve (Discounted Thompson) flattens again quickly. It forgot its old certainty and re-found the new best arm. The gap between it and the other three, measured in lost score, is the number the demo reports.</p></div></div>'''

def img4():
    L=[("ε-greedy","#000","eps","count n[a], mean m[a]","90% of the time the arm with the best mean, 10% of the time a random arm.","Blind coin flip, forever.","The baseline. Never stops wasting 10% of pulls, and after drift only rediscovers the new best arm by luck."),
       ("UCB1","#000","ucb","n[a], m[a], total pulls t","argmax of  m[a] + √(2·ln t / n[a]).  Rarely-pulled arms get a bonus.","Optimism about untried arms. Bonus shrinks as an arm is pulled.","Provably optimal when the world holds still. After drift it is the worst, so sure of the old arm that the bonus never lets it look again."),
       ("Thompson","#000","ts","Beta(α[a], β[a]) per arm, a belief curve","Draw one random guess per arm from its belief, pick the highest.","Randomness shrinks as evidence grows. No separate exploration rule.","Best stationary learner in practice, the one rival papers use. After drift, 20 new bad results barely move 200 old good ones. Stuck, just less rigidly."),
       ("Discounted Thompson","#000","dts","same Beta, but old evidence fades by γ each pull","Same draw-and-pick as Thompson.","Belief never fully narrows, so it keeps sampling other arms.","Built for drift. Pays a small regret tax before the change for never fully committing, then recovers fast. The γ slider in the UI sets memory. γ=1 is plain Thompson, γ=0.9 forgets in about 10 pulls.")]
    html='<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:16px">'
    for name,col,k,state,pick,explore,show in L:
        html+=f'''<div class="card" style="border-color:{col};height:540px"><h3 style="font-size:21px;border-bottom:2px solid #000;padding-bottom:6px">{name}</h3>
<p style="margin-top:8px"><b>Keeps</b> {state}</p>
<p style="margin-top:8px"><b>Picks</b> {pick}</p>
<p style="margin-top:8px"><b>Explores by</b> {explore}</p>
<div style="margin:14px 0 6px"><b>Cumulative regret (illustrative)</b></div>{regret_curve(k)}
<p style="margin-top:12px"><b>In the demo</b> {show}</p></div>'''
    html+='</div>'+overlay_row()+'<div class="foot">Regret is the score lost by not pulling the best arm, summed over pulls. A flat line means it found the best arm and is sticking to it. A kink upward at drift means it kept pulling an arm that stopped being best. · diagram 4 of 14</div>'
    return page("Four learners, four decision rules",html,"Three assume the world is fixed. One assumes it changes. The gap between them after drift is the result.")

# ---------- 5. drift ----------
def img5():
    def tbl(title,rows,score,col):
        r="".join(f"<tr><td class='mono'>{k}</td><td>{v}</td></tr>" for k,v in rows)
        return f'<div class="card" style="flex:1"><h3>{title}</h3><table style="margin-top:8px"><tr><th>string</th><th>shots</th></tr>{r}</table><p style="margin-top:10px;font-size:20px"><b>score {score}</b></p></div>'
    left=f'''<div style="display:flex;gap:14px">
{tbl("Mon 9 am, fresh calibration",[("0000",940),("0001",15),("1000",14),("0011",8),("1111",6),("other",17)],"0.94","#000")}
{tbl("Mon 9 pm, lab warmed up",[("0000",870),("0001",30),("1000",28),("0011",22),("1111",25),("other",25)],"0.87","#000")}
{tbl("Tue 9 am, recalibrated",[("0000",945),("0001",14),("1000",13),("0011",7),("1111",6),("other",15)],"0.945","#000")}</div>
<div class="card" style="margin-top:14px"><h3>Same circuit, same code, 1,000 shots each time</h3><p>The machine got worse through the day and snapped back after the owner recalibrated it. Nobody using it changed anything. That wobble is drift. It is not wear and it is not caused by running circuits.</p></div>
<div class="card" style="margin-top:14px"><h3 class="am">What IBM publishes with every calibration (ibm_fez, one qubit pair, one week)</h3>
<table style="margin-top:6px"><tr><th>day</th><th>2-qubit gate error</th><th>readout error</th><th>T1 (µs)</th></tr>
<tr><td>Mon</td><td>0.52%</td><td>1.1%</td><td>310</td></tr><tr><td>Tue</td><td>0.61%</td><td>1.3%</td><td>285</td></tr><tr><td>Wed</td><td>0.58%</td><td>1.0%</td><td>290</td></tr><tr style="background:#e6e6e6"><td><b>Thu</b></td><td><b>0.89%</b></td><td>1.2%</td><td><b>240</b></td></tr><tr><td>Fri</td><td>0.49%</td><td>0.9%</td><td>325</td></tr></table>
<p style="margin-top:6px">The paper replays nine months of these numbers day by day.</p></div>'''
    # right: coherent vs stochastic
    def bars(rows,col):
        mx=max(v for _,v in rows)
        s='<svg width="300" height="150">'
        for i,(k,v) in enumerate(rows):
            w=v/mx*180; y=i*24+4
            s+=f'<text x="0" y="{y+14}" fill="#000" font-size="13" font-family="Menlo,monospace">{k}</text><rect x="60" y="{y+3}" width="{w}" height="14" fill="{col}"/><text x="{65+w}" y="{y+14}" fill="#000" font-size="12">{v}</text>'
        return s+'</svg>'
    right=f'''<div class="card" style="height:100%"><h3>Two machine states, same score 0.87, different fix</h3>
<div style="display:flex;gap:14px;margin-top:10px">
<div style="flex:1"><p><b class="pu">Mostly coherent error</b><br>Every gate over-rotates the same way, like a steering wheel pulled left. Wrong answers cluster.</p>{bars([("1111",48),("0011",31),("1100",27),("0001",9),("1000",7),("other",8)],"#000")}<p><b>Fix with twirling.</b> Scrambles the direction so the pulls cancel on average.</p></div>
<div style="flex:1"><p><b class="cy">Mostly stochastic error</b><br>A random kick in a random direction each shot. Wrong answers scatter as single flips.</p>{bars([("0001",31),("0010",29),("0100",28),("1000",27),("0011",8),("other",7)],"#888")}<p><b>Fix with ZNE.</b> Random noise scales cleanly with gate count, so extrapolation works.</p></div></div>
<div style="margin-top:16px;background:#f2f2f2;border:1px solid #000;border-radius:3px;padding:12px">
<p><b class="am">The drift dial in our simulator</b></p>
<svg width="560" height="60"><line x1="20" y1="30" x2="540" y2="30" stroke="#000" stroke-width="3"/><circle cx="150" cy="30" r="11" fill="#fff" stroke="#000" stroke-width="3"/><text x="20" y="55" fill="#000" font-size="14" font-weight="700">mostly stochastic → ZNE wins</text><text x="340" y="55" fill="#000" font-size="14" font-weight="700">mostly coherent → twirling wins</text></svg>
<p style="margin-top:6px">IonQ's noise model is fixed, so we inject our own, random Pauli kicks (p) and a steady over-rotation (θ) after every 2-qubit gate. Sliding the dial changes the <i>mix</i>, not the amount. <b>That flips which arm is best, and the learners have to notice.</b></p></div>
<div style="display:flex;gap:14px;margin-top:16px">
<div style="flex:1;background:#f2f2f2;border:1px solid #000;border-radius:3px;padding:12px"><p><b class="gr">Recalibration</b> is the machine's owner re-tunes the hardware, about once a day. Lasers re-aimed, pulses re-set. Users can't trigger it. It makes the machine itself better.</p></div>
<div style="flex:1;background:#f2f2f2;border:1px solid #000;border-radius:3px;padding:12px"><p><b class="cy">The arms</b> are pure software on your side. The gates run exactly as noisy as they run. Arms either make the noise do less damage (fewer gates, twirling) or estimate what the clean answer would have been (ZNE). Neither touches the machine.</p></div></div>
<p style="margin-top:14px"><b>So the bandit is the adaptive layer.</b> Arms can't adapt on their own. A recipe is a recipe. The learner watches how well each one works <i>today</i> and reroutes. It does for the software side what recalibration does for the hardware side, continuously, from the user's seat.</p></div>'''
    html=f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:16px;height:830px"><div>{left}</div><div>{right}</div></div><div class="foot">Counts and IBM rows are illustrative, shaped like the real data (HF phanerozoic/qiskit-calibration-drift, ibm_fez, Jan–Oct 2026). · diagram 5 of 14</div>'
    return page("What drift looks like in ones and zeros",html,"Noise is always there. Drift is the noise changing over time. The arms never fix the machine. They cope with whatever it is doing today.")

# ---------- 6. what comes out ----------
def img6():
    # regret chart
    W,H=720,300
    def curves():
        random.seed(2); out={}
        for k,rates in {"eps":(0.06,0.025,0.09),"ucb":(0.08,0.01,0.12),"ts":(0.07,0.008,0.11),"dts":(0.07,0.018,0.10)}.items():
            r=0;pts=[]
            for t in range(200):
                if t<25: rate=rates[0]
                elif t<100: rate=rates[1]
                else:
                    if k=="dts": rate=rates[2] if t<118 else 0.02
                    elif k=="ts": rate=rates[2] if t<150 else 0.05
                    elif k=="ucb": rate=rates[2] if t<170 else 0.09
                    else: rate=rates[2]
                r+=rate; pts.append(r)
            out[k]=pts
        return out
    cs=curves(); mx=18
    def X(t): return 50+t*(W-70)/200
    def Y(v): return H-30-v*(H-50)/mx
    svg=f'<svg width="{W}" height="{H}"><rect x="{X(100)}" y="10" width="{X(200)-X(100)}" height="{H-40}" fill="#000" opacity="0.06"/><line x1="{X(100)}" y1="10" x2="{X(100)}" y2="{H-30}" stroke="#000" stroke-width="1" stroke-dasharray="4 3"/><text x="{X(100)+6}" y="26" fill="#000" font-size="13" font-weight="700">drift (jump at pull 100)</text>'
    svg+=f'<line x1="50" y1="{H-30}" x2="{W-20}" y2="{H-30}" stroke="#000"/><line x1="50" y1="10" x2="50" y2="{H-30}" stroke="#000"/><text x="{W-60}" y="{H-8}" fill="#000" font-size="12">pulls</text><text x="4" y="20" fill="#000" font-size="12">regret</text>'
    cols={"eps":"#000","ucb":"#000","ts":"#000","dts":"#000"}; names={"eps":"ε-greedy","ucb":"UCB1","ts":"Thompson","dts":"Discounted Thompson (γ=0.95)"}
    for k,pts in cs.items():
        poly=" ".join(f"{X(t):.1f},{Y(v):.1f}" for t,v in enumerate(pts))
        svg+=f'<polyline points="{poly}" fill="none" stroke="#000" stroke-width="{2.8 if k=="dts" else 1.8}" stroke-dasharray="{DASH[k]}"/>'
    lx=60
    for k in cs:
        svg+=f'<line x1="{lx}" y1="{H-22}" x2="{lx+30}" y2="{H-22}" stroke="#000" stroke-width="{2.8 if k=="dts" else 1.8}" stroke-dasharray="{DASH[k]}"/><text x="{lx+36}" y="{H-18}" fill="#000" font-size="12">{names[k]}</text>'; lx+=56+len(names[k])*7
    svg+='</svg>'
    # arm strip
    random.seed(3)
    def seq(best_before,best_after,noise,recover):
        s=[]
        for t in range(200):
            if t<20: s.append(random.randint(1,8))
            elif t<100: s.append(best_before if random.random()>noise else random.randint(1,8))
            elif t<100+recover: s.append(best_before if random.random()>noise else random.randint(1,8))
            else: s.append(best_after if random.random()>noise else random.randint(1,8))
        return s
    seqs={"eps":seq(7,3,0.12,60),"ucb":seq(7,3,0.02,90),"ts":seq(7,3,0.03,60),"dts":seq(7,3,0.06,15)}
    armcol={1:"#e0e0e0",2:"#cfcfcf",3:"#8a8a8a",4:"#d8d8d8",5:"#dcdcdc",6:"#c4c4c4",7:"#000",8:"#bdbdbd"}
    strip=f'<svg width="{W}" height="140">'
    for i,(k,s) in enumerate(seqs.items()):
        y=i*30+4
        strip+=f'<text x="0" y="{y+16}" fill="#000" font-size="12">{names[k].split(" (")[0]}</text>'
        for t,a in enumerate(s): strip+=f'<rect x="{160+t*2.75:.1f}" y="{y}" width="2.75" height="22" fill="{armcol[a]}"/>'
    strip+=f'<line x1="{160+100*2.75}" y1="0" x2="{160+100*2.75}" y2="124" stroke="#000" stroke-width="1" stroke-dasharray="4 3"/>'
    strip+='<text x="160" y="138" fill="#000" font-size="12"><tspan fill="#000">■</tspan> arm 7, best before drift &nbsp; <tspan fill="#8a8a8a">■</tspan> arm 3, best after &nbsp; <tspan fill="#d0d0d0">■</tspan> other arms</text></svg>'
    html=f'''<div style="display:grid;grid-template-columns:760px 1fr;gap:18px;margin-top:14px">
<div style="display:flex;flex-direction:column;gap:14px">
<div class="card"><h3>Chart 1, cumulative pseudo-regret (vs the expected best arm each step), 20-seed bands</h3>{svg}</div>
<div class="card"><h3>Chart 2, which arm each learner pulled</h3>{strip}</div></div>
<div style="display:flex;flex-direction:column;gap:14px">
<div class="card" style="background:#f2f2f2"><h3>Recommendation</h3><p style="font-size:17px"><b>Arm 3. Pauli twirling on, ZNE off, readout mitigation off.</b><br>Locked on 118 pulls after the change (10 consecutive picks). Mirror score 0.91 vs 0.74 with nothing on, 0.90 with everything on.</p>
<div class="chip" style="margin-top:10px">from automitigate import twirl
tc = transpile(qc, optimization_level=1)
copies = [twirl(tc, seed=k) for k in range(8)]
job = backend.run(copies, shots=150)
counts = merge(job.result().get_counts())</div></div>
<div class="card"><h3>Arms and their cost</h3><table style="margin-top:6px"><tr><th>arm</th><th>ZNE</th><th>twirl</th><th>REM</th><th>circuits/pull</th><th>mean score</th></tr>
<tr><td>1</td><td>off</td><td>off</td><td>off</td><td>1</td><td>0.74</td></tr><tr><td>2</td><td>off</td><td>off</td><td>on</td><td>1 + 2</td><td>0.78</td></tr><tr style="background:#e6e6e6"><td><b>3</b></td><td>off</td><td><b>on</b></td><td>off</td><td>8</td><td><b>0.91</b></td></tr><tr><td>4</td><td>off</td><td>on</td><td>on</td><td>8 + 2</td><td>0.90</td></tr><tr><td>5</td><td>on</td><td>off</td><td>off</td><td>3</td><td>0.83</td></tr><tr><td>6</td><td>on</td><td>off</td><td>on</td><td>3 + 2</td><td>0.85</td></tr><tr><td>7</td><td>on</td><td>on</td><td>off</td><td>24</td><td>0.89</td></tr><tr><td>8</td><td>on</td><td>on</td><td>on</td><td>24 + 2</td><td>0.90</td></tr></table></div>
<div class="card"><h3 class="am">Controls at the top of the page</h3><p>circuit <b>GHZ-4</b> ▾ &nbsp; source <b>IonQ-like, jump</b> ▾ / ibm_fez real drift &nbsp; memory γ <b>0.95</b> ━●━ &nbsp; <b>[ Tune ]</b> &nbsp; mode <b>replay</b> | live</p></div></div></div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:14px">
<div class="card"><h3 class="cy">Reading chart 1</h3><p>Height is the score thrown away so far by not pulling the best arm. Flat means converged. A kink at the dashed line means drift caught it. Only the heavy solid line (Discounted Thompson) flattens again.</p></div>
<div class="card"><h3 class="am">Reading chart 2</h3><p>One tick per pull. Solid black before the line means locked onto arm 7. The sooner a row turns mid-grey (arm 3) after the line, the faster that learner noticed. Chart 1 also carries the four fixed policies (oracles, nothing, everything), omitted here.</p></div>
<div class="card"><h3 class="gr">Reading the recommendation</h3><p>The arm with the highest mean score <i>right now</i>, in plain words, with the exact Qiskit calls to reproduce it on your own circuit. Cost column tells you what it will take per run.</p></div></div>
<div class="foot">Mock-up with synthetic data. Replay mode re-runs the learners on stored reward tables (what judges see); live mode runs real jobs on IonQ Aria-1. · diagram 6 of 14</div>'''
    return page("The result screen",html,"After pressing Tune on GHZ-4 with the jump drift schedule.")

# ---------- 7. how you use it ----------
def img7():
    panels=[("1","A researcher has a circuit","A 12-qubit chemistry circuit (VQE for a small molecule). She needs a number accurate to 2%. The raw run is off by 11%. There are 8 mitigation combos, no rule, and every real-hardware shot costs credits.","#000"),
            ("2","Paste it, press Tune","AutoMitigate builds the mirror twin, runs the bandit on IonQ's noise model for a few minutes, 200 pulls, pennies in simulator time instead of hardware credits.","#000"),
            ("3","Gets a setting and the code","“Arm 3. Twirling on, ZNE off, readout mitigation off. Expected error 3% vs 11% raw. Costs 8 circuits per run.” Plus a copy-paste Qiskit snippet.","#000"),
            ("4","Runs the real job with it","One hardware job with the tuned setting instead of eight exploratory ones. Re-runs Tune next week if the machine has drifted.","#000")]
    html='<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:16px">'
    for n,t,p,c in panels:
        html+=f'<div class="card" style="border-color:{c};height:250px"><h3><span class="num" style="background:{c}">{n}</span>{t}</h3><p style="margin-top:8px">{p}</p></div>'
    html+='</div>'
    def bars(title,items,unit):
        mx=max(v for _,v,_ in items)*1.0; mx=mx if mx else 1
        mxw=290
        s=f'<div class="card" style="flex:1"><h3>{title}</h3><svg width="700" height="120">'
        for i,(k,v,c) in enumerate(items):
            y=i*50+10; w=v/mx*mxw
            s+=f'<text x="0" y="{y+22}" fill="#000" font-size="15">{k}</text><rect x="330" y="{y+6}" width="{w}" height="24" fill="{c}"/><text x="{340+w}" y="{y+23}" fill="#000" font-size="15" font-weight="700">{v}{unit}</text>'
        return s+'</svg></div>'
    html+=f'''<div style="display:flex;gap:16px;margin-top:16px">
{bars("Error on the final answer (illustrative)",[("Default settings, no tuning",11,"#999"),("AutoMitigate's pick",3,"#000")],"%")}
{bars("Hardware shots spent finding the setting",[("Try all 8 by hand on hardware",9600,"#999"),("Bandit on free sim, then 1 real run",1200,"#000")],"")}</div>
<div class="card" style="margin-top:16px"><h3 class="pu">When it's useful</h3>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:8px">
<p><b>New circuit.</b> Nobody knows which trick suits it. Five minutes beats a week of reading papers.</p>
<p><b>New machine.</b> Trapped ions and superconducting chips favour different tricks. The bandit doesn't care which one it's on.</p>
<p><b>Machine drifted.</b> Last month's setting may be wrong now. Re-tune, and the forgetting learner notices without being told.</p>
<p><b>Limited credits.</b> Students and small labs can't afford trial and error on hardware. Exploration happens on the free simulator.</p></div></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px">
<div class="card"><h3>What it does not do</h3><p>It does not fix the machine, remove noise, or guarantee a result. It picks, from the tricks you already have, the one that works best on your circuit today. The hackathon version's drift is synthetic and the noise model is depolarising only; the project card says so.</p></div>
<div class="card" style="background:#f2f2f2"><h3>Where it goes next, the paper</h3><p>Replace synthetic drift with nine months of real IBM calibration logs, replay them day by day, and ask the question nobody has checked. Does the best setting actually change on a real machine? Yes means online tuning is necessary. No means a fixed setting is fine. Either answer is a result.</p></div></div>
<div class="foot">Numbers are illustrative, not measured. The honest claim is an online tuner for mitigation settings that needs no known answer and re-tunes under drift. · diagram 7 of 14</div>'''
    return page("How someone uses it and why they would care",html,"The tool after the hackathon, seen from the user side.")

for i,f in enumerate([img1,img2,img3,img4,img5,img6,img7],1):
    open(os.path.join(OUT,f"{i:02d}.html"),"w").write(f())
print("wrote 7 html files")
