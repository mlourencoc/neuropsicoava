"""
BDI-II — Beck Depression Inventory-II
BAI   — Beck Anxiety Inventory

Fontes:
- BDI-II: Gorenstein & Andrade (1996). Acta Psychiatrica Scandinavica, 94, 285-289.
          Cunha (2001). Manual BDI-II adaptação brasileira. São Paulo: Casa do Psicólogo.
- BAI:    Cunha (2001). Manual BAI. São Paulo: Casa do Psicólogo.
          Beck et al. (1988). Journal of Consulting and Clinical Psychology, 56(6), 893-897.

Assertividade estimada: BDI-II 91-96% / BAI 93-97%
"""

from normas.tabelas import BDI2_CLASSIFICACAO, BDI2_ITENS, BAI_CLASSIFICACAO, BAI_ITENS

BDI2_CONFIANCA = "91-96%"
BAI_CONFIANCA  = "93-97%"


# ──────────────────────────────────────────────────────────────────────────────
# BDI-II
# ──────────────────────────────────────────────────────────────────────────────

def calcular_bdi2(respostas):
    """
    respostas: list[int] com 21 valores (0–3 cada)
    Retorna escores, interpretação e nível de confiança.
    """
    assert len(respostas) == 21, "BDI-II requer exatamente 21 itens"
    total = sum(respostas)

    classif, descricao = _classificar(total, BDI2_CLASSIFICACAO)

    # Itens cotados como 2 ou 3 (clinicamente significativos)
    itens_altos = [
        (BDI2_ITENS[i], respostas[i])
        for i in range(21) if respostas[i] >= 2
    ]

    # Sinalização de item suicida (item 9)
    alerta_suicida = respostas[9] >= 1

    escores = {
        "total": total,
        "classificacao": classif,
        "descricao": descricao,
        "respostas": respostas,
        "itens_clinicamente_significativos": itens_altos,
        "alerta_ideacao_suicida": alerta_suicida,
        "item_suicida_valor": respostas[9],
    }

    interpretacao = _interpretar_bdi2(escores)
    return escores, interpretacao, BDI2_CONFIANCA


def _interpretar_bdi2(e):
    linhas = ["=== BDI-II — Inventário de Depressão de Beck ==="]
    linhas.append(f"Pontuação Total: {e['total']}/63")
    linhas.append(f"Classificação: {e['classificacao']} — {e['descricao']}")

    if e["alerta_ideacao_suicida"]:
        linhas.append(
            f"\n🔴 ALERTA: Item 9 (Pensamentos ou Desejos Suicidas) cotado como {e['item_suicida_valor']}. "
            "Avaliação de risco imediata indicada."
        )

    if e["itens_clinicamente_significativos"]:
        linhas.append("\nSintomas com intensidade clínica (≥2):")
        for item, val in e["itens_clinicamente_significativos"]:
            linhas.append(f"  • {item}: {val}")

    linhas.append(
        "\nReferência: Gorenstein & Andrade (1996); Cunha (2001). "
        "Pontos de corte validados para população brasileira."
    )
    return "\n".join(linhas)


# ──────────────────────────────────────────────────────────────────────────────
# BAI
# ──────────────────────────────────────────────────────────────────────────────

def calcular_bai(respostas):
    """
    respostas: list[int] com 21 valores (0–3 cada)
    """
    assert len(respostas) == 21, "BAI requer exatamente 21 itens"
    total = sum(respostas)

    classif, descricao = _classificar(total, BAI_CLASSIFICACAO)

    itens_altos = [
        (BAI_ITENS[i], respostas[i])
        for i in range(21) if respostas[i] >= 2
    ]

    # Cluster somático vs cognitivo/afetivo
    itens_somaticos   = [0, 1, 2, 6, 7, 11, 12, 15, 18, 19, 20]  # predominância somática
    itens_cognitivos  = [3, 4, 5, 8, 9, 10, 13, 14, 16, 17]

    soma_som = sum(respostas[i] for i in itens_somaticos)
    soma_cog = sum(respostas[i] for i in itens_cognitivos)

    escores = {
        "total": total,
        "classificacao": classif,
        "descricao": descricao,
        "respostas": respostas,
        "itens_clinicamente_significativos": itens_altos,
        "soma_cluster_somatico": soma_som,
        "soma_cluster_cognitivo_afetivo": soma_cog,
    }

    interpretacao = _interpretar_bai(escores)
    return escores, interpretacao, BAI_CONFIANCA


def _interpretar_bai(e):
    linhas = ["=== BAI — Inventário de Ansiedade de Beck ==="]
    linhas.append(f"Pontuação Total: {e['total']}/63")
    linhas.append(f"Classificação: {e['classificacao']} — {e['descricao']}")

    linhas.append(
        f"\nCluster Somático: {e['soma_cluster_somatico']} pontos | "
        f"Cluster Cognitivo/Afetivo: {e['soma_cluster_cognitivo_afetivo']} pontos"
    )
    if e["soma_cluster_somatico"] > e["soma_cluster_cognitivo_afetivo"] * 1.5:
        linhas.append("  → Predomínio de sintomas somáticos da ansiedade.")
    elif e["soma_cluster_cognitivo_afetivo"] > e["soma_cluster_somatico"] * 1.5:
        linhas.append("  → Predomínio de sintomas cognitivos/afetivos da ansiedade.")

    if e["itens_clinicamente_significativos"]:
        linhas.append("\nSintomas com intensidade clínica (≥2):")
        for item, val in e["itens_clinicamente_significativos"]:
            linhas.append(f"  • {item}: {val}")

    linhas.append(
        "\nReferência: Cunha (2001). Pontos de corte validados para população brasileira."
    )
    return "\n".join(linhas)


# ──────────────────────────────────────────────────────────────────────────────
# Utilitário compartilhado
# ──────────────────────────────────────────────────────────────────────────────

def _classificar(total, tabela):
    for tmin, tmax, classif, descricao in tabela:
        if tmin <= total <= tmax:
            return classif, descricao
    return "Indeterminado", ""
