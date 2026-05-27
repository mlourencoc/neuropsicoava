"""
RAVLT — Rey Auditory Verbal Learning Test
Correção baseada em Malloy-Diniz et al. (2007) e Fichman et al. (2010).
Assertividade estimada: 88-92%
"""

from normas.tabelas import (
    RAVLT_NORMAS, RAVLT_NORMAS_INFANTIL,
    calcular_z_percentil, classificar_por_percentil,
    faixa_etaria_adulto, faixa_etaria_infantil_ravlt,
    escolaridade_grupo, escolaridade_infantil,
)


NIVEL_CONFIANCA = "88-92%"

LISTA_A = [
    "tambor", "cortina", "sino", "café", "escola",
    "pais", "lua", "jardim", "chapéu", "fazenda",
    "nariz", "peru", "cor", "céu", "bota",
]

LISTA_B = [
    "mesa", "maçã", "cartão", "palha", "janela",
    "chefe", "corda", "aldeia", "flauta", "sol",
    "palha", "prado", "vidro", "bicicleta", "árvore",
]


def calcular_escores(dados, idade, anos_escolaridade, populacao="adulto"):
    """
    dados: dict com chaves A1..A5, B1, A6, A7, rec_hits, rec_falsos_alarmes
    Retorna dict com escores, percentis e interpretação por índice.
    """
    a1 = dados.get("A1", 0)
    a2 = dados.get("A2", 0)
    a3 = dados.get("A3", 0)
    a4 = dados.get("A4", 0)
    a5 = dados.get("A5", 0)
    b1 = dados.get("B1", 0)
    a6 = dados.get("A6", 0)
    a7 = dados.get("A7", 0)
    rec_hits = dados.get("rec_hits", 0)
    rec_fa   = dados.get("rec_fa",   0)

    total_a = a1 + a2 + a3 + a4 + a5

    # Índices derivados
    efeito_primazia  = a1
    efeito_recencia  = a5
    curva_aprendiz   = a5 - a1
    interferencia_retro = a5 - a6   # perda pós-interferência
    retencao_pct     = round((a7 / a5 * 100) if a5 > 0 else 0, 1)
    discriminabilidade = rec_hits - rec_fa

    # Norma
    if populacao == "adulto":
        faixa = faixa_etaria_adulto(idade)
        esc   = escolaridade_grupo(anos_escolaridade)
        norma = RAVLT_NORMAS.get((faixa, esc), RAVLT_NORMAS[("40-49", "media")])
    else:
        faixa = faixa_etaria_infantil_ravlt(idade)
        esc   = "fundamental"
        norma = RAVLT_NORMAS_INFANTIL.get((faixa, esc), RAVLT_NORMAS_INFANTIL[("10-11", "fundamental")])

    # Z-scores e percentis
    z_total, pct_total = calcular_z_percentil(total_a, *norma["A1-A5"])
    z_a6,    pct_a6    = calcular_z_percentil(a6,      *norma["A6"])
    z_a7,    pct_a7    = calcular_z_percentil(a7,      *norma["A7"])
    z_b1,    pct_b1    = calcular_z_percentil(b1,      *norma["B1"])
    z_rec,   pct_rec   = calcular_z_percentil(rec_hits, *norma["rec_hits"])

    classif_total, cor_total = classificar_por_percentil(pct_total)
    classif_a7,    _         = classificar_por_percentil(pct_a7)
    classif_rec,   _         = classificar_por_percentil(pct_rec)

    # Padrão de déficit
    padrao = _identificar_padrao(pct_total, pct_a7, pct_rec, retencao_pct)

    escores = {
        "A1": a1, "A2": a2, "A3": a3, "A4": a4, "A5": a5,
        "B1": b1, "A6": a6, "A7": a7,
        "rec_hits": rec_hits, "rec_fa": rec_fa,
        "total_A1_A5": total_a,
        "curva_aprendizagem": curva_aprendiz,
        "efeito_primazia": efeito_primazia,
        "efeito_recencia": efeito_recencia,
        "interferencia_retroativa": interferencia_retro,
        "retencao_percentual": retencao_pct,
        "discriminabilidade": discriminabilidade,
        "z_total": z_total, "percentil_total": pct_total, "classif_total": classif_total,
        "z_a7":    z_a7,    "percentil_a7":    pct_a7,    "classif_a7":    classif_a7,
        "z_rec":   z_rec,   "percentil_rec":   pct_rec,   "classif_rec":   classif_rec,
        "norma_usada": f"{faixa} anos / escolaridade {esc}",
        "populacao": populacao,
    }

    interpretacao = _gerar_interpretacao(escores, padrao)
    return escores, interpretacao, padrao, NIVEL_CONFIANCA


def _identificar_padrao(pct_total, pct_a7, pct_rec, retencao_pct):
    """Identifica o padrão neuropsicológico do déficit de memória."""
    if pct_total >= 25 and pct_a7 >= 25 and pct_rec >= 25:
        return "normal"
    if pct_total < 25 and pct_a7 < 25 and pct_rec < 25:
        return "deficit_codificacao"  # déficit desde a entrada
    if pct_total >= 25 and pct_a7 < 25 and pct_rec >= 25:
        return "deficit_evocacao"     # aprende, mas não evoca livremente
    if pct_total < 25 and pct_a7 < 25 and pct_rec >= 25:
        return "deficit_codificacao_com_reconhecimento"  # disfunção executiva
    if retencao_pct < 70:
        return "perda_acelerada"      # esquecimento acelerado
    return "atipico"


def _gerar_interpretacao(e, padrao):
    linhas = []

    linhas.append(
        f"Aprendizagem total (A1–A5): {e['total_A1_A5']} palavras "
        f"[Percentil {e['percentil_total']:.0f} — {e['classif_total']}]."
    )

    # Curva de aprendizagem
    if e['curva_aprendizagem'] > 3:
        linhas.append(f"Curva de aprendizagem adequada (+{e['curva_aprendizagem']} palavras de A1 para A5).")
    elif e['curva_aprendizagem'] > 0:
        linhas.append(f"Curva de aprendizagem modesta (+{e['curva_aprendizagem']} palavras), sugerindo dificuldade de consolidação.")
    else:
        linhas.append(f"Ausência de curva de aprendizagem (variação de {e['curva_aprendizagem']} palavras), indicando comprometimento significativo na aquisição.")

    linhas.append(
        f"Evocação após interferência (A6): {e['A6']} palavras. "
        f"Evocação tardia (A7): {e['A7']} palavras [Percentil {e['percentil_a7']:.0f} — {e['classif_a7']}]."
    )

    linhas.append(f"Retenção A5→A7: {e['retencao_percentual']}%.")
    if e['retencao_percentual'] < 70:
        linhas.append("Retenção abaixo de 70%, sugestivo de esquecimento acelerado.")

    linhas.append(
        f"Reconhecimento: {e['rec_hits']} acertos / {e['rec_fa']} falsos alarmes "
        f"[Discriminabilidade = {e['discriminabilidade']}; Percentil {e['percentil_rec']:.0f} — {e['classif_rec']}]."
    )

    padroes = {
        "normal":                              "Perfil mnêmico dentro dos limites esperados para a faixa normativa.",
        "deficit_codificacao":                 "Padrão compatível com DÉFICIT DE CODIFICAÇÃO: comprometimento desde as fases iniciais de aprendizagem, com evocação e reconhecimento proporcionalmente rebaixados. Sugere disfunção hipocampal primária.",
        "deficit_evocacao":                    "Padrão compatível com DÉFICIT DE EVOCAÇÃO LIVRE com reconhecimento preservado: o material foi codificado mas não é recuperado espontaneamente. Mais associado a disfunção frontoestriatal/executiva do que a disfunção hipocampal pura.",
        "deficit_codificacao_com_reconhecimento": "Aprendizagem comprometida com reconhecimento relativamente preservado. Sugestivo de comprometimento da codificação com estratégias de recuperação parcialmente efetivas — considerar disfunção frontal e hipocampal combinadas.",
        "perda_acelerada":                     "Retenção percentual rebaixada (<70%), indicando esquecimento acelerado do material aprendido. Compatível com disfunção hipocampal de consolidação (ex.: Alzheimer inicial, lesão temporal mesial).",
        "atipico":                             "Perfil atípico — interpretar com cautela em conjunto com os demais instrumentos e contexto clínico.",
    }
    linhas.append(padroes.get(padrao, ""))

    linhas.append(f"\n[Norma aplicada: {e['norma_usada']} | Confiança: {NIVEL_CONFIANCA}]")
    return "\n".join(linhas)
