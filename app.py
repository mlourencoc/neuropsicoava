"""
NeuroPsico Avaliação — Plataforma de Correção de Testes Neuropsicológicos
Versão 1.0
"""

import streamlit as st
import sys
import os

# Fix SSL no Windows — substitui create_default_context globalmente pelo certifi
try:
    import ssl
    import certifi
    _orig_ctx = ssl.create_default_context
    def _ssl_certifi(*args, **kwargs):
        kwargs.setdefault("cafile", certifi.where())
        return _orig_ctx(*args, **kwargs)
    ssl.create_default_context = _ssl_certifi
    os.environ["SSL_CERT_FILE"]      = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
except Exception:
    pass

# Adiciona o diretório raiz ao path para imports relativos
sys.path.insert(0, os.path.dirname(__file__))

from database.db import inicializar_banco

st.set_page_config(
    page_title="NeuroPsico Avaliação",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicializar banco na primeira execução
inicializar_banco()

# ── CSS personalizado ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a5276 0%, #2980b9 100%);
        padding: 1.5rem 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { color: white; margin: 0; font-size: 1.8rem; }
    .main-header p  { color: #d6eaf8; margin: 0.3rem 0 0 0; font-size: 0.95rem; }

    .card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    .badge-danger   { background:#e74c3c; color:white; padding:2px 8px; border-radius:4px; font-size:0.8rem; }
    .badge-warning  { background:#f39c12; color:white; padding:2px 8px; border-radius:4px; font-size:0.8rem; }
    .badge-success  { background:#27ae60; color:white; padding:2px 8px; border-radius:4px; font-size:0.8rem; }
    .badge-info     { background:#2980b9; color:white; padding:2px 8px; border-radius:4px; font-size:0.8rem; }

    .metric-box {
        border-left: 4px solid #2980b9;
        padding: 0.5rem 1rem;
        background: #f8f9fa;
        border-radius: 0 6px 6px 0;
        margin: 0.4rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🧠 NeuroPsico Avaliação</h1>
    <p>Plataforma de Correção e Análise de Testes Neuropsicológicos</p>
</div>
""", unsafe_allow_html=True)


# ── Navegação ─────────────────────────────────────────────────────────────────
st.sidebar.markdown("## Navegação")

pagina = st.sidebar.radio(
    "Selecionar página:",
    [
        "🏠 Início",
        "👤 Pacientes",
        "📋 Nova Avaliação",
        "📊 Resultados",
        "⚙️ Configurações",
    ],
    label_visibility="collapsed",
)

# Provedor de IA no sidebar
st.sidebar.markdown("---")

# Inicializar estado se necessário
if "provedor_ia" not in st.session_state:
    st.session_state.provedor_ia = "offline"
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if st.session_state.api_key:
        st.session_state.api_key_claude = st.session_state.api_key

provedor_atual = st.session_state.get("provedor_ia", "offline")
api_key_prov   = st.session_state.get(f"api_key_{provedor_atual}", "")
modo_ia_ativo  = provedor_atual != "offline" and bool(api_key_prov)

ICONS = {"offline": "⚪", "claude": "🟠", "gemini": "🔵", "openai": "🟢"}
icone = ICONS.get(provedor_atual, "⚪")
label = provedor_atual.capitalize() if provedor_atual != "offline" else "Offline"
st.sidebar.markdown(f"**IA:** {icone} {label} {'✓' if modo_ia_ativo else '(sem chave)'}")
if not modo_ia_ativo and provedor_atual != "offline":
    st.sidebar.caption("Configure a chave em ⚙️ Configurações.")

st.sidebar.markdown("---")
st.sidebar.caption("v1.0 | Normas brasileiras publicadas")


# ── Página Início ─────────────────────────────────────────────────────────────
if pagina == "🏠 Início":
    from paginas.inicio import render
    render()

elif pagina == "👤 Pacientes":
    from paginas.pacientes import render
    render()

elif pagina == "📋 Nova Avaliação":
    from paginas.avaliacao import render
    render()

elif pagina == "📊 Resultados":
    from paginas.resultados import render
    render()

elif pagina == "⚙️ Configurações":
    from paginas.configuracoes import render
    render()
