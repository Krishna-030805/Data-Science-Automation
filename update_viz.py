import re

with open('core/visualizer.py', 'r', encoding='utf-8') as f:
    content = f.read()

template_code = """
import plotly.io as pio
import plotly.graph_objects as go

saas_template = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Inter, sans-serif", color="#A1A1AA"),
        title=dict(font=dict(color="#EDEDED", size=18, family="Inter, sans-serif")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.05)"),
        colorway=["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899", "#06B6D4", "#F97316"],
        margin=dict(t=50, b=40, l=40, r=40)
    )
)
pio.templates["saas"] = saas_template
pio.templates.default = "saas"
"""

# Insert template setup after imports
content = re.sub(r'(from config import PALETTE\s*)', r'\1\n' + template_code + '\n', content)

# Replace plotly_dark with saas
content = content.replace('"plotly_dark"', '"saas"')
content = content.replace("'plotly_dark'", '"saas"')

with open('core/visualizer.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Visualizer updated with SaaS theme.")
