"""
Página de Resultados — dashboard por avaliação com gráficos e exportação de laudo.
"""

import streamlit as st
import json
from datetime import date, datetime
from database.db import (
    listar_pacientes, buscar_paciente, buscar_avaliacoes_paciente,
    buscar_resultados_avaliacao, salvar_insight, buscar_insights,
)


COR_CLASSIF = {
    "Muito Rebaixado": "#c0392b",
    "Rebaixado":       "#e74c3c",
    "Abaixo da Média": "#e67e22",
    "Médio":           "#27ae60",
    "Acima da Média":  "#27ae60",
    "Superior":        "#2980b9",
    "Muito Superior":  "#1a5276",
    "Mínimo":          "#27ae60",
    "Leve":            "#f39c12",
    "Moderado":        "#e74c3c",
    "Grave":           "#c0392b",
    "Dentro da normalidade": "#27ae60",
}


def render():
    st.subheader("Resultados")

    pacientes = listar_pacientes()
    if not pacientes:
        st.info("Nenhum paciente cadastrado.")
        return

    opcoes_pac = {f"{p['nome']} (ID {p['id']})": p["id"] for p in pacientes}
    selecionado_default = None
    if "paciente_selecionado" in st.session_state:
        pid_saved = st.session_state["paciente_selecionado"]
        for k, v in opcoes_pac.items():
            if v == pid_saved:
                selecionado_default = k
                break

    escolha_pac = st.selectbox(
        "Paciente:",
        list(opcoes_pac.keys()),
        index=list(opcoes_pac.keys()).index(selecionado_default) if selecionado_default else 0,
    )
    paciente_id = opcoes_pac[escolha_pac]
    paciente = buscar_paciente(paciente_id)

    avals = buscar_avaliacoes_paciente(paciente_id)
    if not avals:
        st.info("Este paciente não possui avaliações ainda.")
        return

    opcoes_av = {f"Avaliação {a['data_avaliacao']} — {a['status']}": a["id"] for a in avals}
    escolha_av = st.selectbox("Avaliação:", list(opcoes_av.keys()))
    avaliacao_id = opcoes_av[escolha_av]

    resultados = buscar_resultados_avaliacao(avaliacao_id)
    if not resultados:
        st.info("Nenhum teste inserido nesta avaliação ainda.")
        return

    avaliacao = next((a for a in avals if a["id"] == avaliacao_id), {})

    st.markdown("---")
    _mostrar_dashboard(resultados, paciente, avaliacao)

    st.markdown("---")
    _secao_analise_integrada(resultados, paciente, avaliacao_id)

    st.markdown("---")
    _secao_exportar_laudo(paciente, avaliacao, resultados, avaliacao_id)


def _mostrar_dashboard(resultados, paciente, avaliacao):
    st.markdown("### Dashboard de Resultados")

    # Resumo de classificações
    classifs = _extrair_classificacoes(resultados)
    if classifs:
        cols = st.columns(len(classifs))
        for i, (nome, classif) in enumerate(classifs.items()):
            cor = COR_CLASSIF.get(classif, "#888")
            cols[i].markdown(f"""
            <div style="text-align:center; padding:0.8rem; border:1px solid #ddd; border-radius:8px; border-top:4px solid {cor}">
                <div style="font-size:0.75rem; color:#666">{nome}</div>
                <div style="font-size:0.9rem; font-weight:bold; color:{cor}">{classif}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")

    # Detalhes por teste
    for resultado in resultados:
        codigo = resultado["teste_codigo"]
        escores = resultado["escores_calculados"]
        interp  = resultado["interpretacao"]
        confianca = resultado.get("nivel_confianca", "—")

        with st.expander(f"**{codigo}** — {_titulo_teste(codigo)}", expanded=True):
            col_conf = st.columns([3, 1])
            col_conf[1].caption(f"Confiança normas: {confianca}")

            _renderizar_escores_visuais(codigo, escores)

            if interp:
                st.markdown("**Interpretação:**")
                st.text(interp)


def _renderizar_escores_visuais(codigo, escores):
    if not isinstance(escores, dict):
        return

    if codigo == "RAVLT":
        _visual_ravlt(escores)
    elif codigo == "FDT":
        _visual_fdt(escores)
    elif codigo == "TMT":
        _visual_tmt(escores)
    elif codigo in ("BDI2", "BAI"):
        _visual_escala_humor(codigo, escores)
    elif codigo == "SRS2":
        _visual_srs2(escores)
    elif codigo == "ETDAH":
        _visual_etdah(escores)


def _visual_ravlt(e):
    import plotly.graph_objects as go

    col1, col2 = st.columns([2, 1])
    with col1:
        # Curva de aprendizagem
        tentativas = ["A1", "A2", "A3", "A4", "A5", "B1", "A6", "A7"]
        valores    = [e.get(t, 0) for t in tentativas]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=tentativas, y=valores, mode="lines+markers+text",
            text=valores, textposition="top center",
            line=dict(color="#2980b9", width=2),
            marker=dict(size=8),
        ))
        fig.add_hline(y=15, line_dash="dot", line_color="gray", annotation_text="máx 15")
        fig.update_layout(
            title="Curva de Aprendizagem RAVLT",
            height=280, margin=dict(t=40, b=20, l=20, r=20),
            xaxis_title="Tentativa", yaxis_title="Palavras",
            yaxis=dict(range=[0, 16]),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        pct = e.get("percentil_total", 50)
        classif = e.get("classif_total", "—")
        cor = COR_CLASSIF.get(classif, "#888")
        st.markdown(f"""
        <div style="border-left:4px solid {cor}; padding:0.5rem 1rem; background:#f8f9fa; border-radius:0 6px 6px 0; margin:0.3rem 0">
            <div style="font-size:0.75rem; color:#666">Aprendizagem Total (A1-A5)</div>
            <div style="font-size:1.3rem; font-weight:bold">{e.get('total_A1_A5', 0)}</div>
            <div style="color:{cor}; font-size:0.85rem">{classif} | P{pct:.0f}</div>
        </div>
        """, unsafe_allow_html=True)

        pct7 = e.get("percentil_a7", 50)
        c7 = e.get("classif_a7", "—")
        cor7 = COR_CLASSIF.get(c7, "#888")
        st.markdown(f"""
        <div style="border-left:4px solid {cor7}; padding:0.5rem 1rem; background:#f8f9fa; border-radius:0 6px 6px 0; margin:0.3rem 0">
            <div style="font-size:0.75rem; color:#666">Evocação Tardia (A7)</div>
            <div style="font-size:1.3rem; font-weight:bold">{e.get('A7', 0)}</div>
            <div style="color:{cor7}; font-size:0.85rem">{c7} | P{pct7:.0f}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"**Retenção:** {e.get('retencao_percentual', 0)}%")
        st.markdown(f"**Reconhecimento:** {e.get('rec_hits', 0)} acertos / {e.get('rec_fa', 0)} FA")


def _visual_fdt(e):
    import plotly.graph_objects as go

    conds = e.get("condicoes", {})
    nomes = ["Contar", "Ler", "Escolher", "Alternar"]
    chaves = ["contar", "ler", "escolher", "alternar"]

    tempos = [conds.get(c, {}).get("tempo", 0) for c in chaves]
    pcts   = [conds.get(c, {}).get("percentil_tempo", 50) for c in chaves]
    cores  = [
        "#27ae60" if p >= 25 else ("#f39c12" if p >= 10 else "#e74c3c")
        for p in pcts
    ]

    fig = go.Figure(go.Bar(
        x=nomes, y=tempos, text=[f"{t:.1f}s<br>P{p:.0f}" for t, p in zip(tempos, pcts)],
        textposition="outside", marker_color=cores,
    ))
    fig.update_layout(
        title="FDT — Tempos por Condição",
        height=280, margin=dict(t=40, b=20, l=20, r=20),
        yaxis_title="Tempo (s)",
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    col1.metric("Índice de Inibição", f"{e.get('inibicao', 0):.1f}s", help="Escolher − Contar")
    col2.metric("Índice de Flexibilidade", f"{e.get('flexibilidade', 0):.1f}s", help="Alternar − média(Contar+Ler)")


def _visual_tmt(e):
    col1, col2, col3 = st.columns(3)
    cor_a = COR_CLASSIF.get(e.get("classificacao_a", ""), "#888")
    cor_b = COR_CLASSIF.get(e.get("classificacao_b", ""), "#888")

    col1.markdown(f"""
    <div style="border-left:4px solid {cor_a}; padding:0.5rem 1rem; background:#f8f9fa; border-radius:0 6px 6px 0">
        <div style="font-size:0.75rem; color:#666">TMT-A</div>
        <div style="font-size:1.3rem; font-weight:bold">{e.get('tempo_a', 0):.1f}s</div>
        <div style="color:{cor_a}; font-size:0.85rem">{e.get('classificacao_a','—')} | P{e.get('percentil_a',50):.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"""
    <div style="border-left:4px solid {cor_b}; padding:0.5rem 1rem; background:#f8f9fa; border-radius:0 6px 6px 0">
        <div style="font-size:0.75rem; color:#666">TMT-B</div>
        <div style="font-size:1.3rem; font-weight:bold">{e.get('tempo_b', 0):.1f}s</div>
        <div style="color:{cor_b}; font-size:0.85rem">{e.get('classificacao_b','—')} | P{e.get('percentil_b',50):.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    razao = e.get("razao_B_A")
    if razao:
        cor_razao = "#e74c3c" if razao > 3.5 else ("#f39c12" if razao > 2.5 else "#27ae60")
        col3.markdown(f"""
        <div style="border-left:4px solid {cor_razao}; padding:0.5rem 1rem; background:#f8f9fa; border-radius:0 6px 6px 0">
            <div style="font-size:0.75rem; color:#666">Razão B/A</div>
            <div style="font-size:1.3rem; font-weight:bold">{razao:.2f}</div>
            <div style="color:{cor_razao}; font-size:0.85rem">{'Elevada' if razao > 3.5 else ('Moderada' if razao > 2.5 else 'Normal')}</div>
        </div>
        """, unsafe_allow_html=True)


def _visual_escala_humor(codigo, e):
    import plotly.graph_objects as go

    total = e.get("total", 0)
    classif = e.get("classificacao", "—")
    maximo = 63
    cor = COR_CLASSIF.get(classif, "#888")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total,
        number={"suffix": f"/{maximo}"},
        title={"text": f"{codigo} — {classif}"},
        gauge={
            "axis": {"range": [0, maximo]},
            "bar": {"color": cor},
            "steps": [
                {"range": [0, 13],  "color": "#d5f5e3"},
                {"range": [13, 19], "color": "#fef9e7"},
                {"range": [19, 28], "color": "#fde8e8"},
                {"range": [28, 63], "color": "#fadbd8"},
            ] if codigo == "BDI2" else [
                {"range": [0, 10],  "color": "#d5f5e3"},
                {"range": [10, 19], "color": "#fef9e7"},
                {"range": [19, 30], "color": "#fde8e8"},
                {"range": [30, 63], "color": "#fadbd8"},
            ],
        },
    ))
    fig.update_layout(height=230, margin=dict(t=30, b=10, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)

    if e.get("alerta_ideacao_suicida"):
        st.error("🔴 ALERTA: Ideação suicida presente — avaliação de risco imediata indicada.")


def _visual_srs2(e):
    import plotly.graph_objects as go

    ts = e.get("tscores", {})
    subs = ["Percepção Social", "Cognição Social", "Comunicação Social", "Motivação Social", "Maneirismos"]
    valores = [ts.get(s, 50) for s in subs]
    cores   = ["#e74c3c" if v >= 66 else ("#f39c12" if v >= 60 else "#27ae60") for v in valores]

    fig = go.Figure(go.Bar(
        x=[s.replace(" ", "<br>") for s in subs],
        y=valores,
        text=[f"T={v:.0f}" for v in valores],
        textposition="outside",
        marker_color=cores,
    ))
    fig.add_hline(y=60, line_dash="dash", line_color="#f39c12", annotation_text="T=60 (leve)")
    fig.add_hline(y=66, line_dash="dash", line_color="#e74c3c", annotation_text="T=66 (moderado)")
    fig.update_layout(
        title=f"SRS-2 — T-scores por Subscala | Total T={e.get('total_tscore',50):.0f}",
        height=320, margin=dict(t=40, b=20, l=20, r=20),
        yaxis=dict(range=[30, 90]),
    )
    st.plotly_chart(fig, use_container_width=True)


def _visual_etdah(e):
    import plotly.graph_objects as go

    sint_d  = e.get("sintomas_desatencao", 0)
    sint_h  = e.get("sintomas_hi", 0)
    limiar  = e.get("limiar_usado", 6)

    fig = go.Figure(go.Bar(
        x=["Desatenção", "Hiperatividade/Impulsividade"],
        y=[sint_d, sint_h],
        text=[f"{sint_d}/9", f"{sint_h}/9"],
        textposition="outside",
        marker_color=[
            "#e74c3c" if sint_d >= limiar else "#f39c12" if sint_d >= limiar - 2 else "#27ae60",
            "#e74c3c" if sint_h >= limiar else "#f39c12" if sint_h >= limiar - 2 else "#27ae60",
        ],
    ))
    fig.add_hline(y=limiar, line_dash="dash", line_color="#e74c3c",
                  annotation_text=f"Limiar DSM-5 ({limiar})")
    fig.update_layout(
        title=f"ETDAH — Sintomas Presentes | {e.get('apresentacao_sugerida','—')}",
        height=280, margin=dict(t=40, b=20, l=20, r=20),
        yaxis=dict(range=[0, 10]),
    )
    st.plotly_chart(fig, use_container_width=True)


def _secao_analise_integrada(resultados, paciente, avaliacao_id):
    st.markdown("### Análise Integrada")

    provedor  = st.session_state.get("provedor_ia", "offline")
    api_key   = st.session_state.get(f"api_key_{provedor}", "")
    tem_ia    = provedor != "offline" and bool(api_key)

    insights_salvos = buscar_insights(avaliacao_id)

    if insights_salvos:
        ins_mais_recente = insights_salvos[0]
        st.caption(f"Gerado em: {ins_mais_recente['criado_em']} | Modelo: {ins_mais_recente['modelo_usado']}")
        st.text(ins_mais_recente["conteudo"])
        st.markdown("---")
        if st.button("Regenerar Análise", key="regen_insights"):
            _gerar_e_salvar_insights(resultados, paciente, avaliacao_id, provedor, api_key)
    else:
        label = f"Gerar Análise com {provedor.capitalize()}" if tem_ia else "Gerar Análise Offline"
        if st.button(label, type="primary", key="gerar_insights"):
            _gerar_e_salvar_insights(resultados, paciente, avaliacao_id, provedor, api_key)


def _gerar_e_salvar_insights(resultados, paciente, avaliacao_id, provedor, api_key):
    from ia.insights import gerar_insights

    idade = _calcular_idade(paciente.get("data_nascimento", ""))
    pac_contexto = {
        "nome": paciente.get("nome", ""),
        "idade": idade,
        "sexo": paciente.get("sexo", ""),
        "escolaridade": paciente.get("escolaridade", ""),
        "queixa_principal": paciente.get("queixa_principal", ""),
    }

    modelos_label = {
        "claude":  "claude-sonnet-4-6",
        "gemini":  "gemini-2.5-flash",
        "openai":  "gpt-4o",
        "offline": "offline",
    }

    with st.spinner(f"Gerando análise ({provedor})..."):
        texto = gerar_insights(
            resultados, pac_contexto,
            provedor=provedor,
            api_key=api_key,
        )

    modelo = modelos_label.get(provedor, provedor)
    salvar_insight(avaliacao_id, "perfil_integrado", texto, modelo)
    st.success("Análise gerada!")
    st.text(texto)


def _secao_exportar_laudo(paciente, avaliacao, resultados, avaliacao_id):
    st.markdown("### Exportar Rascunho de Laudo")

    insights = buscar_insights(avaliacao_id)
    texto_insights = insights[0]["conteudo"] if insights else None

    if st.button("Gerar Laudo Word (.docx)", type="primary", key="gerar_laudo"):
        from relatorios.gerador import gerar_laudo

        with st.spinner("Gerando documento Word..."):
            buffer = gerar_laudo(paciente, avaliacao, resultados, insights=texto_insights)

        nome_arquivo = f"laudo_{paciente.get('nome','paciente').replace(' ','_')}_{avaliacao.get('data_avaliacao', str(date.today()))}.docx"
        st.download_button(
            label="Baixar Laudo Word",
            data=buffer,
            file_name=nome_arquivo,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
        )
        st.success("Laudo gerado! Revise e edite antes da versão final.")
        st.info(
            "O arquivo Word contém rascunho estruturado com todos os resultados. "
            "Seções em colchetes [  ] precisam ser preenchidas manualmente com informações clínicas."
        )


def _extrair_classificacoes(resultados):
    classifs = {}
    for r in resultados:
        codigo = r["teste_codigo"]
        e = r.get("escores_calculados", {})
        if not isinstance(e, dict):
            continue

        mapa = {
            "RAVLT": ("Memória", e.get("classif_total")),
            "FDT":   ("FDT-Alternar", e.get("condicoes", {}).get("alternar", {}).get("classificacao")),
            "TMT":   ("TMT-B", e.get("classificacao_b")),
            "BDI2":  ("Depressão", e.get("classificacao")),
            "BAI":   ("Ansiedade", e.get("classificacao")),
            "SRS2":  ("Social", e.get("classificacao")),
            "ETDAH": ("TDAH", "Sim" if e.get("criterios_quantitativos_met") else "Não"),
        }
        if codigo in mapa:
            nome, val = mapa[codigo]
            if val:
                classifs[nome] = val

    return classifs


def _titulo_teste(codigo):
    nomes = {
        "RAVLT": "Memória Episódica Verbal",
        "FDT":   "Five Digit Test",
        "TMT":   "Trail Making Test",
        "SRS2":  "Responsividade Social",
        "ETDAH": "Escala TDAH DSM-5",
        "BDI2":  "Depressão (BDI-II)",
        "BAI":   "Ansiedade (BAI)",
    }
    return nomes.get(codigo, codigo)


def _calcular_idade(data_nasc_str):
    if not data_nasc_str:
        return 35
    try:
        nasc = datetime.strptime(str(data_nasc_str)[:10], "%Y-%m-%d").date()
        hoje = date.today()
        return hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
    except Exception:
        return 35
