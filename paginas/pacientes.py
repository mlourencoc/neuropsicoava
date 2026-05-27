import streamlit as st
from datetime import date, datetime
from database.db import (
    criar_paciente, listar_pacientes, buscar_paciente,
    buscar_avaliacoes_paciente, atualizar_paciente,
)


def render():
    st.subheader("Gerenciamento de Pacientes")

    aba = st.tabs(["Lista de Pacientes", "Novo Paciente"])

    # ── Aba: Lista ─────────────────────────────────────────────────────────
    with aba[0]:
        pacientes = listar_pacientes()
        if not pacientes:
            st.info("Nenhum paciente cadastrado ainda. Use a aba 'Novo Paciente' para começar.")
            # não retorna — deixa a aba Novo Paciente renderizar

        # Busca
        busca = st.text_input("Buscar por nome:", placeholder="Digite parte do nome...")
        if busca:
            pacientes = [p for p in pacientes if busca.lower() in p["nome"].lower()]

        for p in pacientes:
            with st.expander(f"**{p['nome']}** — {_idade_str(p['data_nascimento'])} | {p.get('sexo','')} | {p.get('escolaridade','')}"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Queixa:** {p.get('queixa_principal','—')}")
                    if p.get("observacoes"):
                        st.markdown(f"**Observações:** {p['observacoes']}")

                    avals = buscar_avaliacoes_paciente(p["id"])
                    st.markdown(f"**Avaliações realizadas:** {len(avals)}")

                with col2:
                    if st.button("Iniciar Avaliação", key=f"btn_aval_{p['id']}"):
                        st.session_state["paciente_selecionado"] = p["id"]
                        st.session_state["pagina_redirect"] = "📋 Nova Avaliação"
                        st.success(f"Paciente {p['nome']} selecionado. Acesse 'Nova Avaliação'.")

                    if st.button("Ver Resultados", key=f"btn_res_{p['id']}"):
                        st.session_state["paciente_selecionado"] = p["id"]
                        st.session_state["pagina_redirect"] = "📊 Resultados"
                        st.success(f"Acesse 'Resultados' para ver os dados de {p['nome']}.")

    # ── Aba: Novo Paciente ─────────────────────────────────────────────────
    with aba[1]:
        st.markdown("#### Cadastrar Novo Paciente")

        with st.form("form_novo_paciente", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome completo *", placeholder="Nome do paciente")
                data_nasc = st.date_input(
                    "Data de nascimento *",
                    value=date(1990, 1, 1),
                    min_value=date(1920, 1, 1),
                    max_value=date.today(),
                    format="DD/MM/YYYY",
                )
                sexo = st.selectbox("Sexo *", ["Feminino", "Masculino", "Outro/Não informado"])

            with col2:
                escolaridade = st.selectbox(
                    "Escolaridade *",
                    [
                        "Sem escolaridade (0 anos)",
                        "Fundamental incompleto (1-4 anos)",
                        "Fundamental completo (5-8 anos)",
                        "Médio incompleto (9-10 anos)",
                        "Médio completo (11 anos)",
                        "Superior incompleto (12+ anos)",
                        "Superior completo (15+ anos)",
                        "Pós-graduação",
                    ],
                )
                anos_esc = _anos_escolaridade(escolaridade)
                st.caption(f"Anos de escolaridade estimados: {anos_esc}")

            queixa = st.text_area(
                "Queixa principal / Motivo da avaliação *",
                placeholder="Descreva a queixa principal, encaminhamento, histórico relevante...",
                height=100,
            )
            obs = st.text_area(
                "Observações adicionais (opcional)",
                placeholder="Histórico médico, medicações, informações relevantes...",
                height=80,
            )

            submit = st.form_submit_button("Cadastrar Paciente", type="primary")

        if submit:
            if not nome or not queixa:
                st.error("Nome e queixa principal são obrigatórios.")
            else:
                sexo_sigla = "F" if sexo == "Feminino" else ("M" if sexo == "Masculino" else "O")
                pid = criar_paciente(
                    nome=nome,
                    data_nascimento=str(data_nasc),
                    escolaridade=f"{escolaridade} ({anos_esc} anos)",
                    sexo=sexo_sigla,
                    queixa=queixa,
                    obs=obs,
                )
                st.session_state["paciente_selecionado"] = pid
                st.success(f"Paciente **{nome}** cadastrado com sucesso! ID: {pid}")
                st.balloons()


def _idade_str(data_nasc_str):
    if not data_nasc_str:
        return "idade desconhecida"
    try:
        nasc = datetime.strptime(str(data_nasc_str)[:10], "%Y-%m-%d").date()
        hoje = date.today()
        anos = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
        return f"{anos} anos"
    except Exception:
        return "—"


def _anos_escolaridade(escolaridade_str):
    mapa = {
        "Sem escolaridade": 0,
        "Fundamental incompleto": 4,
        "Fundamental completo": 8,
        "Médio incompleto": 10,
        "Médio completo": 11,
        "Superior incompleto": 13,
        "Superior completo": 15,
        "Pós-graduação": 17,
    }
    for k, v in mapa.items():
        if k.lower() in escolaridade_str.lower():
            return v
    return 8
