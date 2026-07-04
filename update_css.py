import re

css = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-base: #000000;
    --bg-surface: #0A0A0A;
    --bg-raised: #141414;
    --border: rgba(255, 255, 255, 0.08);
    --border-accent: rgba(255, 255, 255, 0.15);
    --text-primary: #EDEDED;
    --text-secondary: #A1A1AA;
    --text-muted: #71717A;
    --accent: #3B82F6;
    --accent-glow: rgba(59, 130, 246, 0.15);
    --green: #10B981;
    --red: #EF4444;
}

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, sans-serif !important;
    background: var(--bg-base) !important;
    color: var(--text-primary);
    -webkit-font-smoothing: antialiased;
}

#MainMenu, footer, [data-testid="stSidebarNav"] { visibility: hidden; display: none; }
.stDeployButton { display: none; }

.main .block-container {
    background: var(--bg-base);
    padding: 3rem 4rem;
    max-width: 1400px;
}

section[data-testid="stSidebar"] {
    background: var(--bg-surface) !important;
    border-right: 1px solid var(--border);
}

div[data-testid="stSidebar"] .stRadio label {
    padding: 0.5rem 1rem;
    border-radius: 6px;
    color: var(--text-secondary);
    font-size: 0.85rem;
    font-weight: 500;
    transition: all 0.2s ease;
    margin: 2px 8px;
}

div[data-testid="stSidebar"] .stRadio label:hover {
    background: var(--bg-raised);
    color: var(--text-primary);
}

div[data-testid="stSidebar"] .stRadio label[data-checked="true"] {
    background: var(--bg-raised);
    color: var(--text-primary);
    border-left: 3px solid var(--accent);
    padding-left: calc(1rem - 3px);
}

div[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none; }
div[data-testid="stSidebar"] [data-testid="stRadio"] > div { gap: 4px; }

h1 {
    font-weight: 700;
    font-size: 2.25rem;
    letter-spacing: -0.04em;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.75rem;
    margin-bottom: 2rem;
}

h2, h3 {
    font-weight: 600;
    letter-spacing: -0.02em;
    color: var(--text-primary);
}

.saas-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    transition: border-color 0.2s, transform 0.2s;
}
.saas-card:hover {
    border-color: var(--border-accent);
}

.stButton > button {
    background: var(--bg-raised);
    color: var(--text-primary);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 500;
    transition: all 0.2s;
}
.stButton > button:hover {
    border-color: var(--border-accent);
    background: rgba(255,255,255,0.05);
}
.stButton > button[kind="primary"] {
    background: var(--accent);
    color: #fff;
    border: none;
}
.stButton > button[kind="primary"]:hover {
    background: #2563EB;
}

@keyframes fade-in-up {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.main .block-container > * {
    animation: fade-in-up 0.4s ease forwards;
}

div[data-testid="stMetric"] { display: none; }
hr { border-top: 1px solid var(--border); }
.stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div > div {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    color: var(--text-primary);
    border-radius: 6px;
}
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 1px var(--accent);
}
</style>"""

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_content = re.sub(r'<style>.*?</style>', css, content, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('app.py CSS updated')
