"""
FDT — Five Digit Test  (Paula et al., 2012)
TMT — Trail Making Test (Campanholo et al., 2014)
Assertividade estimada: FDT 82-88% / TMT 85-90%
"""

from normas.tabelas import (
    FDT_NORMAS, FDT_NORMAS_INFANTIL,
    TMT_NORMAS,
    calcular_z_percentil, classificar_por_percentil,
    faixa_etaria_fdt, faixa_etaria_tmt, faixa_etaria_infantil_fdt,
    escolaridade_grupo,
)

FDT_CONFIANCA = "82-88%"
TMT_CONFIANCA = "85-90%"


# ──────────────────────────────────────────────────────────────────────────────
# FDT
# ──────────────────────────────────────────────────────────────────────────────

def calcular_fdt(dados, idade, anos_escolaridade, populacao="adulto"):
    """
    dados: dict com chaves: contar_tempo, contar_erros, ler_tempo, ler_erros,
                            escolher_tempo, escolher_erros, alternar_tempo, alternar_erros
    """
    t_con = dados.get("contar_tempo", 0)
    e_con = dados.get("contar_erros", 0)
    t_ler = dados.get("ler_tempo", 0)
    e_ler = dados.get("ler_erros", 0)
    t_esc = dados.get("escolher_tempo", 0)
    e_esc = dados.get("escolher_erros", 0)
    t_alt = dados.get("alternar_tempo", 0)
    e_alt = dados.get("alternar_erros", 0)

    # Índices derivados (Sedó, 2004)
    base_media = (t_con + t_ler) / 2 if (t_con + t_ler) > 0 else 1
    inibicao   = t_esc - t_con
    flexib     = t_alt - base_media

    # Norma
    if populacao == "adulto":
        faixa = faixa_etaria_fdt(idade)
        esc   = escolaridade_grupo(anos_escolaridade)
        tabela = FDT_NORMAS.get((faixa, esc), FDT_NORMAS[("40-59", "media")])
    else:
        faixa = faixa_etaria_infantil_fdt(idade)
        tabela = FDT_NORMAS_INFANTIL.get((faixa, "fundamental"), FDT_NORMAS_INFANTIL[("10-11", "fundamental")])

    def processar_condicao(nome_chave, tempo_val, erros_val):
        m_t, dp_t, m_e, dp_e = tabela[nome_chave]
        # Para tempo: escore alto = pior desempenho → inverter para percentil
        z_t_inv, pct_t = calcular_z_percentil(-tempo_val, -m_t, dp_t)
        z_e_inv, pct_e = calcular_z_percentil(-erros_val, -m_e, dp_e) if dp_e > 0 else (0.0, 50.0)
        classif, _     = classificar_por_percentil(pct_t)
        return {
            "tempo": tempo_val, "erros": erros_val,
            "percentil_tempo": pct_t, "classificacao": classif,
        }

    cond = {
        "contar":   processar_condicao("contar",   t_con, e_con),
        "ler":      processar_condicao("ler",       t_ler, e_ler),
        "escolher": processar_condicao("escolher",  t_esc, e_esc),
        "alternar": processar_condicao("alternar",  t_alt, e_alt),
    }

    escores = {
        "condicoes": cond,
        "inibicao": round(inibicao, 1),
        "flexibilidade": round(flexib, 1),
        "norma_usada": f"{faixa} anos / escolaridade {esc if populacao == 'adulto' else 'infantil'}",
        "populacao": populacao,
    }

    interpretacao = _interpretar_fdt(cond, inibicao, flexib)
    return escores, interpretacao, FDT_CONFIANCA


def _interpretar_fdt(cond, inibicao, flexib):
    linhas = []

    linhas.append("=== FDT — Five Digit Test ===")
    for nome, dados in cond.items():
        linhas.append(
            f"  {nome.capitalize()}: {dados['tempo']:.1f}s / {dados['erros']} erros "
            f"[Percentil {dados['percentil_tempo']:.0f} — {dados['classificacao']}]"
        )

    linhas.append(f"\nÍndice de Inibição (Escolher − Contar): {inibicao:.1f}s")
    if inibicao > 30:
        linhas.append("  → Inibição significativamente aumentada: dificuldade no controle inibitório.")
    elif inibicao > 15:
        linhas.append("  → Inibição moderadamente aumentada: possível lentificação no controle de respostas automáticas.")
    else:
        linhas.append("  → Controle inibitório adequado.")

    linhas.append(f"\nÍndice de Flexibilidade (Alternar − média Contar/Ler): {flexib:.1f}s")
    if flexib > 40:
        linhas.append("  → Flexibilidade cognitiva significativamente comprometida.")
    elif flexib > 20:
        linhas.append("  → Flexibilidade cognitiva moderadamente reduzida.")
    else:
        linhas.append("  → Flexibilidade cognitiva preservada.")

    v_con = cond["contar"]["percentil_tempo"]
    v_ler = cond["ler"]["percentil_tempo"]
    if v_con < 25 and v_ler < 25:
        linhas.append("\nVelocidade de processamento basal rebaixada (Contar e Ler comprometidos).")

    return "\n".join(linhas)


# ──────────────────────────────────────────────────────────────────────────────
# TMT
# ──────────────────────────────────────────────────────────────────────────────

def calcular_tmt(dados, idade, anos_escolaridade):
    """
    dados: dict com tempo_a (s), erros_a, tempo_b (s), erros_b
    """
    t_a = dados.get("tempo_a", 0)
    e_a = dados.get("erros_a", 0)
    t_b = dados.get("tempo_b", 0)
    e_b = dados.get("erros_b", 0)

    faixa = faixa_etaria_tmt(idade)
    esc   = escolaridade_grupo(anos_escolaridade)
    norma = TMT_NORMAS.get((faixa, esc), TMT_NORMAS[("40-59", "media")])

    # Maior tempo = pior → inverter para percentil
    z_a, pct_a = calcular_z_percentil(-t_a, -norma["A"][0], norma["A"][1])
    z_b, pct_b = calcular_z_percentil(-t_b, -norma["B"][0], norma["B"][1])

    classif_a, _ = classificar_por_percentil(pct_a)
    classif_b, _ = classificar_por_percentil(pct_b)

    razao_ba = round(t_b / t_a, 2) if t_a > 0 else None

    escores = {
        "tempo_a": t_a, "erros_a": e_a,
        "tempo_b": t_b, "erros_b": e_b,
        "razao_B_A": razao_ba,
        "percentil_a": pct_a, "classificacao_a": classif_a,
        "percentil_b": pct_b, "classificacao_b": classif_b,
        "norma_usada": f"{faixa} anos / escolaridade {esc}",
    }

    interpretacao = _interpretar_tmt(escores)
    return escores, interpretacao, TMT_CONFIANCA


def _interpretar_tmt(e):
    linhas = ["=== TMT — Trail Making Test ==="]
    linhas.append(
        f"Parte A: {e['tempo_a']:.1f}s / {e['erros_a']} erros "
        f"[Percentil {e['percentil_a']:.0f} — {e['classificacao_a']}]"
    )
    linhas.append(
        f"Parte B: {e['tempo_b']:.1f}s / {e['erros_b']} erros "
        f"[Percentil {e['percentil_b']:.0f} — {e['classificacao_b']}]"
    )

    if e["razao_B_A"]:
        linhas.append(f"\nRazão B/A: {e['razao_B_A']:.2f}")
        if e["razao_B_A"] > 3.5:
            linhas.append(
                "  → Razão B/A elevada: dificuldade desproporcional na alternância atencional "
                "em relação à velocidade de processamento basal — sugere comprometimento executivo-frontal."
            )
        elif e["razao_B_A"] > 2.5:
            linhas.append("  → Razão B/A moderadamente elevada: possível dificuldade de alternância cognitiva.")
        else:
            linhas.append("  → Razão B/A dentro do esperado.")

    if e["percentil_a"] < 25:
        linhas.append("\nTMT-A rebaixado: lentificação na velocidade de processamento visuomotora e/ou atenção sustentada básica.")

    if e["percentil_b"] < 25 and e["percentil_a"] >= 25:
        linhas.append("\nTMT-B rebaixado com TMT-A preservado: dificuldade específica em alternância cognitiva / flexibilidade executiva.")

    return "\n".join(linhas)
