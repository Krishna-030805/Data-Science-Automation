"""
app.py  —  DataSense AI: Main Streamlit application entry point.
Multi-page app with persistent sidebar navigation and live action log.
"""

# ── Path setup ──────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))

# ── Imports ────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import datetime
from core.voice_engine import VoiceOnboardingEngine
from core.llm_engine import correction_agent

# ── Page config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataSense AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
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
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ──────────────────────────────────────────
defaults = {
    "df": None,
    "df_original": None,
    "file_names": [],
    "goals": [],
    "goals_confirmed": False,
    "target_col": None,
    "ml_task": None,
    "hypothesis": "",
    "domain_context": "",
    "action_log": [],
    "user_notes": [],
    "flags": [],
    "ml_results": None,
    "best_model": None,
    "overview": None,
    "profiling_df": None,
    "corr_matrix": None,
    "outlier_summary": {},
    "wrangling_history": [],
    "df_stack": [],
    "all_insights": [],
    "feature_imp_df": None,
    "voice_onboarding_active": False,
    "voice_engine": None,
    "voice_transcript": [],
    "messages": [],
    "qa_messages": [],
    "ai_profile_summary": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Log helper ──────────────────────────────────────────────────────
def log(msg: str, status: str = "✅"):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state["action_log"].append({"time": ts, "action": msg, "status": status})


# ── Pages ────────────────────────────────────────────────────────────
PAGES = {
    "🏠 Home":            None, # Handled natively in app.py
    "📂 Data Upload":     "pages/upload.py",
    "🎯 Insight Goals":   "pages/goals.py",
    "🔍 Data Mining":     "pages/mining.py",
    "🔧 Data Wrangling":  "pages/wrangling.py",
    "📊 Analysis":        "pages/analysis.py",
    "🤖 ML Models":       "pages/ml.py",
    "📈 Visualizations":  "pages/viz.py",
    "🔮 Predict":        "pages/predict.py",
    "🧠 AI Agents":       "pages/agent.py",
    "💡 Insights":        "pages/insights.py",
}

PIPELINE_STEPS = list(PAGES.keys())


# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:0.75rem 0.5rem 0.5rem 0.75rem;'>
        <div style='font-size:0.95rem;font-weight:700;color:var(--text-primary);letter-spacing:-0.02em'>DataSense AI</div>
        <div style='font-size:0.65rem;color:var(--amber);margin-top:1px;letter-spacing:0.04em;text-transform:uppercase'>Core Dashboard</div>
    </div>
    <div style='height:15px'></div>
    """, unsafe_allow_html=True)

    # ── Pipeline Status Logic ───────────────────────────────────────
    has_data    = st.session_state["df"] is not None
    has_goals   = st.session_state["goals_confirmed"]
    has_ml      = st.session_state["ml_results"] is not None

    step_status = {
        "🏠 Home":           "done",
        "📂 Data Upload":    "done" if has_data else "current" if not has_data else "todo",
        "🎯 Insight Goals":  "done" if has_goals else "current" if has_data else "todo",
        "🔍 Data Mining":    "done" if st.session_state["profiling_df"] is not None else "todo",
        "🔧 Data Wrangling": "done" if st.session_state["wrangling_history"] else "todo",
        "📊 Analysis":       "todo",
        "🤖 ML Models":      "done" if has_ml else "todo",
        "📈 Visualizations": "todo",
        "🔮 Predict":        "done" if st.session_state["ml_results"] else "todo",
        "🧠 AI Agents":       "todo",
        "💡 Insights":       "done" if st.session_state["all_insights"] else "todo",
    }
    
    def format_nav(step):
        status = step_status.get(step, "todo")
        icon = step.split(" ", 1)[0] if " " in step else ""
        name = step.split(" ", 1)[-1] if " " in step else step
        
        if status == "done":
            return f"✓ {name}"
        elif status == "current":
            return f"→ {name}"
        else:
            return f"  {name}"

    # ── Grouped Navigation ──────────────────────────────────────────
    st.markdown("<div class='section-header' style='margin-top:0'>Pipeline Navigation</div>", unsafe_allow_html=True)
    
    # We'll use one radio for the whole thing to keep state simple, but style it as a singular list
    selected = st.radio("Nav", list(PAGES.keys()), format_func=format_nav, label_visibility="collapsed")
    
    st.markdown("<div style='margin: 1.5rem 0'></div>", unsafe_allow_html=True)

    # ── Live action log ───────────────────────────────────────────
    log_entries = st.session_state["action_log"]
    if log_entries:
        st.markdown("<div style='font-size:0.75rem; color:var(--text-muted); font-weight:600; text-transform:uppercase; margin-bottom:10px; letter-spacing:0.05em'>⚡ Recent Activity</div>", unsafe_allow_html=True)
        for entry in reversed(log_entries[-6:]):
            s = entry["status"]
            cls = "log-ok" if s == "✅" else "log-warn" if s == "⚠️" else "log-err"
            st.markdown(
                f"<div class='log-entry {cls}'>{entry['time']} — {entry['action']}</div>",
                unsafe_allow_html=True
            )

    # ── Dataset info ──────────────────────────────────────────────
    if st.session_state["df"] is not None:
        df = st.session_state["df"]
        st.markdown("---")
        st.markdown("**📦 Dataset**")
        st.markdown(f"`{df.shape[0]:,}` rows × `{df.shape[1]}` cols")
        if st.session_state["target_col"]:
            st.markdown(f"🎯 Target: `{st.session_state['target_col']}`")
        if st.session_state["goals"]:
            for g in st.session_state["goals"]:
                st.markdown(f"<span class='badge'>{g}</span>", unsafe_allow_html=True)

    # ── Sidebar Session Stats ──
    st.sidebar.markdown("---")
    with st.sidebar:
        st.markdown("**📊 Session Overview**")
        df_exists = st.session_state["df"] is not None
        rows = f"{st.session_state['df'].shape[0]:,}" if df_exists else "0"
        cols = f"{st.session_state['df'].shape[1]}" if df_exists else "0"
        
        st.markdown(f"""
        <div style='background:#12141c;border:1px solid #2a2d3d;border-radius:8px;padding:10px;font-size:0.8rem'>
            Rows × Cols: <b>{rows} × {cols}</b><br>
            Active Goals: <b>{len(st.session_state['goals'])}</b><br>
            Best Model: <b>{st.session_state.get('best_model', 'None')}</b>
        </div>
        """, unsafe_allow_html=True)


# ── Home Page Logic ──────────────────────────────────────────────────
def render_home():
    st.markdown("# DataSense AI")
    st.markdown("### *Your Automated Data Science Co-Pilot*")

    st.markdown("""
    <div class='narrate-box'>
    <b>What is DataSense AI?</b><br>
    A platform that automates the full data science lifecycle — from raw files to actionable insights.
    The machine handles the computation; <em>you</em> bring domain knowledge, judgment, and context.
    Every step is explained. Nothing is a black box.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Voice Onboarding ──
    if "voice_engine" not in st.session_state or st.session_state["voice_engine"] is None:
        st.session_state["voice_engine"] = VoiceOnboardingEngine()

    engine = st.session_state["voice_engine"]

    if not st.session_state["voice_onboarding_active"]:
        st.markdown("###  Quick Start: Voice Requirements Gathering")
        st.markdown("Unlock the full power of DataSense AI by starting with a brief interactive interview.")
        if st.button(" Start Voice Onboarding", type="primary", use_container_width=True):
            st.session_state["voice_onboarding_active"] = True
            log("Voice onboarding started")
            st.rerun()
    else:
        st.markdown("###  Virtual Co-Pilot Interview")
        q = engine.get_next_question()
        
        if q:
            st.markdown(f"<div class='narrate-box'><b>Co-Pilot:</b> {q}</div>", unsafe_allow_html=True)
            
        # ── REAL-TIME VOICE BRIDGE ──
        st.markdown("<div style='font-size:0.8rem; color:var(--text-muted); margin-bottom:5px'>🎤 Click to start. Words will appear live as you speak.</div>", unsafe_allow_html=True)
        
        # We use a custom HTML/JS bridge for the "Wow" real-time factor
        from streamlit_javascript import st_javascript
        
        # Unique key for this step's component
        comp_id = f"stt_{engine.current_step}"
        
        st.components.v1.html(f"""
            <div id="root-{comp_id}" style="color: #e8a020; font-family: monospace;">
                <button id="btn-{comp_id}" style="
                    background: #1a1812; 
                    color: #e8a020; 
                    border: 1px solid #e8a020; 
                    padding: 8px 16px; 
                    border-radius: 4px; 
                    cursor: pointer;
                    width: 100%;
                    font-weight: bold;
                    margin-bottom: 10px;
                ">⏺ Start Dictation</button>
                <div id="monitor-{comp_id}" style="
                    border: 1px dashed #2e2b22; 
                    padding: 10px; 
                    min-height: 50px; 
                    background: #000;
                    font-size: 14px;
                "><i>Listening for your voice...</i></div>
            </div>

            <script>
                const btn = document.getElementById('btn-{comp_id}');
                const monitor = document.getElementById('monitor-{comp_id}');
                let recognizing = false;
                
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                
                if (!SpeechRecognition) {{
                    monitor.innerHTML = "⚠️ Real-time voice not supported in this browser. Please type below.";
                    btn.style.display = 'none';
                }} else {{
                    const recognition = new SpeechRecognition();
                    recognition.continuous = true;
                    recognition.interimResults = true;
                    recognition.lang = 'en-US';

                    recognition.onstart = () => {{
                        recognizing = true;
                        btn.innerHTML = "⏹ Stop Dictation";
                        btn.style.background = "#c0544a";
                        btn.style.color = "#fff";
                    }};

                    recognition.onresult = (event) => {{
                        let interimTranscript = '';
                        let finalTranscript = '';
                        for (let i = event.resultIndex; i < event.results.length; ++i) {{
                            if (event.results[i].isFinal) {{
                                finalTranscript += event.results[i][0].transcript;
                            }} else {{
                                interimTranscript += event.results[i][0].transcript;
                            }}
                        }}
                        monitor.innerHTML = '<b>' + finalTranscript + '</b><span style="color:#665e4e">' + interimTranscript + '</span>';
                        // Send back to parent if finished? 
                        // For simplicity, we let the user see it and then we use a bridge.
                        window.parent.postMessage({{
                            type: 'stt_update',
                            text: finalTranscript + interimTranscript,
                            id: '{comp_id}'
                        }}, '*');
                    }};

                    recognition.onend = () => {{
                        recognizing = false;
                        btn.innerHTML = "⏺ Start Dictation";
                        btn.style.background = "#1a1812";
                        btn.style.color = "#e8a020";
                    }};

                    btn.onclick = () => {{
                        if (recognizing) {{
                            recognition.stop();
                        }} else {{
                            recognition.start();
                        }}
                    }};
                }}
            </script>
        """, height=160)

        # Bridge the JS value back to session state using a small streamlit-javascript hack
        # This catches the latest message from our component
        js_code = f"""
            (function() {{
                let val = "";
                window.addEventListener('message', function(e) {{
                    if (e.data.type === 'stt_update' && e.data.id === '{comp_id}') {{
                        window.latest_stt = e.data.text;
                    }}
                }});
                return window.latest_stt || "";
            }})()
        """
        captured_text = st_javascript(js_code)
        
        user_input = st.text_input("...or edit/type your response:", value=captured_text if captured_text else "", key=f"voice_input_{engine.current_step}", placeholder="e.g. 'I want to predict credit card fraud'...")
        
        # ── AI Auto-Refine ──
        if user_input:
            if st.button("✨ Refine with AI", help="Fix grammar & technical terms"):
                with st.spinner("Refining..."):
                    refined = correction_agent(user_input, context=f"Context: Co-Pilot asked: {q}")
                    # Update session state for the text input's default value
                    # We can't easily update st.text_input value once rendered without a rerun or a key change
                    st.session_state[f"voice_input_{engine.current_step}"] = refined
                    st.rerun()

        if st.button(" Next Step", type="primary"):
            final_input = user_input if user_input else captured_text
            if final_input:
                engine.process_response(final_input)
                st.session_state["voice_transcript"].append({"q": q, "a": final_input})
                log(f"Voice Step {engine.current_step}: {final_input[:20]}...")
                st.rerun()
            else:
                st.warning("Please record your voice or type a message to proceed.")
        else:
            st.success(" Voice Interview Complete!")
            summary = engine.get_summary()
            st.markdown(f"<div class='human-note'>{summary}</div>", unsafe_allow_html=True)
            
            mapped_data = engine.map_to_session_state()
            for k, v in mapped_data.items():
                st.session_state[k] = v
                
            if st.button(" Finish and Start Mining"):
                st.session_state["voice_onboarding_active"] = False
                st.session_state["goals_confirmed"] = True
                log("Voice requirements confirmed")
                st.switch_page("pages/mining.py")

    st.markdown("---")

    # ── How it works ──
    st.markdown("##  How It Works")
    steps = [
        ("📂", "1. Upload Data", "Upload one or more CSV, Excel, JSON, or Parquet files. Merge them if needed."),
        ("🎯", "2. Set Your Goals", "Tell us what you want to find — predict, explore, diagnose, or detect anomalies."),
        ("🔍", "3. Data Mining", "Auto-profile every column. Find missing values, outliers, and correlations."),
        ("🔧", "4. Wrangle", "Clean and transform your data interactively. Every change is tracked."),
        ("📊", "5. Analyze", "Run statistical tests. Get plain-English interpretations of every result."),
        ("🤖", "6. ML Models", "Auto-select and train multiple models. Understand why each was chosen."),
        ("📈", "7. Visualize", "Explore interactive charts. Flag anything interesting."),
        ("💡", "8. Insights", "Read your personalized report — machine findings + your human observations."),
    ]

    cols = st.columns(4)
    for i, (icon, title, desc) in enumerate(steps):
        with cols[i % 4]:
            st.markdown(f"""
            <div class='ds-card' style='text-align:center;min-height:140px'>
                <div style='font-size:2rem'>{icon}</div>
                <div style='font-weight:700;color:#9f9bff;margin:0.3rem 0;font-size:0.9rem'>{title}</div>
                <div style='font-size:0.8rem;color:#aaa'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Demo Datasets ──
    st.markdown("##  Try a Demo Dataset")
    st.markdown("Don't have data handy? Load one of these classic datasets to see the platform in action.")

    c1, c2, c3 = st.columns(3)

    def load_demo(name):
        from sklearn import datasets
        if name == "Titanic":
            df = pd.read_csv("https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv")
        elif name == "Iris":
            data = datasets.load_iris()
            df = pd.DataFrame(data.data, columns=data.feature_names)
            df['target'] = data.target
        elif name == "California":
            data = datasets.fetch_california_housing()
            df = pd.DataFrame(data.data, columns=data.feature_names)
            df['target'] = data.target
        
        st.session_state["df"] = df
        st.session_state["original_df"] = df.copy()
        st.session_state["data_loaded"] = True
        st.session_state["goals"] = [f"Explore {name} dataset", "Build predictive model"]
        st.session_state["goals_confirmed"] = True
        log(f"Loaded demo dataset: {name}")
        st.switch_page("pages/mining.py")

    if c1.button(" Titanic (Classification)", use_container_width=True):
        load_demo("Titanic")
    if c2.button(" Iris (Multi-class)", use_container_width=True):
        load_demo("Iris")
    if c3.button(" California Housing (Regression)", use_container_width=True):
        load_demo("California")

    st.markdown("---")

    # ── Philosophy ──
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("###  Human ↔ Machine Collaboration")
        st.markdown("""
        Data science isn't fully automatable — and we don't pretend it is.
        -  **Machine**: crunches numbers, detects patterns, trains models
        -  **You**: provide domain context, validate findings, flag anomalies, write hypotheses
        -  **Together**: produce insights that are both statistically sound and practically meaningful
        """)

    with col2:
        st.markdown("###  Full Transparency")
        st.markdown("""
        Every automated action comes with:
        - **Why** it was done (AutoNarrate callouts)
        - **What it means** in plain English
        - **Your annotation panel** to add observations
        - **Flag buttons** on every chart and result
        - A final **Session Report** that combines machine + human findings
        """)

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:#555;font-size:0.82rem'>"
        "Use the sidebar to navigate. Start with <b>Data Upload</b>."
        "</div>",
        unsafe_allow_html=True
    )

# ── Route to page ────────────────────────────────────────────────────
import runpy, types

if selected == "🏠 Home":
    render_home()
else:
    page_file = os.path.join(os.path.dirname(__file__), PAGES[selected])
    if os.path.exists(page_file):
        page_globals = {
            "__name__": "__main__",
            "__file__": page_file,
            "log": log,
        }
        try:
            runpy.run_path(page_file, init_globals=page_globals, run_name="__main__")
        except SystemExit:
            pass  # st.stop() raises SystemExit
        except Exception as e:
            st.error(f"Page error: {e}")
            import traceback
            with st.expander("Stack trace"):
                st.code(traceback.format_exc())
    else:
        st.error(f"Page file not found: {page_file}")

# ── Next Step Navigation ──────────────────────────────────────────────
st.markdown("---")
page_order = [
    "🏠 Home", "📂 Data Upload", "🎯 Insight Goals", "🔍 Data Mining",
    "🔧 Data Wrangling", "📊 Analysis", "🤖 ML Models", "📈 Visualizations",
    "🔮 Predict", "🧠 AI Agents", "💡 Insights"
]

if selected in page_order and selected != page_order[-1]:
    idx = page_order.index(selected)
    nxt = page_order[idx + 1]
    col_l, col_r = st.columns([4, 1])
    if col_r.button(f"Next: {nxt} ▶", use_container_width=True):
        try:
            st.switch_page(PAGES[nxt])
        except Exception:
            st.info(f"Navigate to **{nxt}** in the sidebar.")
