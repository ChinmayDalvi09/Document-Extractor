"""
Premium Streamlit UI for the Intelligent Document Extraction Platform.
"""

import io
import streamlit as st
import requests
import pandas as pd

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DocExtract AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = "http://127.0.0.1:8000"

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Hide Streamlit default header, menu, and footer */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Gradient header */
    .hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .hero h1 { color: #e94560; font-size: 2.4rem; font-weight: 700; margin: 0; }
    .hero p  { color: #a0aec0; font-size: 1.05rem; margin-top: 0.5rem; }

    /* Badge */
    .badge {
        display: inline-block;
        padding: 0.3rem 0.9rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    .badge-aadhaar   { background:#2d6a4f; color:#b7e4c7; }
    .badge-passport  { background:#1e3a5f; color:#90cdf4; }
    .badge-driving   { background:#4a1942; color:#f9a8d4; }
    .badge-invoice   { background:#4a3000; color:#fcd34d; }
    .badge-unknown   { background:#374151; color:#d1d5db; }

    /* Card */
    .card {
        background: #1e2a3a;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .card h3 { color: #e94560; margin-top: 0; }

    /* Status dot */
    .dot-green { color: #48bb78; font-size: 1.2rem; }
    .dot-red   { color: #fc8181; font-size: 1.2rem; }

    /* Field table */
    .field-key   { color: #90cdf4; font-weight: 600; }
    .field-value { color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)


# ── Helper: API status ────────────────────────────────────────────────────────
def check_api() -> bool:
    try:
        r = requests.get(f"{API_BASE}/", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def doc_badge(doc_type: str) -> str:
    css = {
        "aadhaar":          "badge-aadhaar",
        "driving_licence":  "badge-driving",
        "passport":         "badge-passport",
        "invoice":          "badge-invoice",
    }.get(doc_type, "badge-unknown")
    label = doc_type.replace("_", " ").title()
    return f'<span class="badge {css}">{label}</span>'


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("##  @DocExtract AI")
    st.markdown("---")

    api_ok = check_api()
    if api_ok:
        st.markdown('<span class="dot-green">●</span> **API Connected**', unsafe_allow_html=True)
    else:
        st.markdown('<span class="dot-red">●</span> **API Offline**', unsafe_allow_html=True)
        st.warning("Start the backend:\n```\nuvicorn app.main:app --reload\n```")

    st.markdown("---")
    st.markdown("**Supported Documents**")
    st.markdown("""
-  Aadhaar Card
-  Driving Licence
-  Passport
-  Invoice
""")
    st.markdown("---")
    st.markdown("**Supported Formats**")
    st.markdown("JPG · PNG · PDF")


# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1> Intelligent Document Extraction</h1>
  <p>Upload a document → OCR → Classify → Extract structured fields with AI</p>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_extract, tab_history = st.tabs(["📄 Extract Document", "📋 Extraction History"])


# ═══════════ TAB 1: Extract ═══════════════════════════════════════════════════
with tab_extract:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("### Upload Document")
        uploaded = st.file_uploader(
            "Drag & drop or click to browse",
            type=["jpg", "jpeg", "png", "bmp", "tiff", "tif", "gif", "pdf"],
            label_visibility="collapsed",
        )

        if uploaded:
            # Preview image
            if uploaded.type.startswith("image/"):
                st.image(uploaded, caption=uploaded.name, use_container_width=True)
            else:
                st.info(f"📄 **{uploaded.name}** ({uploaded.size:,} bytes)")

            extract_btn = st.button("🚀 Extract Fields", type="primary", use_container_width=True)

            if extract_btn:
                if not api_ok:
                    st.error("Backend API is offline. Please start it first.")
                else:
                    with st.spinner("Running OCR and extracting fields…"):
                        files = {
                            "file": (uploaded.name, uploaded.getvalue(), uploaded.type)
                        }
                        try:
                            resp = requests.post(f"{API_BASE}/extract", files=files, timeout=60)
                            if resp.status_code == 200:
                                st.session_state["last_result"] = resp.json()
                                st.success("✅ Extraction complete!")
                            else:
                                detail = resp.json().get("detail", resp.text)
                                st.error(f"❌ Error {resp.status_code}: {detail}")
                        except requests.exceptions.ConnectionError:
                            st.error("Cannot reach the API. Is uvicorn running?")
                        except Exception as exc:
                            st.error(f"Unexpected error: {exc}")

    with col2:
        if "last_result" in st.session_state:
            data = st.session_state["last_result"]
            st.markdown("### Extraction Result")

            # Doc type badge
            st.markdown(
                f"**Document Type:** {doc_badge(data['document_type'])}",
                unsafe_allow_html=True,
            )
            st.markdown(f"**File:** `{data['filename']}`")
            st.markdown(f"**Record ID:** `{data['id']}`")
            st.markdown(f"**Processed:** `{data['created_at'][:19].replace('T', ' ')}`")
            st.markdown("---")

            # Structured fields table
            st.markdown("#### ** Extracted Fields")
            structured = data.get("structured_data", {})
            if structured:
                rows = [
                    {"Field": k.replace("_", " ").title(), "Value": v or "—"}
                    for k, v in structured.items()
                ]
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No structured fields extracted.")

        else:
            st.markdown("### Result Preview")
            st.info("Upload a document and click **Extract Fields** to see results here.")


# ═══════════ TAB 2: History ════════════════════════════════════════════════════
with tab_history:
    st.markdown("### Extraction History")

    refresh = st.button("Refresh", type="secondary")

    if api_ok:
        try:
            resp = requests.get(f"{API_BASE}/records?limit=50", timeout=10)
            if resp.status_code == 200:
                payload = resp.json()
                records = payload.get("records", [])
                total   = payload.get("total", 0)

                st.markdown(f"**{total} record(s) in database**")

                if records:
                    rows = []
                    for r in records:
                        rows.append({
                            "ID":            r["id"],
                            "Filename":      r["filename"],
                            "Document Type": r["document_type"].replace("_", " ").title(),
                            "Processed At":  r["created_at"][:19].replace("T", " "),
                        })
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    # Delete action
                    st.markdown("---")
                    del_id = st.number_input("Delete record by ID:", min_value=1, step=1, value=1)
                    if st.button("Delete Record", type="secondary"):
                        dr = requests.delete(f"{API_BASE}/records/{int(del_id)}", timeout=10)
                        if dr.status_code == 204:
                            st.success(f"Record {del_id} deleted.")
                            st.rerun()
                        else:
                            st.error(f"Delete failed: {dr.json().get('detail', dr.text)}")
                else:
                    st.info("No records yet. Extract a document first.")
            else:
                st.error(f"Failed to load records: {resp.status_code}")
        except Exception as exc:
            st.error(f"Could not connect to API: {exc}")
    else:
        st.warning("API is offline. Start the backend first.")