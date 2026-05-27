import streamlit as st
from database.db import listar_pacientes, buscar_avaliacoes_paciente


def render():
    st.subheader("Bem-vinda à Plataforma NeuroPsico Avaliação")

    # Estatísticas rápidas
    pacientes = listar_pacientes()
    total_avaliacoes = sum(len(buscar_avaliacoes_paciente(p["id"])) for p in pacientes)

    col1, col2, col3 = st.columns(3)
    col1.metric("Pacientes cadastrados", len(pacientes))
    col2.metric("Avaliações realizadas", total_avaliacoes)
    col3.metric("Testes disponíveis", "7")

    st.markdown("---")

    # Testes disponíveis
    st.markdown("### Testes Disponíveis")

    testes = [
        ("RAVLT",  "Memória",              "88-92%", "Rey Auditory Verbal Learning Test"),
        ("FDT",    "Funções Executivas",   "82-88%", "Five Digit Test"),
        ("TMT",    "Funções Executivas",   "85-90%", "Trail Making Test A e B"),
        ("SRS-2",  "Cognição Social",      "75-80%", "Social Responsiveness Scale"),
        ("ETDAH",  "TDAH (DSM-5)",         "88-92%", "Escala de Avaliação de TDAH"),
        ("BDI-II", "Humor",                "91-96%", "Inventário de Depressão de Beck"),
        ("BAI",    "Ansiedade",            "93-97%", "Inventário de Ansiedade de Beck"),
    ]

    cols = st.columns(2)
    for i, (sigla, dominio, assert_, nome_completo) in enumerate(testes):
        col = cols[i % 2]
        with col:
            cor = "#27ae60" if float(assert_.split("-")[0]) >= 88 else (
                  "#f39c12" if float(assert_.split("-")[0]) >= 80 else "#e67e22")
            st.markdown(f"""
            <div style="border:1px solid #e0e0e0; border-radius:8px; padding:0.8rem; margin-bottom:0.6rem; border-left:4px solid {cor}">
                <strong>{sigla}</strong> &nbsp;
                <span style="background:{cor}; color:white; padding:2px 6px; border-radius:3px; font-size:0.75rem">
                    {assert_}
                </span><br>
                <span style="color:#666; font-size:0.85rem">{nome_completo}</span><br>
                <span style="color:#888; font-size:0.8rem">Domínio: {dominio}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Como Usar")
    st.markdown("""
    1. **👤 Cadastre o paciente** → Acesse "Pacientes" e clique em "Novo Paciente"
    2. **📋 Inicie uma avaliação** → Em "Nova Avaliação", selecione o paciente e os testes que aplicou
    3. **📸 Insira os dados** → Upload de foto do teste ou digitação manual dos escores
    4. **📊 Veja os resultados** → Escores, percentis, classificações e análise integrada
    5. **📄 Exporte o laudo** → Rascunho em Word pronto para edição
    """)

    st.info(
        "**Nota sobre assertividade:** Os percentuais indicam a confiança nas normas utilizadas, "
        "baseadas em literatura brasileira publicada. Sempre revisar os resultados com julgamento clínico. "
        "O SRS-2 utiliza normas americanas (sem publicação brasileira validada até o momento)."
    )
