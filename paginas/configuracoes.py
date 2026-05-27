import streamlit as st
import os


PROVEDORES = {
    "offline": {
        "label":       "Offline (sem IA)",
        "descricao":   "Análise por regras clínicas. Gratuito, sem internet, sem chave.",
        "key_label":   None,
        "key_help":    None,
        "placeholder": None,
        "modelos":     "—",
        "cor":         "#7f8c8d",
    },
    "claude": {
        "label":       "Claude (Anthropic)",
        "descricao":   "Claude Sonnet — melhor integração clínica, suporte nativo a visão.",
        "key_label":   "Chave API Anthropic",
        "key_help":    "Obtenha em console.anthropic.com",
        "placeholder": "sk-ant-api03-...",
        "modelos":     "claude-sonnet-4-6 (insights) · claude-sonnet-4-6 (visão)",
        "cor":         "#d35400",
    },
    "gemini": {
        "label":       "Gemini (Google)",
        "descricao":   "Gemini 2.5 Flash — rápido, generoso no tier gratuito.",
        "key_label":   "Chave API Google AI Studio",
        "key_help":    "Obtenha em aistudio.google.com/apikey",
        "placeholder": "AIza...",
        "modelos":     "gemini-2.5-flash (insights e visão)",
        "cor":         "#1a73e8",
    },
    "openai": {
        "label":       "GPT-4o (OpenAI)",
        "descricao":   "GPT-4o — boa capacidade analítica e de visão.",
        "key_label":   "Chave API OpenAI",
        "key_help":    "Obtenha em platform.openai.com/api-keys",
        "placeholder": "sk-proj-...",
        "modelos":     "gpt-4o (insights e visão)",
        "cor":         "#10a37f",
    },
}


def render():
    st.subheader("Configurações")

    # ── Seleção de provedor ────────────────────────────────────────────────
    st.markdown("### Provedor de IA")

    provedor_atual = st.session_state.get("provedor_ia", "offline")

    cols = st.columns(4)
    for i, (chave, info) in enumerate(PROVEDORES.items()):
        selecionado = provedor_atual == chave
        borda = f"3px solid {info['cor']}" if selecionado else "1px solid #ddd"
        bg    = "#f0f7ff" if selecionado else "white"
        badge = " ✓" if selecionado else ""
        cols[i].markdown(f"""
        <div style="border:{borda}; border-radius:8px; padding:0.8rem; background:{bg}; min-height:90px">
            <div style="font-weight:bold; color:{info['cor']}">{info['label']}{badge}</div>
            <div style="font-size:0.78rem; color:#555; margin-top:0.3rem">{info['descricao']}</div>
        </div>
        """, unsafe_allow_html=True)
        if cols[i].button("Selecionar", key=f"sel_{chave}", use_container_width=True):
            st.session_state["provedor_ia"] = chave
            st.rerun()

    provedor_atual = st.session_state.get("provedor_ia", "offline")
    info = PROVEDORES[provedor_atual]

    st.markdown(f"**Provedor ativo:** {info['label']} — Modelos: `{info['modelos']}`")

    # ── Chave API do provedor selecionado ──────────────────────────────────
    if provedor_atual != "offline":
        st.markdown(f"### Chave API — {info['label']}")
        st.caption(info["key_help"])

        key_session = f"api_key_{provedor_atual}"
        chave_atual = st.session_state.get(key_session, "")

        with st.form(f"form_key_{provedor_atual}"):
            nova_key = st.text_input(
                info["key_label"],
                value=chave_atual,
                type="password",
                placeholder=info["placeholder"],
            )
            col1, col2 = st.columns(2)
            salvar = col1.form_submit_button("Salvar chave", type="primary")
            limpar = col2.form_submit_button("Remover")

        if salvar:
            st.session_state[key_session] = nova_key
            # Compatibilidade com código legado que usa "api_key"
            st.session_state["api_key"] = nova_key if nova_key else ""
            st.success(f"Chave {info['label']} salva!" if nova_key else "Chave removida.")

        if limpar:
            st.session_state[key_session] = ""
            st.session_state["api_key"]   = ""
            st.info("Chave removida.")

        chave_ativa = st.session_state.get(key_session, "")
        if chave_ativa:
            if st.button(f"Testar conexão com {info['label']}"):
                _testar_provedor(provedor_atual, chave_ativa)

    # ── Resumo de chaves configuradas ─────────────────────────────────────
    st.markdown("---")
    st.markdown("### Chaves configuradas")
    for chave, inf in PROVEDORES.items():
        if chave == "offline":
            continue
        key_session = f"api_key_{chave}"
        tem_chave = bool(st.session_state.get(key_session, ""))
        status = "✅ Configurada" if tem_chave else "⚪ Não configurada"
        st.markdown(f"- **{inf['label']}**: {status}")

    # ── Sobre ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Sobre a Plataforma")
    st.markdown("""
    **NeuroPsico Avaliação v1.0**

    | Teste | Norma | Assertividade |
    |-------|-------|---------------|
    | RAVLT | Malloy-Diniz et al. (2007); Fichman et al. (2010) | 88–92% |
    | FDT   | Paula et al. (2012) | 82–88% |
    | TMT   | Campanholo et al. (2014) | 85–90% |
    | SRS-2 | Constantino & Gruber (2012) — normas EUA | 75–80% |
    | ETDAH | DSM-5-TR (2022) | 88–92% |
    | BDI-II | Gorenstein & Andrade (1996); Cunha (2001) | 91–96% |
    | BAI   | Cunha (2001) | 93–97% |

    Dados armazenados localmente em `dados_neuropsico.db`. Nenhum dado é enviado a terceiros,
    exceto quando um provedor de IA está ativo para análise ou leitura de fotos.
    """)

    st.markdown("---")
    st.markdown("### Banco de Dados")
    col1, col2 = st.columns(2)
    from database.db import listar_pacientes
    col1.metric("Pacientes no banco", len(listar_pacientes()))
    from pathlib import Path
    db_path = Path(__file__).parent.parent / "dados_neuropsico.db"
    if db_path.exists():
        col2.metric("Tamanho do banco", f"{db_path.stat().st_size / 1024:.1f} KB")


# ──────────────────────────────────────────────────────────────────────────────

def _testar_provedor(provedor, api_key):
    msg_teste = "Responda apenas: OK"
    try:
        if provedor == "claude":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=10,
                messages=[{"role": "user", "content": msg_teste}],
            )
            st.success(f"Claude OK — {resp.content[0].text}")

        elif provedor == "gemini":
            from google import genai
            client = genai.Client(api_key=api_key)
            resp   = client.models.generate_content(model="gemini-2.5-flash", contents=msg_teste)
            st.success(f"Gemini OK — {resp.text[:50]}")

        elif provedor == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=10,
                messages=[{"role": "user", "content": msg_teste}],
            )
            st.success(f"OpenAI OK — {resp.choices[0].message.content}")

    except ImportError as e:
        st.error(f"Pacote não instalado: {e}")
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
