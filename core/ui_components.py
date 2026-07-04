import json
import streamlit as st
import pandas as pd

def _fmt(value):
    try:
        n = float(str(value).replace(",", "").replace("%", "").replace(" MB", ""))
        return n, str(value)
    except (ValueError, TypeError):
        return 0.0, str(value)

# 1. SaaS KPI Card
def saas_kpi_card(title: str, value, trend=None, prefix: str = "", suffix: str = "", delay: int = 0, height: int = 120):
    num_val, disp = _fmt(value)
    
    trend_html = ""
    if trend is not None:
        try:
            t = float(str(trend).replace(",", "").replace("%", ""))
            arrow = "↑" if t >= 0 else "↓"
            trend_color = "#10B981" if t >= 0 else "#EF4444"
            trend_html = f"<div style='color:{trend_color}; font-size: 0.85rem; font-weight: 500; margin-top: 4px; display: flex; align-items: center; gap: 4px;'><span>{arrow}</span> {trend}</div>"
        except:
            trend_html = f"<div style='color:#71717A; font-size: 0.85rem; font-weight: 500; margin-top: 4px;'>{trend}</div>"

    uid = abs(hash(title + str(value))) % 999999

    html = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  
  .saas-kpi-{uid} {{
    font-family: 'Inter', sans-serif;
    background: #0A0A0A;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s ease, transform 0.2s ease;
    animation: fade-in-up-{uid} 0.4s ease {delay}ms forwards;
    opacity: 0;
    transform: translateY(10px);
  }}
  .saas-kpi-{uid}:hover {{
    border-color: rgba(255,255,255,0.15);
  }}
  .kpi-title-{uid} {{
    color: #A1A1AA;
    font-size: 0.875rem;
    font-weight: 500;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .kpi-value-{uid} {{
    color: #EDEDED;
    font-size: 2rem;
    font-weight: 600;
    line-height: 1.2;
    letter-spacing: -0.02em;
  }}
  @keyframes fade-in-up-{uid} {{
    to {{ opacity: 1; transform: translateY(0); }}
  }}
</style>
<div class="saas-kpi-{uid}">
  <div class="kpi-title-{uid}">{title}</div>
  <div class="kpi-value-{uid}" id="kpi-v-{uid}">{prefix}0{suffix}</div>
  {trend_html}
</div>
<script>
(function(){{
  const el = document.getElementById('kpi-v-{uid}');
  const target = {num_val}; const prefix = '{prefix}'; const suffix = '{suffix}'; const disp = '{disp}';
  const isFloat = target !== Math.floor(target); const duration = 1200; const delay_ms = {delay};
  if(isNaN(target)){{ setTimeout(() => el.textContent = disp, delay_ms); return; }}
  setTimeout(() => {{
    const t0 = performance.now();
    function ease(t) {{ return 1 - Math.pow(1 - t, 3); }}
    function step(now) {{
      const prog = Math.min((now - t0) / duration, 1);
      const val = target * ease(prog);
      el.textContent = isFloat ? prefix + val.toFixed(2) + suffix : prefix + Math.floor(val).toLocaleString() + suffix;
      if(prog < 1) requestAnimationFrame(step);
      else el.textContent = prefix + disp + suffix;
    }}
    requestAnimationFrame(step);
  }}, delay_ms);
}})();
</script>
"""
    st.components.v1.html(html, height=height, scrolling=False)


# 2. SaaS Radial Gauge
def saas_radial_gauge(score: float, label: str = "Quality Score", details: list = None, height: int = 240):
    html = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  
  .gauge-container {{
    display: flex;
    flex-direction: column;
    align-items: center;
    font-family: 'Inter', sans-serif;
  }}
  .gauge-label {{
    color: #A1A1AA;
    font-size: 0.875rem;
    font-weight: 500;
    margin-top: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .gauge-wrapper {{
    position: relative;
    width: 160px;
    height: 160px;
  }}
  canvas#sg-canvas {{
    position: absolute;
    top: 0; left: 0;
    filter: drop-shadow(0 0 12px rgba(59, 130, 246, 0.2));
  }}
  .gauge-text {{
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }}
  .gauge-val {{
    color: #EDEDED;
    font-size: 2.5rem;
    font-weight: 600;
    line-height: 1;
    letter-spacing: -0.02em;
  }}
  .gauge-sub {{
    color: #71717A;
    font-size: 0.75rem;
    margin-top: 4px;
  }}
</style>
<div class="gauge-container">
  <div class="gauge-wrapper">
    <canvas id="sg-canvas" width="160" height="160"></canvas>
    <div class="gauge-text">
      <div class="gauge-val" id="sg-val">0</div>
      <div class="gauge-sub">/ 100</div>
    </div>
  </div>
  <div class="gauge-label">{label}</div>
</div>
<script>
(function(){{
  const canvas = document.getElementById('sg-canvas');
  const ctx = canvas.getContext('2d');
  const valEl = document.getElementById('sg-val');
  const target = {score};
  const duration = 1500;
  
  function getColor(pct) {{
    if(pct < 0.5) return '#EF4444'; // Red
    if(pct < 0.8) return '#F59E0B'; // Amber
    return '#10B981'; // Green
  }}

  function draw(current) {{
    ctx.clearRect(0,0,160,160);
    const cx = 80, cy = 80, r = 70;
    const sa = -Math.PI/2;
    const pct = current / 100;
    const ea = sa + (2 * Math.PI) * pct;
    
    // Background track
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, 2*Math.PI);
    ctx.strokeStyle = 'rgba(255,255,255,0.05)';
    ctx.lineWidth = 8;
    ctx.stroke();

    // Foreground arc
    if(current > 0) {{
      const color = getColor(pct);
      ctx.beginPath();
      ctx.arc(cx, cy, r, sa, ea);
      ctx.strokeStyle = color;
      ctx.lineWidth = 8;
      ctx.lineCap = 'round';
      ctx.stroke();
    }}
    
    valEl.textContent = Math.round(current);
  }}

  const t0 = performance.now();
  function ease(t) {{ return 1 - Math.pow(1 - t, 3); }}
  function step(now) {{
    const prog = Math.min((now - t0)/duration, 1);
    draw(target * ease(prog));
    if(prog < 1) requestAnimationFrame(step);
    else draw(target);
  }}
  requestAnimationFrame(step);
}})();
</script>
"""
    st.components.v1.html(html, height=height, scrolling=False)


# 3. SaaS Alert
def saas_alert(message: str, type: str = "info", height: int = 70):
    icons = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "success": "✅"
    }
    colors = {
        "info": "#3B82F6",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "success": "#10B981"
    }
    icon = icons.get(type, "ℹ️")
    color = colors.get(type, "#3B82F6")
    
    html = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=swap');
  .saas-alert {{
    font-family: 'Inter', sans-serif;
    display: flex;
    align-items: center;
    padding: 12px 16px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-left: 3px solid {color};
    border-radius: 6px;
    color: #EDEDED;
    font-size: 0.9rem;
    line-height: 1.5;
  }}
  .saas-alert-icon {{
    margin-right: 12px;
    font-size: 1.1rem;
  }}
</style>
<div class="saas-alert">
  <div class="saas-alert-icon">{icon}</div>
  <div>{message}</div>
</div>
"""
    st.components.v1.html(html, height=height, scrolling=False)


# 4. SaaS Physics Universe (Datadog/Palantir aesthetic)
def correlation_physics_universe(df: pd.DataFrame, height: int = 500):
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if len(num_cols) < 2:
        saas_alert("Need at least 2 numeric columns for the network map.", "warning")
        return

    cols = num_cols[:18]
    corr = df[cols].corr().fillna(0)

    edges = []
    for i, ca in enumerate(cols):
        for j, cb in enumerate(cols):
            if j <= i: continue
            c = float(corr.loc[ca, cb])
            if abs(c) > 0.15:
                edges.append({"source": i, "target": j, "strength": round(c, 3)})

    nodes_json = json.dumps([{"label": c} for c in cols])
    edges_json = json.dumps(edges)
    
    html = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=swap');
  #saas-net-wrap {{
    position: relative;
    width: 100%;
    height: {height-20}px;
    background: #0A0A0A;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    overflow: hidden;
  }}
  canvas#net-canvas {{ display: block; cursor: grab; }}
  canvas#net-canvas:active {{ cursor: grabbing; }}
  .net-legend {{
    position: absolute;
    bottom: 12px; left: 16px;
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    color: #71717A;
    display: flex; gap: 12px;
  }}
  .leg-item {{ display: flex; align-items: center; gap: 6px; }}
  .leg-dot {{ width: 8px; height: 8px; border-radius: 50%; }}
</style>
<div id="saas-net-wrap">
  <canvas id="net-canvas"></canvas>
  <div class="net-legend">
    <div class="leg-item"><div class="leg-dot" style="background:#3B82F6"></div>Positive</div>
    <div class="leg-item"><div class="leg-dot" style="background:#EF4444"></div>Negative</div>
    <div class="leg-item" style="color:#A1A1AA">Interactive</div>
  </div>
</div>
<script>
(function(){{
  const NODES = {nodes_json}; const EDGES = {edges_json};
  const wrap = document.getElementById('saas-net-wrap');
  const canvas = document.getElementById('net-canvas');
  const ctx = canvas.getContext('2d');
  
  const W = wrap.offsetWidth || 600; const H = {height-20};
  canvas.width = W; canvas.height = H;
  
  const nodes = NODES.map((n,i)=>({{
    id:i, label:n.label,
    x: W/2 + (Math.random()-0.5)*W*0.5, y: H/2 + (Math.random()-0.5)*H*0.5,
    vx:0, vy:0, r: 4
  }}));
  
  const REP = 3000, SPRING = 0.02, DAMP = 0.8, CP = 0.005;
  
  function sim(){{
    const cx = W/2, cy = H/2;
    for(const n of nodes){{ n.vx+=(cx-n.x)*CP; n.vy+=(cy-n.y)*CP; }}
    
    for(let i=0; i<nodes.length; i++)for(let j=i+1; j<nodes.length; j++){{
      const dx=nodes[j].x-nodes[i].x, dy=nodes[j].y-nodes[i].y;
      const d2=dx*dx+dy*dy+1, d=Math.sqrt(d2), f=REP/d2;
      nodes[i].vx-=(dx/d)*f; nodes[i].vy-=(dy/d)*f;
      nodes[j].vx+=(dx/d)*f; nodes[j].vy+=(dy/d)*f;
    }}
    
    for(const e of EDGES){{
      const a=nodes[e.source], b=nodes[e.target];
      const dx=b.x-a.x, dy=b.y-a.y, d=Math.sqrt(dx*dx+dy*dy)+1;
      const ideal = 150 - Math.abs(e.strength)*80;
      const f = SPRING*(d-ideal)*Math.abs(e.strength);
      a.vx+=(dx/d)*f; a.vy+=(dy/d)*f;
      b.vx-=(dx/d)*f; b.vy-=(dy/d)*f;
    }}
    
    for(const n of nodes){{
      if(n === dragNode) continue;
      n.vx*=DAMP; n.vy*=DAMP; n.x+=n.vx; n.y+=n.vy;
      n.x = Math.max(10, Math.min(W-10, n.x));
      n.y = Math.max(10, Math.min(H-10, n.y));
    }}
  }}
  
  function draw(){{
    ctx.clearRect(0,0,W,H);
    // Draw edges
    for(const e of EDGES){{
      const a=nodes[e.source], b=nodes[e.target];
      ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y);
      const alpha = 0.2 + Math.abs(e.strength)*0.5;
      ctx.strokeStyle = e.strength > 0 ? `rgba(59,130,246,${{alpha}})` : `rgba(239,68,68,${{alpha}})`;
      ctx.lineWidth = 1 + Math.abs(e.strength)*2;
      ctx.stroke();
    }}
    
    // Draw nodes
    for(const n of nodes){{
      ctx.beginPath(); ctx.arc(n.x,n.y,n.r,0,Math.PI*2);
      ctx.fillStyle = '#EDEDED';
      if(n === dragNode) {{
        ctx.shadowColor = '#3B82F6'; ctx.shadowBlur = 10;
        ctx.fillStyle = '#3B82F6';
      }}
      ctx.fill(); ctx.shadowBlur = 0;
      
      // Labels
      ctx.fillStyle = '#A1A1AA';
      ctx.font = '500 10px Inter, sans-serif';
      ctx.textAlign = 'center'; ctx.textBaseline = 'top';
      ctx.fillText(n.label, n.x, n.y + 8);
    }}
  }}
  
  function loop(){{ sim(); draw(); requestAnimationFrame(loop); }}
  loop();
  
  let dragNode = null, ox=0, oy=0;
  function getP(e){{ const r=canvas.getBoundingClientRect(); const t=e.touches?e.touches[0]:e; return [t.clientX-r.left, t.clientY-r.top]; }}
  canvas.addEventListener('mousedown', e=>{{ const [x,y]=getP(e); dragNode=nodes.find(n=>Math.hypot(n.x-x,n.y-y)<15); if(dragNode){{ox=dragNode.x-x; oy=dragNode.y-y;}} }});
  canvas.addEventListener('mousemove', e=>{{ if(!dragNode)return; const [x,y]=getP(e); dragNode.x=x+ox; dragNode.y=y+oy; }});
  canvas.addEventListener('mouseup', ()=>{{dragNode=null;}});
  canvas.addEventListener('mouseleave', ()=>{{dragNode=null;}});
}})();
</script>
"""
    st.components.v1.html(html, height=height, scrolling=False)

# Keep the old references just in case some page still uses them before migration
animated_counter = saas_kpi_card
animated_radial_gauge = saas_radial_gauge

