import os, json
H=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.expanduser("~/automitigate")
src=open(os.path.join(H,"diagram_style.py")).read()
exec(src[:src.index("# ---------- 1. the loop")])   # CSS, page(), arrow(), MARK from the diagram generator
CSS += """
body{display:flex;flex-direction:column;justify-content:flex-start}
.content{margin:auto 0;width:100%}
h1{font-size:40px}.sub{font-size:22px;margin-top:10px}
.card h3{font-size:24px}.card p{font-size:20px;line-height:1.4}.chip{font-size:17px;padding:6px 10px}
th,td{font-size:24px;padding:12px 18px}
.k{font-size:150px;font-weight:700;letter-spacing:-2px;line-height:1}
.kl{font-size:24px;margin-top:10px}
.frame{border:1px solid #000;border-radius:3px;padding:10px;background:#fff;display:inline-block}
.center{display:flex;justify-content:center;align-items:center}
.armbox{width:172px;height:160px;border:1px solid #000;border-radius:3px;padding:14px 16px;font-size:21px;line-height:1.5}
"""
def P(title, body, sub=""): return page(title, f'<div class="content">{body}</div>', sub)
def foot(n): return ""
def framed(path, h=700, w=1500, fw=None): return f'<div class="center" style="margin-top:22px"><div class="frame"><img src="file://{path}" style="{"width:"+str(fw)+"px;" if fw else ""}max-width:{w}px;max-height:{h}px;display:block"></div></div>'
s={}
s["01-title"]=page("", f'''<div class="content"><div><div style="font-size:88px;font-weight:700;letter-spacing:-2px">AutoMitigate</div>
<div style="font-size:30px;margin-top:22px">A bandit that picks your error-mitigation settings for you.</div>
<div class="chip" style="margin-top:40px;font-size:16px">Ian Wilson · Thomas Sebahi · McGill University</div></div></div>{foot("1 of 16")}''')
def sketch(kind):
    if kind=="zne":
        return '<svg width="420" height="150"><rect x="10" y="100" width="120" height="14" fill="#000"/><rect x="10" y="70" width="120" height="14" fill="#999"/><rect x="10" y="40" width="120" height="14" fill="#ccc"/><text x="140" y="112" font-size="16">1× noise</text><text x="140" y="82" font-size="16">3×</text><text x="140" y="52" font-size="16">5×</text><polyline points="260,120 300,95 340,70 380,45" fill="none" stroke="#000" stroke-width="2"/><circle cx="400" cy="32" r="5" fill="none" stroke="#000" stroke-width="2"/><text x="250" y="145" font-size="15">extrapolate to 0×</text></svg>'
    if kind=="twirl":
        return '<svg width="420" height="150">'+''.join(f'<rect x="10" y="{8+i*17}" width="200" height="11" rx="2" fill="#555"/>' for i in range(8))+'<text x="230" y="80" font-size="16">8 random copies,</text><text x="230" y="104" font-size="16">averaged</text></svg>'
    return '<svg width="420" height="150"><rect x="10" y="30" width="200" height="14" fill="none" stroke="#000" stroke-width="2"/><text x="220" y="43" font-size="16">prepare 0000, read it</text><rect x="10" y="70" width="200" height="14" fill="none" stroke="#000" stroke-width="2"/><text x="220" y="83" font-size="16">prepare 1111, read it</text><text x="10" y="130" font-size="16">invert the confusion matrix</text></svg>'
def card(n,t,p,chip="",extra=""): return f'<div class="card" style="flex:1;min-height:380px"><h3><span class="num">{n}</span>{t}</h3><p>{p}</p>{f"<div class=chip>{chip}</div>" if chip else ""}<div style="margin-top:14px">{extra}</div></div>'
s["02-three-fixes"]=P("Noisy answers, three fixes", f'''<div style="display:flex;gap:18px;margin-top:40px">
{card(1,"Zero-noise extrapolation","Run at 1×, 3×, 5× the noise. Extrapolate back to 0×.","3 circuits",sketch("zne"))}
{card(2,"Pauli twirling","Random Pauli flips around every two-qubit gate. Coherent errors average out.","8 circuits",sketch("twirl"))}
{card(3,"Readout mitigation","Measure the detector's own bias. Undo it.","2 calibration circuits",sketch("rem"))}</div>{foot("2 of 16")}''')
ser=json.load(open(os.path.join(H,"cz_series.json"))); ys=ser["cz"]; lo,hi=min(ys),max(ys)
pts=" ".join(f"{60+i*1360/(len(ys)-1):.1f},{480-400*(y-lo)/(hi-lo):.1f}" for i,y in enumerate(ys))
s["03-depends-on-the-day"]=P("Which ones to switch on depends on the circuit, the machine, and the day", f'''<div class="card" style="margin-top:30px;height:700px;position:relative"><h3>Two-qubit gate error on the ibm_fez chain we used, Jan 31 to Oct 9 2026</h3>
<svg width="1460" height="600" style="position:absolute;left:18px;top:70px"><line x1="60" y1="80" x2="1420" y2="80" stroke="#ccc" stroke-dasharray="4 4"/><polyline fill="none" stroke="#000" stroke-width="2.5" points="{pts}"/><line x1="60" y1="490" x2="1420" y2="490" stroke="#000"/><text x="60" y="525" font-size="20">Jan 31</text><text x="1360" y="525" font-size="20">Oct 9</text><text x="0" y="86" font-size="20">1.6 %</text><text x="0" y="486" font-size="20">0.2 %</text><text x="480" y="570" font-size="20">mean two-qubit error on the four-qubit chain, 241 daily calibration snapshots</text></svg></div>{foot("3 of 16")}''',
"")
arms=""
for a in range(8):
    z,t,r=a&4,a&2,a&1
    arms+=f'<div class="armbox"><b>arm {a}</b><br><span class="{"on" if z else "off"}">{"● " if z else "○ "}ZNE</span><br><span class="{"on" if t else "off"}">{"● " if t else "○ "}twirl</span><br><span class="{"on" if r else "off"}">{"● " if r else "○ "}REM</span></div>'
s["04-bandit"]=P("Treat it as a bandit", f'''<div style="display:flex;gap:18px;margin-top:40px">{arms}</div><p style="font-size:19px;margin-top:14px">ZNE = zero-noise extrapolation · twirl = Pauli twirling · REM = readout-error mitigation</p>
<div style="position:relative;height:380px;margin-top:60px"><svg width="1504" height="380" style="position:absolute;left:0;top:0">{MARK}
<rect x="60" y="60" width="300" height="90" rx="3" fill="#fff" stroke="#000"/><text x="210" y="112" font-size="28" font-weight="700" text-anchor="middle">pull an arm</text>
<rect x="600" y="60" width="300" height="90" rx="3" fill="#fff" stroke="#000"/><text x="750" y="112" font-size="28" font-weight="700" text-anchor="middle">score it</text>
<rect x="1140" y="60" width="300" height="90" rx="3" fill="#fff" stroke="#000"/><text x="1290" y="112" font-size="28" font-weight="700" text-anchor="middle">update</text>
{arrow(362,105,594,105)}{arrow(902,105,1134,105)}
<path d="M1290,152 L1290,230 L210,230 L210,158" stroke="#000" stroke-width="2" fill="none" stroke-dasharray="8 5" marker-end="url(#ah)"/>
<text x="750" y="275" font-size="22" text-anchor="middle">one pull per day</text></svg></div>{foot("4 of 16")}''',
"")
s["05-mirror"]=P("The score is a mirror circuit", f'''<div style="position:relative;height:520px;margin-top:50px"><svg width="1504" height="520" style="position:absolute;left:0;top:0">{MARK}
<rect x="20" y="120" width="300" height="130" rx="3" fill="#fff" stroke="#000"/><text x="170" y="178" font-size="26" font-weight="700" text-anchor="middle">your circuit</text><text x="170" y="210" font-size="26" text-anchor="middle" font-family="Menlo">U</text>
<rect x="400" y="120" width="300" height="130" rx="3" fill="#fff" stroke="#000"/><text x="550" y="178" font-size="26" font-weight="700" text-anchor="middle">random Pauli layer</text><text x="550" y="210" font-size="26" text-anchor="middle" font-family="Menlo">Q</text>
<rect x="780" y="120" width="300" height="130" rx="3" fill="#fff" stroke="#000"/><text x="930" y="178" font-size="26" font-weight="700" text-anchor="middle">the gates undone</text><text x="930" y="210" font-size="26" text-anchor="middle" font-family="Menlo">Ũ⁻¹</text>
<rect x="1160" y="120" width="320" height="130" rx="3" fill="#eee" stroke="#000"/><text x="1320" y="178" font-size="26" font-weight="700" text-anchor="middle">one known bitstring</text><text x="1320" y="210" font-size="26" text-anchor="middle" font-family="Menlo">00011110</text>
{arrow(322,185,394,185)}{arrow(702,185,774,185)}{arrow(1082,185,1154,185)}
<text x="750" y="350" font-size="34" font-weight="700" text-anchor="middle">score = how often that bitstring comes out</text>
<text x="750" y="410" font-size="24" text-anchor="middle">no ideal simulation needed</text></svg></div>{foot("5 of 16")}''')
s["06-qollab-run"]=P("On Qollab", framed(f"{H}/shots/console_table.png", 780, 1500)+foot("6 of 16"), "GHZ-8 on nine months of real ibm_fez calibration data, one pull per day.")
s["07-chart"]=P("What comes out", framed(f"{H}/shots/chart_0.png", 760, 1500)+foot("7 of 16"), "Regret = score lost by not pulling the day's best arm. Below: the arm picked each day.")
s["08-live-run"]=P("Then the circuit runs for real on the simulator you chose", f'''<div style="display:flex;gap:18px;margin-top:60px">
<div class="card" style="flex:1;text-align:center;padding:90px 40px"><div class="k">0.82</div><div class="kl">raw</div></div>
<div class="card" style="flex:1;text-align:center;padding:90px 40px"><div class="k">0.94</div><div class="kl">after readout mitigation</div></div>
<div class="card" style="flex:1;text-align:center;padding:90px 40px;background:#eee"><div class="k">1.00</div><div class="kl">ideal</div></div></div>
{framed(f"{H}/shots/live_lines.png", 200, 1500)}{foot("8 of 16")}''', "GHZ-8 parity on the IBM Fez noise-model simulator, 1000 shots.")
s["09-drift-value"]=P("The best setting never changed", framed(f"{REPO}/figures/drift_value.png", 780, 1500, fw=1140)+foot("9 of 16"), "Drift value = what a perfect day-by-day tracker gains over picking once. 240 days, five circuits: under 0.01 %.")
s["10-best-arm"]=P("Every day the same arm", '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:20px">'+"".join(f'<div class="frame" style="padding:6px"><img src="file://{REPO}/figures/best_arm_{c}.png" style="width:730px;display:block"></div>' for c in ["ghz4","ghz8","grover3","qaoa6","qft3"])+'<div class="card" style="padding:18px"><p>Black line = best arm each day (Z = ZNE, T = twirl, R = readout mitigation). Grey = a significant switch.</p></div></div>'+foot("10 of 16"), "ZNE + readout mitigation was the best arm on every one of the 240 days.")
rows="".join(f"<tr><td>{c}</td><td>{e}</td><td>{a7}</td><td><b>{p}</b></td></tr>" for c,e,a7,p in [("ghz4","1.60","4.46","64 %"),("ghz8","3.26","11.47","72 %"),("grover3","3.08","14.87","79 %"),("qaoa6","3.19","13.73","77 %"),("qft3","2.16","3.96","45 %")])
s["11-regret-table"]=P("Finding that setting cheaply", f'''<div style="display:flex;gap:18px;margin-top:40px"><div class="card" style="flex:1;text-align:center;padding:60px 30px"><div class="k">45–79 %</div><div class="kl">less regret than switching everything on</div></div><div class="card" style="flex:1.3"><table style="font-size:24px;width:100%"><tr><th>circuit</th><th>ε-greedy learner</th><th>everything switched on (arm 7)</th><th>learner is lower by</th></tr>{rows}</table>
<p style="margin-top:14px">regret = score lost vs always picking the best arm, over 240 days. Lower is better.</p></div></div>{foot("11 of 16")}''')
s["11b-all-circuits"]=P("The same on every circuit", '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-top:20px">'+"".join(f'<div class="frame" style="padding:6px"><img src="file://{REPO}/figures/regret_{c}.png" style="width:470px;display:block"></div>' for c in ["ghz4","ghz8","grover3","qaoa6","qft3"])+'<div class="card" style="padding:18px"><p>Cumulative regret, 240 days. Thick line = ε-greedy. Dashed = everything switched on. The learner is lowest on all five.</p></div></div>'+foot(""), "")
s["12-proxy"]=P("Is the score honest?", framed(f"{REPO}/figures/proxy_per_day.png", 800, 1500, fw=1160)+foot("12 of 16"), "Rank agreement between the mirror score and the real error, per day.")
s["13-ionq"]=P("A different machine", framed(f"{H}/shots/chart_1.png", 760, 1500)+foot("13 of 16"), "IonQ-like model, noise jumps at step 150. Everything-on stays best; the gap is the cost of checking.")
s["14-spot-check"]=P("Checked against Qollab's Aria-1 simulator", f'''<div style="display:flex;gap:18px;margin-top:60px">
<div class="card" style="flex:1;text-align:center;padding:90px 40px"><div class="k">0.027</div><div class="kl">mean difference in P(target), our model vs Qollab's Aria-1 simulator</div></div>
<div class="card" style="flex:1;text-align:center;padding:90px 40px"><div class="k">8</div><div class="kl">identical circuits, job IDs in the repo</div><div class="chip">data/ionq/spot_check.json</div></div></div>{foot("14 of 16")}''')
s["15-caveat"]=P("One caveat", f'''<div style="display:flex;gap:18px;margin-top:60px">
<div class="card" style="flex:1;text-align:center;padding:90px 40px"><div class="k">9</div><div class="kl">best-arm switches on a middling chain of qubits</div></div>
<div class="card" style="flex:1;text-align:center;padding:90px 40px"><div class="k">0.37 %</div><div class="kl">drift value there, vs under 0.01 % on the best chain</div></div></div>
<div class="card" style="margin-top:18px"><p style="font-size:20px"><b>Tracking matters exactly where the hardware is worse.</b></p></div>{foot("15 of 16")}''')
s["16-end"]=page("", f'''<div class="content"><div><div style="font-size:88px;font-weight:700;letter-spacing:-2px">AutoMitigate</div>
<div class="chip" style="margin-top:30px;font-size:18px">github.com/I-ala-Wilson/automitigate</div>
<div style="font-size:22px;margin-top:26px">MIT licence · pip install -e . · every number reproducible from the committed tables</div>
<div style="font-size:22px;margin-top:60px">Ian Wilson · Thomas Sebahi · McGill University</div></div></div>{foot("16 of 16")}''')
for i,(k,v) in enumerate(s.items(),1): open(f"{H}/{i:02d}.html","w").write(v)
print(len(s),"slides written")
