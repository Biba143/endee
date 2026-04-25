"""InsightAI — Premium UI"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from app import InsightAI

st.set_page_config(
    page_title="InsightAI", page_icon="🧠",
    layout="wide", initial_sidebar_state="collapsed"
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* === RESET === */
*, *::before, *::after { box-sizing: border-box; }
html, body { margin:0; padding:0; }
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    font-family:'Inter',sans-serif !important;
    background:#0a0a0f !important;
    color:#e2e8f0 !important;
}

/* === HIDE ALL STREAMLIT CHROME === */
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
header[data-testid="stHeader"],
[data-testid="collapsedControl"],
[data-testid="stSidebar"],
#MainMenu, footer { display:none !important; }

/* === ZERO OUT EVERY CONTAINER LAYER === */
[data-testid="stApp"]                > div,
[data-testid="stAppViewContainer"]   > section,
[data-testid="stMain"],
[data-testid="stMain"]               > div,
[data-testid="stMainBlockContainer"],
[data-testid="stVerticalBlock"],
[data-testid="stVerticalBlock"]      > div,
.block-container,
.main                                > div {
    padding:0 !important;
    margin:0 !important;
    max-width:100% !important;
}

/* === HERO FULL-BLEED === */
.hero-bleed {
    /* break out of any remaining parent padding */
    position:relative;
    left:50%; transform:translateX(-50%);
    width:100vw;
    /* no height set here — iframe inside controls it */
    overflow:hidden;
    display:block;
    line-height:0;
}
.hero-bleed iframe {
    width:100vw;
    height:100vh;
    border:none;
    display:block;
}

/* === APP DASHBOARD CARD === */
.app-card {
    background:rgba(255,255,255,0.03);
    border:1px solid rgba(255,255,255,0.07);
    border-radius:20px;
    padding:2rem 2.4rem 2.4rem;
    margin:2rem auto;
    max-width:1100px;
    box-shadow:0 8px 40px rgba(0,0,0,.4);
}

/* === SECTION LABELS === */
.sec-label {
    display:inline-flex; align-items:center; gap:.5rem;
    font-size:.68rem; font-weight:700; letter-spacing:.12em;
    text-transform:uppercase; color:#64748b; margin-bottom:.8rem;
}
.sec-num {
    width:18px; height:18px; border-radius:50%;
    background:linear-gradient(135deg,#818cf8,#34d399);
    display:inline-flex; align-items:center; justify-content:center;
    font-size:.6rem; font-weight:800; color:#0a0a0f;
}

/* === FILE UPLOADER === */
[data-testid="stFileUploader"] {
    background:rgba(255,255,255,0.02) !important;
    border:2px dashed rgba(129,140,248,0.25) !important;
    border-radius:12px !important;
}
[data-testid="stFileUploaderDropzone"] { background:transparent !important; }

/* === BUTTONS === */
.stButton > button {
    border-radius:10px !important; font-weight:600 !important;
    font-size:.88rem !important; transition:all .2s !important; border:none !important;
}
.stButton > button[kind="primary"] {
    background:linear-gradient(135deg,#818cf8,#6366f1) !important;
    color:#fff !important; box-shadow:0 4px 20px rgba(99,102,241,.35) !important;
}
.stButton > button[kind="primary"]:hover {
    transform:translateY(-1px) !important;
    box-shadow:0 6px 28px rgba(99,102,241,.5) !important;
}
.stButton > button[kind="secondary"] {
    background:rgba(255,255,255,0.05) !important;
    color:#94a3b8 !important;
    border:1px solid rgba(255,255,255,0.08) !important;
}

/* === TEXT INPUT === */
.stTextInput > div > div > input {
    background:rgba(255,255,255,0.04) !important;
    border:1px solid rgba(255,255,255,0.1) !important;
    border-radius:12px !important; color:#f1f5f9 !important;
    font-size:1rem !important; padding:.75rem 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color:#818cf8 !important;
    box-shadow:0 0 0 3px rgba(129,140,248,.15) !important;
}
.stTextInput > div > div > input::placeholder { color:#475569 !important; }

/* === DIVIDER === */
.fancy-divider {
    height:1px;
    background:linear-gradient(90deg,transparent,rgba(129,140,248,.3),transparent);
    margin:1.5rem 0; border:none;
}

/* === RESULT CARDS === */
.sec-head {
    font-size:.68rem; font-weight:700; letter-spacing:.12em;
    text-transform:uppercase; color:#475569;
    margin:1.2rem 0 .5rem; display:flex; align-items:center; gap:.4rem;
}
.rcard {
    border-radius:10px; padding:.8rem 1rem;
    margin-bottom:.45rem; line-height:1.6;
    font-size:.88rem; color:#cbd5e1;
    border:1px solid transparent; transition:transform .15s;
}
.rcard:hover { transform:translateX(3px); }
.rcard-obs    { background:rgba(129,140,248,.08); border-color:rgba(129,140,248,.2); }
.rcard-issue  { background:rgba(251,191,36,.07);  border-color:rgba(251,191,36,.2);  color:#fde68a; }
.rcard-cause  { background:rgba(239,68,68,.07);   border-color:rgba(239,68,68,.2);   color:#fca5a5; }
.rcard-plan   { background:rgba(52,211,153,.07);  border-color:rgba(52,211,153,.2);  color:#6ee7b7; }
.rcard-pillar { background:rgba(56,189,248,.07);  border-color:rgba(56,189,248,.2);  color:#7dd3fc; }
.rcard-metric { background:rgba(192,132,252,.07); border-color:rgba(192,132,252,.2); color:#d8b4fe; }
.rcard-num    { font-size:.75rem; font-weight:700; color:#64748b; margin-right:.5rem; }

/* === INSIGHT BOX === */
.insight-box {
    background:linear-gradient(135deg,rgba(129,140,248,.1),rgba(52,211,153,.08));
    border:1px solid rgba(129,140,248,.2); border-radius:12px;
    padding:1rem 1.2rem; font-size:.9rem; line-height:1.7; color:#cbd5e1;
    position:relative; overflow:hidden;
}
.insight-box::before {
    content:'"'; position:absolute; top:-10px; left:12px;
    font-size:5rem; color:rgba(129,140,248,.1);
    font-family:Georgia,serif; line-height:1;
}

/* === BADGES === */
.badge {
    display:inline-flex; align-items:center; gap:.3rem;
    padding:3px 12px; border-radius:20px;
    font-size:.72rem; font-weight:700; letter-spacing:.05em; text-transform:uppercase;
}
.b-why      { background:rgba(239,68,68,.15);  color:#fca5a5; border:1px solid rgba(239,68,68,.25); }
.b-strategy { background:rgba(52,211,153,.15); color:#6ee7b7; border:1px solid rgba(52,211,153,.25); }
.b-improve  { background:rgba(129,140,248,.15);color:#a5b4fc; border:1px solid rgba(129,140,248,.25); }
.b-summary  { background:rgba(148,163,184,.12);color:#94a3b8; border:1px solid rgba(148,163,184,.2); }
.b-domain   { background:rgba(251,191,36,.12); color:#fcd34d; border:1px solid rgba(251,191,36,.2); }

/* === SOURCE PILLS === */
.src-pill {
    display:inline-flex; align-items:center; gap:.3rem;
    background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.08);
    border-radius:8px; padding:3px 10px; font-size:.78rem; color:#64748b; margin:2px;
}
.src-score { color:#34d399; font-weight:600; }

/* === DOC PILLS === */
.doc-pill {
    display:inline-flex; align-items:center; gap:.3rem;
    background:rgba(129,140,248,.12); border:1px solid rgba(129,140,248,.25);
    border-radius:8px; padding:3px 12px; font-size:.8rem; color:#a5b4fc; margin:2px;
}

/* === HOW-IT-WORKS CARDS === */
.how-card {
    background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06);
    border-radius:14px; padding:1.4rem; text-align:center;
}
.how-icon  { font-size:2rem; margin-bottom:.6rem; }
.how-title { font-size:.9rem; font-weight:700; color:#e2e8f0; margin-bottom:.3rem; }
.how-desc  { font-size:.8rem; color:#64748b; line-height:1.5; }

/* === EMPTY STATE === */
.empty-wrap { text-align:center; padding:3rem 1rem; }
.empty-icon  { font-size:3rem; margin-bottom:.8rem; }
.empty-title { font-size:1.3rem; font-weight:700; color:#334155; margin-bottom:.4rem; }
.empty-sub   { font-size:.9rem; color:#475569; line-height:1.6; }

/* === MISC === */
::-webkit-scrollbar { width:6px; }
::-webkit-scrollbar-track { background:#0a0a0f; }
::-webkit-scrollbar-thumb { background:#334155; border-radius:3px; }
.stProgress > div > div { background:linear-gradient(90deg,#818cf8,#34d399) !important; }
[data-testid="stExpander"] {
    background:rgba(255,255,255,0.02) !important;
    border:1px solid rgba(255,255,255,0.06) !important;
    border-radius:12px !important;
}
[data-testid="stAlert"] { border-radius:10px !important; }
.chunk-box {
    background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06);
    border-radius:8px; padding:.8rem 1rem; font-size:.83rem; color:#94a3b8;
    margin-bottom:.5rem; line-height:1.5;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
def _init():
    for k, v in {
        "ai":None,"connected":False,"ingested_docs":[],
        "last_result":None,"history":[],"pending_query":"",
        "top_k":10,"doc_filter":None,"show_chunks":False,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v
_init()

# ── Auto-connect ───────────────────────────────────────────────────────────────
if not st.session_state["connected"]:
    try:
        _ai = InsightAI(
            endee_host=os.getenv("ENDEE_HOST","http://localhost:8080"),
            index_name=os.getenv("ENDEE_INDEX","insightai_docs"),
            auth_token=os.getenv("NDD_AUTH_TOKEN","") or None,
        )
        if _ai.setup():
            st.session_state["ai"] = _ai
            st.session_state["connected"] = True
    except Exception:
        pass

connected = st.session_state["connected"]

# ══════════════════════════════════════════════════════════════════════════════
# HERO — full-bleed WebGL shader (no black bars)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero-bleed">
  <iframe src="http://localhost:3000" scrolling="no"></iframe>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# APP DASHBOARD — single unified card
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="app-card">', unsafe_allow_html=True)

# ── Status bar inside the card ────────────────────────────────────────────────
stats     = st.session_state["ai"].get_index_stats() if connected else {}
vec_count = stats.get("total_elements", 0) if stats else 0
doc_count = len(st.session_state["ingested_docs"])

dot_color = "#22c55e" if connected else "#ef4444"
status_txt = (
    f"Connected · {doc_count} doc{'s' if doc_count!=1 else ''}"
    + (f" · {vec_count:,} vectors" if vec_count else "")
    if connected else "Not connected — start Endee on port 8080"
)
st.markdown(
    f'<div style="display:flex;align-items:center;gap:.5rem;'
    f'font-size:.8rem;color:#64748b;margin-bottom:1.5rem;">'
    f'<div style="width:8px;height:8px;border-radius:50%;background:{dot_color};'
    f'box-shadow:0 0 8px {dot_color}88;flex-shrink:0;"></div>'
    f'<span>{status_txt}</span></div>',
    unsafe_allow_html=True,
)

# ── STEP 1: Upload ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="sec-label">
  <span class="sec-num">1</span> Upload Documents
</div>""", unsafe_allow_html=True)

up_col, btn_col = st.columns([4, 1])
with up_col:
    uploaded = st.file_uploader(
        "drop", type=["pdf","txt"], accept_multiple_files=True,
        label_visibility="collapsed",
    )
with btn_col:
    st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
    ingest_btn = st.button("📥 Load", use_container_width=True,
                           type="primary", disabled=not connected)

if st.session_state["ingested_docs"]:
    pills = "".join(f'<span class="doc-pill">📄 {d}</span>'
                    for d in st.session_state["ingested_docs"])
    dc, pc = st.columns([1,7])
    with pc:
        st.markdown(f'<div style="margin-top:.4rem">{pills}</div>', unsafe_allow_html=True)
    with dc:
        if st.button("🗑️ Clear", key="clear_btn", use_container_width=True):
            st.session_state["ai"].clear_index()
            st.session_state["ingested_docs"] = []
            st.session_state["last_result"] = None
            st.rerun()

if ingest_btn:
    if not uploaded:
        st.warning("Select at least one file first.")
    else:
        # Always wipe the index before loading new documents
        # so old uploads never pollute new queries
        with st.spinner("Clearing previous data…"):
            st.session_state["ai"].clear_index()
        st.session_state["ingested_docs"] = []
        st.session_state["last_result"] = None
        st.session_state["doc_filter"] = None

        bar = st.progress(0, text="Processing…")
        newly_loaded = []
        for i, f in enumerate(uploaded):
            bar.progress(i/len(uploaded), text=f"Processing {f.name}…")
            res = st.session_state["ai"].ingest_document(
                file_source=f, doc_name=f.name,
                file_type="pdf" if f.name.lower().endswith(".pdf") else "text",
                chunk_size=400, overlap=50,
            )
            if res["status"] == "success":
                st.success(f"✅ **{f.name}** — {res['chunks']} chunks stored in Endee")
                if f.name not in st.session_state["ingested_docs"]:
                    st.session_state["ingested_docs"].append(f.name)
                newly_loaded.append(f.name)
            else:
                st.error(f"❌ **{f.name}**: {res['message']}")
        bar.progress(1.0, text="Done!")
        # Auto-set filter to the single loaded doc
        if len(newly_loaded) == 1:
            st.session_state["doc_filter"] = newly_loaded[0]
        st.rerun()

st.markdown('<hr class="fancy-divider">', unsafe_allow_html=True)

# ── STEP 2: Ask ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="sec-label" style="margin-top:.2rem">
  <span class="sec-num">2</span> Ask a Question
</div>""", unsafe_allow_html=True)

# Clean integrated query box — no iframe, no black box
st.markdown("""
<style>
/* Query box container */
.query-wrap {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.2rem 1.4rem 1rem;
    margin-bottom: .8rem;
    transition: border-color .2s;
}
.query-wrap:focus-within {
    border-color: rgba(129,140,248,0.45);
    box-shadow: 0 0 0 3px rgba(129,140,248,0.08);
}
/* Override Streamlit text input inside query-wrap */
.query-wrap .stTextInput > div > div > input {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    font-size: 1.05rem !important;
    color: #f1f5f9 !important;
    padding: .4rem 0 !important;
    box-shadow: none !important;
}
.query-wrap .stTextInput > div > div > input::placeholder {
    color: #334155 !important;
    font-size: 1rem !important;
}
/* Example chip buttons */
.stButton > button.chip-btn {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    color: #64748b !important;
    font-size: .8rem !important;
    border-radius: 20px !important;
    padding: .3rem .8rem !important;
    font-weight: 500 !important;
}
.stButton > button.chip-btn:hover {
    background: rgba(129,140,248,0.1) !important;
    border-color: rgba(129,140,248,0.3) !important;
    color: #a5b4fc !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="query-wrap">', unsafe_allow_html=True)
q_col, btn_col = st.columns([6, 1])
with q_col:
    query = st.text_input(
        "q_fb",
        value=st.session_state.get("pending_query", ""),
        placeholder='Ask anything — "Why did I score less?", "How can I improve?", "What strategy should I use?"',
        label_visibility="collapsed",
        key="query_box",
    )
with btn_col:
    st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
    run_btn = st.button("Analyse →", type="primary",
                        use_container_width=True, disabled=not connected, key="run_btn")
st.markdown('</div>', unsafe_allow_html=True)

# Example chips — clean pill row
st.markdown('<div style="font-size:.68rem;font-weight:700;letter-spacing:.1em;'
            'text-transform:uppercase;color:#334155;margin:.6rem 0 .4rem">✦ Try an example</div>',
            unsafe_allow_html=True)
examples = [
    ("📉", "Why did I score less in maths?"),
    ("🎯", "What strategy should I follow?"),
    ("📈", "How can I improve my performance?"),
    ("📋", "Summarise my academic report"),
    ("🏃", "Why did the team lose the match?"),
    ("💼", "How can I strengthen my resume?"),
]
chip_cols = st.columns(len(examples))
clicked_example = None
for idx, (col, (icon, ex)) in enumerate(zip(chip_cols, examples)):
    with col:
        if st.button(f"{icon} {ex}", key=f"chip_{idx}", use_container_width=True):
            clicked_example = ex

with st.expander("⚙️ Advanced options", expanded=False):
    oc1, oc2, oc3 = st.columns(3)
    with oc1:
        df = st.selectbox("Filter by document",
                          ["All documents"] + st.session_state["ingested_docs"])
        st.session_state["doc_filter"] = None if df == "All documents" else df
    with oc2:
        st.session_state["top_k"] = st.slider("Chunks to retrieve", 3, 20, 10)
    with oc3:
        st.session_state["show_chunks"] = st.checkbox("Show context chunks", value=False)

# ── Run analysis ───────────────────────────────────────────────────────────────
active_query = clicked_example or (query if run_btn else None) or st.session_state.get("pending_query", "") or None
if st.session_state.get("pending_query"):
    st.session_state["pending_query"] = ""

if active_query and connected:
    last = st.session_state.get("last_result") or {}
    if last.get("query") != active_query:
        if active_query not in st.session_state["history"]:
            st.session_state["history"].append(active_query)

        # Determine filter: explicit manual filter > single loaded doc > no filter
        active_filter = st.session_state["doc_filter"]
        loaded_docs = st.session_state["ingested_docs"]
        if not active_filter and len(loaded_docs) == 1:
            active_filter = loaded_docs[0]

        if not loaded_docs:
            st.warning("⚠️ No documents loaded. Please upload and click **Load** first.")
        else:
            with st.spinner("🔍 Retrieving from Endee · Reasoning with Llama 3.3 70B…"):
                result = st.session_state["ai"].query(
                    question=active_query,
                    k=st.session_state["top_k"],
                    filter_doc=active_filter,
                )
                st.session_state["last_result"] = result
            st.rerun()
elif active_query and not connected:
    st.warning("⚠️ Endee is not connected.")

st.markdown('<hr class="fancy-divider">', unsafe_allow_html=True)

# ── Results ────────────────────────────────────────────────────────────────────
result = st.session_state.get("last_result")

def sec(icon, label):
    st.markdown(f'<div class="sec-head"><span style="font-size:.95rem">{icon}</span>{label}</div>',
                unsafe_allow_html=True)

def rcard(text, style="obs", num=None):
    prefix = f'<span class="rcard-num">{num}.</span>' if num else "• "
    st.markdown(f'<div class="rcard rcard-{style}">{prefix}{text}</div>',
                unsafe_allow_html=True)

if result:
    intent = result.get("intent","summary")
    domain = result.get("domain","general")

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;margin-bottom:.5rem">'
        f'<span class="badge b-{intent}">{intent.upper()}</span>'
        f'<span class="badge b-domain">{domain.upper()}</span>'
        f'<span style="color:#64748b;font-size:.88rem;font-style:italic">"{result.get("query","")}"</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"🗂 {result.get('context_summary','')}")

    left, right = st.columns([3,2], gap="large")

    with left:
        obs = result.get("analysis",[])
        if obs:
            sec("🔍","Analysis")
            for o in obs: rcard(o,"obs")

        issues = result.get("key_issues",[])
        no_iss = not issues or issues==["No specific issues identified from the available context."]
        sec("📊","Key Issues")
        if no_iss: st.success("No critical issues identified.")
        else:
            for iss in issues: rcard(iss,"issue")

        if intent=="why":
            causes = result.get("root_causes",[])
            if causes:
                sec("🔬","Root Causes")
                for i,rc in enumerate(causes,1): rcard(rc,"cause",num=i)
            factors = result.get("contributing_factors",[])
            if factors:
                sec("🔗","Contributing Factors")
                for f in factors:
                    st.markdown(f'<div style="padding:.3rem 0 .3rem 1rem;color:#94a3b8;'
                                f'font-size:.87rem;border-left:2px solid rgba(148,163,184,.2)">→ {f}</div>',
                                unsafe_allow_html=True)

        if intent=="strategy":
            pillars = result.get("strategic_pillars",[])
            if pillars:
                sec("🏛️","Strategic Pillars")
                for p in pillars: rcard(p,"pillar")
            tactical = result.get("tactical_steps",[])
            if tactical:
                sec("⚡","Tactical Steps")
                for i,t in enumerate(tactical,1): rcard(t,"obs",num=i)

        if intent=="improve":
            short = result.get("short_term_goals",[])
            if short:
                sec("📅","Short-Term Goals (1–4 weeks)")
                for g in short: rcard(g,"pillar")
            long_ = result.get("long_term_strategy",[])
            if long_:
                sec("🗺️","Long-Term Strategy (1–3 months)")
                for s in long_: rcard(s,"obs")

        if intent=="summary":
            hl = result.get("highlights",[])
            if hl:
                sec("✨","Highlights")
                for h in hl: rcard(h,"pillar")

    with right:
        insight = result.get("strategy_insight","")
        if insight:
            sec("🧠","Strategy Insight")
            st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)

        plan = result.get("improvement_plan",[])
        if plan:
            sec("🚀","Improvement Plan")
            for i,step in enumerate(plan,1): rcard(step,"plan",num=i)

        if intent=="improve":
            metrics = result.get("success_metrics",[])
            if metrics:
                sec("📏","Success Metrics")
                for m in metrics: rcard(m,"metric")
            prios = result.get("priority_areas",[])
            if prios:
                sec("🎯","Priority Areas")
                for p in prios:
                    st.markdown(f'<div style="padding:.3rem 0 .3rem 1rem;color:#a5b4fc;'
                                f'font-size:.87rem;border-left:2px solid rgba(129,140,248,.3)">'
                                f'<b>{p}</b></div>', unsafe_allow_html=True)

        numerics = result.get("numeric_findings",[])
        if numerics:
            sec("📊","Numeric Findings")
            for nf in numerics:
                st.markdown(f'<div class="rcard rcard-metric">'
                            f'<b>{nf.get("value","")} {nf.get("unit","")}</b>'
                            f'<span style="color:#64748b;font-size:.82rem"> — {nf.get("context","")[:70]}</span>'
                            f'</div>', unsafe_allow_html=True)

        sources = result.get("sources",[])
        if sources:
            sec("📎","Sources")
            pills = "".join(
                f'<span class="src-pill">📄 {s.get("doc_name","?")} p.{s.get("page","?")} '
                f'<span class="src-score">{s.get("score",0):.3f}</span></span>'
                for s in sources
            )
            st.markdown(f'<div style="margin-top:.3rem">{pills}</div>', unsafe_allow_html=True)

    if st.session_state["show_chunks"]:
        chunks_data = result.get("_chunks",[])
        with st.expander(f"📚 Context Chunks ({len(chunks_data)})", expanded=False):
            for i,ch in enumerate(chunks_data,1):
                text = ch.get("text","")
                st.markdown(
                    f'<div class="chunk-box"><b>#{i}</b> · 📄 {ch.get("doc_name","?")} '
                    f'p.{ch.get("page","?")} · score {ch.get("score",0):.3f}<br><br>'
                    f'{text[:400]}{"…" if len(text)>400 else ""}</div>',
                    unsafe_allow_html=True)

    with st.expander("🔩 Raw JSON", expanded=False):
        st.code(json.dumps({k:v for k,v in result.items() if k!="_chunks"},
                           indent=2, default=str), language="json")

    if st.session_state["history"]:
        with st.expander("🕑 Query History", expanded=False):
            for i,q in enumerate(reversed(st.session_state["history"][-8:])):
                hc1,hc2 = st.columns([5,1])
                with hc1:
                    st.markdown(f'<span style="color:#64748b;font-size:.88rem">{q}</span>',
                                unsafe_allow_html=True)
                with hc2:
                    if st.button("↩",key=f"rerun_{i}"):
                        st.session_state["pending_query"] = q
                        st.session_state["last_result"] = None
                        st.rerun()

else:
    # Welcome / empty state
    if not st.session_state["ingested_docs"]:
        st.markdown('<div style="text-align:center;margin-bottom:1.5rem;font-size:.7rem;'
                    'font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#475569">'
                    'How it works</div>', unsafe_allow_html=True)
        hw1,hw2,hw3,hw4 = st.columns(4)
        for col,icon,title,desc in [
            (hw1,"📄","Upload","Drop any PDF or text file — marksheet, report, resume, or notes."),
            (hw2,"🗄️","Index","Text is chunked, embedded, and stored in Endee vector database."),
            (hw3,"🔍","Retrieve","Your question is embedded and matched against stored vectors."),
            (hw4,"🧠","Reason","Llama 3.3 70B reasons over the context and returns structured output."),
        ]:
            with col:
                st.markdown(f'<div class="how-card"><div class="how-icon">{icon}</div>'
                            f'<div class="how-title">{title}</div>'
                            f'<div class="how-desc">{desc}</div></div>',
                            unsafe_allow_html=True)
        st.markdown('<div class="empty-wrap"><div class="empty-icon">☝️</div>'
                    '<div class="empty-title">Start by uploading a document</div>'
                    '<div class="empty-sub">Drop a PDF or text file above, then ask anything about it.</div>'
                    '</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-wrap"><div class="empty-icon">💬</div>'
                    '<div class="empty-title">Documents loaded — ask a question</div>'
                    '<div class="empty-sub">Type in the box above or click an example chip.</div>'
                    '</div>', unsafe_allow_html=True)

# Close the app-card div
st.markdown('</div>', unsafe_allow_html=True)
