"""
Página de Nova Avaliação — entrada de dados por teste com upload de foto ou digitação manual.
"""

import streamlit as st
import json
from datetime import date, datetime
from database.db import (
    listar_pacientes, buscar_paciente, criar_avaliacao,
    buscar_avaliacoes_paciente, salvar_resultado_teste,
    buscar_resultados_avaliacao, finalizar_avaliacao, deletar_avaliacao,
)


def render():
    st.subheader("Nova Avaliação")

    pacientes = listar_pacientes()
    if not pacientes:
        st.warning("Cadastre um paciente primeiro em 'Pacientes'.")
        return

    # Seleção de paciente
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

    # Info rápida do paciente
    col1, col2, col3 = st.columns(3)
    col1.markdown(f"**Queixa:** {paciente.get('queixa_principal','—')[:60]}...")
    col2.markdown(f"**Escolaridade:** {paciente.get('escolaridade','—')}")
    col3.markdown(f"**Sexo:** {paciente.get('sexo','—')}")

    idade_pac = _calcular_idade(paciente.get("data_nascimento", ""))
    anos_esc  = _extrair_anos_esc(paciente.get("escolaridade", ""))
    sexo_pac  = paciente.get("sexo", "M")

    st.markdown("---")

    # Criação/seleção de avaliação
    avals = buscar_avaliacoes_paciente(paciente_id)
    avals_abertas = [a for a in avals if a["status"] == "em_andamento"]

    col_sel, col_nova = st.columns([3, 1])
    with col_nova:
        st.markdown(" ")
        if st.button("＋ Nova Avaliação", use_container_width=True):
            st.session_state["modo_nova_avaliacao"] = True

    with col_sel:
        if avals_abertas and not st.session_state.get("modo_nova_avaliacao"):
            opcoes_av = {f"Avaliação {a['data_avaliacao']} (ID {a['id']})": a["id"] for a in avals_abertas}
            escolha_av = st.selectbox("Avaliação em andamento:", list(opcoes_av.keys()))
            avaliacao_id = opcoes_av[escolha_av]
        else:
            avaliacao_id = None

    if avaliacao_id is None:
        obs_comp = st.text_area(
            "Observações comportamentais (opcional):",
            placeholder="Como o paciente se apresentou durante a avaliação...",
            height=80,
        )
        if st.button("Iniciar Avaliação", type="primary"):
            avaliacao_id = criar_avaliacao(paciente_id, obs_comportamentais=obs_comp)
            st.session_state["avaliacao_id_atual"] = avaliacao_id
            st.session_state.pop("modo_nova_avaliacao", None)
            st.success(f"Avaliação iniciada (ID: {avaliacao_id})")
            st.rerun()
        return

    st.session_state["avaliacao_id_atual"] = avaliacao_id

    # Resultados já salvos
    resultados_existentes = {r["teste_codigo"]: r for r in buscar_resultados_avaliacao(avaliacao_id)}

    st.markdown(f"### Testes — Avaliação ID {avaliacao_id}")

    # Grade de testes com status visual
    testes_disponiveis = {
        "RAVLT":  "RAVLT\nMemória Episódica Verbal",
        "FDT":    "FDT\nFive Digit Test",
        "TMT":    "TMT\nTrail Making Test",
        "SRS2":   "SRS-2\nResponsividade Social",
        "ETDAH":  "ETDAH\nSintomas de TDAH",
        "BDI2":   "BDI-II\nDepressão de Beck",
        "BAI":    "BAI\nAnsiedade de Beck",
    }

    st.caption("Clique em um teste para abrir o formulário de entrada:")
    cols = st.columns(4)
    for i, (cod, label) in enumerate(testes_disponiveis.items()):
        feito = cod in resultados_existentes
        icone = "✅" if feito else "⬜"
        with cols[i % 4]:
            if st.button(f"{icone} {label}", key=f"btn_sel_{cod}", use_container_width=True):
                st.session_state["teste_ativo"] = cod

    codigo = st.session_state.get("teste_ativo", "RAVLT")
    if codigo not in testes_disponiveis:
        codigo = "RAVLT"

    st.markdown("---")
    feito = codigo in resultados_existentes
    st.markdown(f"**Editando:** `{codigo}` {'✅ (já inserido — você pode atualizar)' if feito else '🆕 (novo)'}")
    st.markdown("---")

    # Roteador por teste
    _renderizar_teste(codigo, avaliacao_id, paciente_id, idade_pac, anos_esc, sexo_pac, resultados_existentes)

    st.markdown("---")

    # Finalizar avaliação
    if resultados_existentes:
        st.markdown(f"**Testes inseridos ({len(resultados_existentes)}):** {', '.join(resultados_existentes.keys())}")
        col_fin, col_del = st.columns([3, 1])
        with col_fin:
            if st.button("✅ Finalizar Avaliação e Ver Resultados", type="primary", use_container_width=True):
                finalizar_avaliacao(avaliacao_id)
                st.session_state["avaliacao_resultado_id"] = avaliacao_id
                st.success("Avaliação finalizada! Acesse 'Resultados' para ver a análise completa.")
        with col_del:
            if st.button("🗑️ Apagar Avaliação", use_container_width=True):
                st.session_state[f"confirmar_del_{avaliacao_id}"] = True

    if st.session_state.get(f"confirmar_del_{avaliacao_id}"):
        st.warning("Tem certeza? Todos os testes desta avaliação serão apagados.")
        c1, c2 = st.columns(2)
        if c1.button("Sim, apagar", type="primary"):
            deletar_avaliacao(avaliacao_id)
            st.session_state.pop(f"confirmar_del_{avaliacao_id}", None)
            st.session_state.pop("avaliacao_id_atual", None)
            st.rerun()
        if c2.button("Cancelar"):
            st.session_state.pop(f"confirmar_del_{avaliacao_id}", None)
            st.rerun()


def _renderizar_teste(codigo, avaliacao_id, paciente_id, idade, anos_esc, sexo, existentes):
    api_key = st.session_state.get("api_key", "")
    modo_ia = bool(api_key)

    # Upload de foto (modo IA)
    provedor = st.session_state.get("provedor_ia", "offline")
    if modo_ia:
        st.markdown(f"#### Upload de Foto do Teste (IA: {provedor.capitalize()})")
        counter_key = f"upload_counter_{codigo}_{avaliacao_id}"
        counter = st.session_state.get(counter_key, 0)

        col_up, col_nova = st.columns([4, 1])
        with col_up:
            foto = st.file_uploader(
                "Envie uma foto da folha de registro (JPG/PNG):",
                type=["jpg", "jpeg", "png"],
                key=f"foto_{codigo}_{avaliacao_id}_{counter}",
            )
        with col_nova:
            st.markdown(" ")
            if st.button("🔄 Nova foto", key=f"nova_foto_{codigo}_{counter}", use_container_width=True):
                st.session_state[counter_key] = counter + 1
                st.session_state.pop(f"dados_foto_{codigo}", None)
                st.rerun()

        if foto and st.button(f"Ler foto com {provedor.capitalize()}", key=f"ler_foto_{codigo}_{counter}"):
            from ia.visao import ler_foto_teste
            with st.spinner("Analisando imagem..."):
                resultado_foto = ler_foto_teste(
                    foto.read(), codigo,
                    provedor=provedor,
                    api_key=st.session_state.get(f"api_key_{provedor}", ""),
                )
            if "erro" in resultado_foto:
                st.error(resultado_foto["erro"])
            elif "_aviso" in resultado_foto:
                st.warning(resultado_foto["_aviso"])
                st.code(resultado_foto.get("texto_bruto", ""))
            else:
                st.success("Dados extraídos! Revise os campos abaixo e clique em Calcular.")
                st.session_state[f"dados_foto_{codigo}"] = resultado_foto
                st.json(resultado_foto)
                if codigo == "RAVLT":
                    for campo, widget_key in _RAVLT_WIDGET_MAP.items():
                        val = resultado_foto.get(campo)
                        if val is not None:
                            try:
                                st.session_state[widget_key] = int(val)
                            except (ValueError, TypeError):
                                pass
                    st.rerun()

        st.markdown("---")

    # Formulários manuais por teste
    if codigo == "RAVLT":
        _form_ravlt(avaliacao_id, idade, anos_esc, existentes)
    elif codigo == "FDT":
        _form_fdt(avaliacao_id, idade, anos_esc, existentes)
    elif codigo == "TMT":
        _form_tmt(avaliacao_id, idade, anos_esc, existentes)
    elif codigo == "SRS2":
        _form_srs2(avaliacao_id, idade, sexo, existentes)
    elif codigo == "ETDAH":
        _form_etdah(avaliacao_id, idade, existentes)
    elif codigo == "BDI2":
        _form_bdi2(avaliacao_id, existentes)
    elif codigo == "BAI":
        _form_bai(avaliacao_id, existentes)


# ──────────────────────────────────────────────────────────────────────────────
# Formulários por teste
# ──────────────────────────────────────────────────────────────────────────────

_RAVLT_WIDGET_MAP = {
    "A1": "ravlt_a1", "A2": "ravlt_a2", "A3": "ravlt_a3",
    "A4": "ravlt_a4", "A5": "ravlt_a5", "B1": "ravlt_b1",
    "A6": "ravlt_a6", "A7": "ravlt_a7",
    "rec_hits": "ravlt_rec_h", "rec_fa": "ravlt_rec_fa",
}



def _form_ravlt(avaliacao_id, idade, anos_esc, existentes):
    from testes.ravlt import calcular_escores

    st.markdown("#### RAVLT — Entrada de Dados")
    st.caption("Informe o número de palavras evocadas em cada tentativa.")

    dados_prev = existentes.get("RAVLT", {}).get("dados_brutos", {})
    foto_dados = st.session_state.get("dados_foto_RAVLT", {})
    pre = {**dados_prev, **foto_dados}

    populacao = st.radio("Faixa etária:", ["Adulto (18+)", "Criança/Adolescente (<18)"], horizontal=True)
    pop_key = "adulto" if "Adulto" in populacao else "infantil"

    col1, col2, col3 = st.columns(3)
    with col1:
        a1 = st.number_input("A1 (palavras):", 0, 15, int(pre.get("A1", 0)), key="ravlt_a1")
        a2 = st.number_input("A2:", 0, 15, int(pre.get("A2", 0)), key="ravlt_a2")
        a3 = st.number_input("A3:", 0, 15, int(pre.get("A3", 0)), key="ravlt_a3")
        a4 = st.number_input("A4:", 0, 15, int(pre.get("A4", 0)), key="ravlt_a4")
        a5 = st.number_input("A5:", 0, 15, int(pre.get("A5", 0)), key="ravlt_a5")
    with col2:
        b1 = st.number_input("B1 (interferência):", 0, 15, int(pre.get("B1", 0)), key="ravlt_b1")
        a6 = st.number_input("A6 (evocação imediata):", 0, 15, int(pre.get("A6", 0)), key="ravlt_a6")
        a7 = st.number_input("A7 (evocação tardia):", 0, 15, int(pre.get("A7", 0)), key="ravlt_a7")
    with col3:
        rec_hits = st.number_input("Reconhecimento — Acertos:", 0, 15, int(pre.get("rec_hits", 0)), key="ravlt_rec_h")
        rec_fa   = st.number_input("Reconhecimento — Falsos alarmes:", 0, 15, int(pre.get("rec_fa", 0)), key="ravlt_rec_fa")

    if st.button("Calcular RAVLT", type="primary", key="btn_ravlt"):
        dados = {"A1": a1, "A2": a2, "A3": a3, "A4": a4, "A5": a5,
                 "B1": b1, "A6": a6, "A7": a7, "rec_hits": rec_hits, "rec_fa": rec_fa}
        escores, interp, padrao, confianca = calcular_escores(dados, idade, anos_esc, pop_key)
        escores["padrao"] = padrao  # guardar para insights
        salvar_resultado_teste(avaliacao_id, "RAVLT", dados, escores, interp, confianca)
        st.success("RAVLT calculado e salvo!")
        _mostrar_resultado_inline(escores, interp, confianca)


def _form_fdt(avaliacao_id, idade, anos_esc, existentes):
    from testes.fdt_tmt import calcular_fdt

    st.markdown("#### FDT — Five Digit Test")
    st.caption("Informe o tempo (em segundos) e número de erros em cada condição.")

    dados_prev = existentes.get("FDT", {}).get("dados_brutos", {})
    foto_dados = st.session_state.get("dados_foto_FDT", {})
    pre = {**dados_prev, **foto_dados}

    populacao = st.radio("Faixa etária:", ["Adulto (18+)", "Criança/Adolescente (<18)"], horizontal=True, key="fdt_pop")
    pop_key = "adulto" if "Adulto" in populacao else "infantil"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Tempos (segundos):**")
        t_con = st.number_input("Contar — tempo:", 0.0, 300.0, float(pre.get("contar_tempo", 0.0)), 0.1, key="fdt_t_con")
        t_ler = st.number_input("Ler — tempo:", 0.0, 300.0, float(pre.get("ler_tempo", 0.0)), 0.1, key="fdt_t_ler")
        t_esc = st.number_input("Escolher — tempo:", 0.0, 300.0, float(pre.get("escolher_tempo", 0.0)), 0.1, key="fdt_t_esc")
        t_alt = st.number_input("Alternar — tempo:", 0.0, 300.0, float(pre.get("alternar_tempo", 0.0)), 0.1, key="fdt_t_alt")
    with col2:
        st.markdown("**Erros:**")
        e_con = st.number_input("Contar — erros:", 0, 50, int(pre.get("contar_erros", 0)), key="fdt_e_con")
        e_ler = st.number_input("Ler — erros:", 0, 50, int(pre.get("ler_erros", 0)), key="fdt_e_ler")
        e_esc = st.number_input("Escolher — erros:", 0, 50, int(pre.get("escolher_erros", 0)), key="fdt_e_esc")
        e_alt = st.number_input("Alternar — erros:", 0, 50, int(pre.get("alternar_erros", 0)), key="fdt_e_alt")

    if st.button("Calcular FDT", type="primary", key="btn_fdt"):
        dados = {
            "contar_tempo": t_con, "contar_erros": e_con,
            "ler_tempo": t_ler, "ler_erros": e_ler,
            "escolher_tempo": t_esc, "escolher_erros": e_esc,
            "alternar_tempo": t_alt, "alternar_erros": e_alt,
        }
        escores, interp, confianca = calcular_fdt(dados, idade, anos_esc, pop_key)
        salvar_resultado_teste(avaliacao_id, "FDT", dados, escores, interp, confianca)
        st.success("FDT calculado e salvo!")
        _mostrar_resultado_inline(escores, interp, confianca)


def _form_tmt(avaliacao_id, idade, anos_esc, existentes):
    from testes.fdt_tmt import calcular_tmt

    st.markdown("#### TMT — Trail Making Test")

    dados_prev = existentes.get("TMT", {}).get("dados_brutos", {})
    pre = dados_prev or {}

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Parte A:**")
        t_a = st.number_input("Tempo (segundos):", 0.0, 600.0, float(pre.get("tempo_a", 0.0)), 0.1, key="tmt_ta")
        e_a = st.number_input("Erros:", 0, 50, int(pre.get("erros_a", 0)), key="tmt_ea")
    with col2:
        st.markdown("**Parte B:**")
        t_b = st.number_input("Tempo (segundos):", 0.0, 600.0, float(pre.get("tempo_b", 0.0)), 0.1, key="tmt_tb")
        e_b = st.number_input("Erros:", 0, 50, int(pre.get("erros_b", 0)), key="tmt_eb")

    if st.button("Calcular TMT", type="primary", key="btn_tmt"):
        dados = {"tempo_a": t_a, "erros_a": e_a, "tempo_b": t_b, "erros_b": e_b}
        escores, interp, confianca = calcular_tmt(dados, idade, anos_esc)
        salvar_resultado_teste(avaliacao_id, "TMT", dados, escores, interp, confianca)
        st.success("TMT calculado e salvo!")
        _mostrar_resultado_inline(escores, interp, confianca)


def _form_srs2(avaliacao_id, idade, sexo, existentes):
    from testes.srs2 import calcular_srs2, SUBSCALAS_ITENS

    st.markdown("#### SRS-2 — Escala de Responsividade Social")
    st.warning("⚠️ Normas americanas. Interpretar com cautela — sem normas brasileiras publicadas.")

    informante = st.selectbox("Informante:", ["Pais", "Professor", "Autoaplicação"], key="srs2_inf")
    sexo_input = st.radio("Sexo do paciente:", ["M", "F"], horizontal=True,
                          index=0 if sexo == "M" else 1, key="srs2_sex")

    st.caption("Pontuação: 1=Nunca, 2=Às vezes, 3=Frequentemente, 4=Sempre")

    dados_prev = existentes.get("SRS2", {}).get("dados_brutos", {})
    resps_prev = dados_prev.get("respostas_itens", {})

    respostas = {}
    for subscala, itens in SUBSCALAS_ITENS.items():
        with st.expander(f"**{subscala}** ({len(itens)} itens)"):
            for item_n in itens:
                val_prev = int(resps_prev.get(str(item_n), 1))
                respostas[item_n] = st.slider(
                    f"Item {item_n}", 1, 4, val_prev, key=f"srs2_{item_n}"
                )

    if st.button("Calcular SRS-2", type="primary", key="btn_srs2"):
        escores, interp, confianca = calcular_srs2(respostas, sexo_input, idade, informante.lower())
        dados_brutos = {"respostas_itens": {str(k): v for k, v in respostas.items()}, "informante": informante}
        salvar_resultado_teste(avaliacao_id, "SRS2", dados_brutos, escores, interp, confianca)
        st.success("SRS-2 calculado e salvo!")
        _mostrar_resultado_inline(escores, interp, confianca)


def _form_etdah(avaliacao_id, idade, existentes):
    from testes.etdah import calcular_etdah, ETDAH_ITENS_DESATENCAO, ETDAH_ITENS_HI, FREQUENCIAS

    st.markdown("#### ETDAH — Escala de Avaliação de TDAH (DSM-5)")

    informante = st.selectbox("Informante:", ["Pais", "Professor", "Autoaplicação"], key="etdah_inf")
    st.caption("Frequência: 0=Nunca, 1=Raramente, 2=Às vezes, 3=Frequentemente, 4=Sempre")

    dados_prev = existentes.get("ETDAH", {}).get("dados_brutos", {})
    d_prev = dados_prev.get("desatencao", [0]*9)
    h_prev = dados_prev.get("hi", [0]*9)

    col1, col2 = st.columns(2)
    res_d = []
    res_h = []

    with col1:
        st.markdown("**DESATENÇÃO (9 itens):**")
        for i, item in enumerate(ETDAH_ITENS_DESATENCAO):
            val = st.select_slider(
                f"D{i+1}: {item[:50]}...",
                options=[0, 1, 2, 3, 4],
                value=int(d_prev[i]) if i < len(d_prev) else 0,
                format_func=lambda x: f"{x} - {FREQUENCIAS[x]}",
                key=f"etdah_d{i}",
            )
            res_d.append(val)

    with col2:
        st.markdown("**HIPERATIVIDADE/IMPULSIVIDADE (9 itens):**")
        for i, item in enumerate(ETDAH_ITENS_HI):
            val = st.select_slider(
                f"H{i+1}: {item[:50]}...",
                options=[0, 1, 2, 3, 4],
                value=int(h_prev[i]) if i < len(h_prev) else 0,
                format_func=lambda x: f"{x} - {FREQUENCIAS[x]}",
                key=f"etdah_h{i}",
            )
            res_h.append(val)

    if st.button("Calcular ETDAH", type="primary", key="btn_etdah"):
        escores, interp, confianca = calcular_etdah(res_d, res_h, idade, informante.lower())
        dados_brutos = {"desatencao": res_d, "hi": res_h, "informante": informante}
        salvar_resultado_teste(avaliacao_id, "ETDAH", dados_brutos, escores, interp, confianca)
        st.success("ETDAH calculado e salvo!")
        _mostrar_resultado_inline(escores, interp, confianca)


def _form_bdi2(avaliacao_id, existentes):
    from testes.bdi2_bai import calcular_bdi2, BDI2_ITENS

    st.markdown("#### BDI-II — Inventário de Depressão de Beck")
    st.caption("Para cada item, selecione a afirmativa que melhor descreve como o paciente se sentiu nas últimas 2 semanas (0–3).")

    dados_prev = existentes.get("BDI2", {}).get("dados_brutos", {})
    resps_prev = dados_prev.get("respostas", [0]*21)

    foto_dados = st.session_state.get("dados_foto_BDI2", {})
    if foto_dados.get("respostas"):
        resps_prev = foto_dados["respostas"]

    respostas = []
    for i, item in enumerate(BDI2_ITENS):
        val_prev = int(resps_prev[i]) if i < len(resps_prev) and resps_prev[i] is not None else 0
        val = st.select_slider(
            f"**{i+1}. {item}**",
            options=[0, 1, 2, 3],
            value=val_prev,
            key=f"bdi2_{i}",
        )
        respostas.append(val)

    if st.button("Calcular BDI-II", type="primary", key="btn_bdi2"):
        escores, interp, confianca = calcular_bdi2(respostas)
        dados_brutos = {"respostas": respostas}
        salvar_resultado_teste(avaliacao_id, "BDI2", dados_brutos, escores, interp, confianca)
        st.success("BDI-II calculado e salvo!")
        _mostrar_resultado_inline(escores, interp, confianca)


def _form_bai(avaliacao_id, existentes):
    from testes.bdi2_bai import calcular_bai, BAI_ITENS

    st.markdown("#### BAI — Inventário de Ansiedade de Beck")
    st.caption("Indique o quanto foi incomodado por cada sintoma na última semana (0=Absolutamente não, 1=Levemente, 2=Moderadamente, 3=Gravemente).")

    dados_prev = existentes.get("BAI", {}).get("dados_brutos", {})
    resps_prev = dados_prev.get("respostas", [0]*21)

    foto_dados = st.session_state.get("dados_foto_BAI", {})
    if foto_dados.get("respostas"):
        resps_prev = foto_dados["respostas"]

    respostas = []
    rotulos = ["0 - Absolutamente não", "1 - Levemente", "2 - Moderadamente", "3 - Gravemente"]
    for i, item in enumerate(BAI_ITENS):
        val_prev = int(resps_prev[i]) if i < len(resps_prev) and resps_prev[i] is not None else 0
        val = st.select_slider(
            f"**{i+1}. {item}**",
            options=[0, 1, 2, 3],
            value=val_prev,
            format_func=lambda x: rotulos[x],
            key=f"bai_{i}",
        )
        respostas.append(val)

    if st.button("Calcular BAI", type="primary", key="btn_bai"):
        escores, interp, confianca = calcular_bai(respostas)
        dados_brutos = {"respostas": respostas}
        salvar_resultado_teste(avaliacao_id, "BAI", dados_brutos, escores, interp, confianca)
        st.success("BAI calculado e salvo!")
        _mostrar_resultado_inline(escores, interp, confianca)


def _mostrar_resultado_inline(escores, interp, confianca):
    with st.expander("Ver resultado calculado", expanded=True):
        st.caption(f"Nível de confiança das normas: **{confianca}**")
        st.text(interp)


def _calcular_idade(data_nasc_str):
    if not data_nasc_str:
        return 35
    try:
        nasc = datetime.strptime(str(data_nasc_str)[:10], "%Y-%m-%d").date()
        hoje = date.today()
        return hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
    except Exception:
        return 35


def _extrair_anos_esc(escolaridade_str):
    import re
    m = re.search(r"(\d+)\s*anos", str(escolaridade_str))
    if m:
        return int(m.group(1))
    return 8
