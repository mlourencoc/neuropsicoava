"""
ETDAH — Escala de Avaliação de TDAH baseada no DSM-5
Critérios DSM-5-TR (2022). Frequência: 0=Nunca, 1=Raramente, 2=Às vezes, 3=Frequentemente, 4=Sempre.
Para fins diagnósticos, considera-se clinicamente significativo o item com frequência ≥ 2.
Assertividade estimada: 88-92%
"""

from normas.tabelas import (
    ETDAH_ITENS_DESATENCAO, ETDAH_ITENS_HI, ETDAH_CRITERIO_DSM5
)

NIVEL_CONFIANCA = "88-92%"

FREQUENCIAS = {0: "Nunca", 1: "Raramente", 2: "Às vezes", 3: "Frequentemente", 4: "Sempre"}

# Limiar para contar sintoma como "presente" (DSM-5: "frequente" = limiar clínico)
LIMIAR_SINTOMA = 2  # ≥ 2 ("Às vezes") considerado clinicamente relevante


def calcular_etdah(respostas_desatencao, respostas_hi, idade, informante="pais"):
    """
    respostas_desatencao: list[int] com 9 valores (0-4)
    respostas_hi:         list[int] com 9 valores (0-4)
    idade: int
    informante: "pais", "professor", "auto"
    """
    assert len(respostas_desatencao) == 9, "Esperados 9 itens de desatenção"
    assert len(respostas_hi) == 9, "Esperados 9 itens de HI"

    total_d  = sum(respostas_desatencao)
    total_hi = sum(respostas_hi)
    total    = total_d + total_hi

    sint_d  = sum(1 for v in respostas_desatencao if v >= LIMIAR_SINTOMA)
    sint_hi = sum(1 for v in respostas_hi         if v >= LIMIAR_SINTOMA)

    # Limiar por faixa etária (DSM-5)
    criterio = ETDAH_CRITERIO_DSM5
    if idade <= 17:
        limiar = criterio["crianca_adolescente"]["limiar_sintomas"]  # 6
    else:
        limiar = criterio["adulto"]["limiar_sintomas"]               # 5

    # Apresentação segundo DSM-5
    crit_d  = sint_d  >= limiar
    crit_hi = sint_hi >= limiar

    if crit_d and crit_hi:
        apresentacao = "Combinada (F90.2)"
        dsm5_met = True
    elif crit_d:
        apresentacao = "Predominantemente Desatenta (F90.0)"
        dsm5_met = True
    elif crit_hi:
        apresentacao = "Predominantemente Hiperativa/Impulsiva (F90.1)"
        dsm5_met = True
    else:
        apresentacao = "Critérios quantitativos não atingidos"
        dsm5_met = False

    # Itens com sintoma presente
    itens_d_presentes  = [ETDAH_ITENS_DESATENCAO[i] for i, v in enumerate(respostas_desatencao) if v >= LIMIAR_SINTOMA]
    itens_hi_presentes = [ETDAH_ITENS_HI[i]         for i, v in enumerate(respostas_hi)         if v >= LIMIAR_SINTOMA]

    escores = {
        "total_desatencao": total_d,
        "total_hi": total_hi,
        "total": total,
        "sintomas_desatencao": sint_d,
        "sintomas_hi": sint_hi,
        "limiar_usado": limiar,
        "criterio_desatencao_met": crit_d,
        "criterio_hi_met": crit_hi,
        "criterios_quantitativos_met": dsm5_met,
        "apresentacao_sugerida": apresentacao,
        "itens_desatencao_presentes": itens_d_presentes,
        "itens_hi_presentes": itens_hi_presentes,
        "respostas_desatencao": respostas_desatencao,
        "respostas_hi": respostas_hi,
        "idade": idade,
        "informante": informante,
    }

    interpretacao = _interpretar_etdah(escores)
    return escores, interpretacao, NIVEL_CONFIANCA


def _interpretar_etdah(e):
    linhas = ["=== ETDAH — Escala de Avaliação de TDAH (DSM-5) ==="]
    linhas.append(f"Informante: {e['informante'].capitalize()} | Idade: {e['idade']} anos")
    linhas.append(f"Limiar de sintoma para esta faixa etária: ≥{e['limiar_usado']} sintomas")

    linhas.append(
        f"\nDesatenção: {e['sintomas_desatencao']}/9 sintomas presentes "
        f"(soma bruta: {e['total_desatencao']}) "
        f"{'✅ Critério atingido' if e['criterio_desatencao_met'] else '❌ Critério não atingido'}"
    )
    linhas.append(
        f"Hiperatividade/Impulsividade: {e['sintomas_hi']}/9 sintomas presentes "
        f"(soma bruta: {e['total_hi']}) "
        f"{'✅ Critério atingido' if e['criterio_hi_met'] else '❌ Critério não atingido'}"
    )

    linhas.append(f"\nApresentação sugerida (DSM-5): {e['apresentacao_sugerida']}")

    if e["itens_desatencao_presentes"]:
        linhas.append("\nSintomas de Desatenção presentes:")
        for item in e["itens_desatencao_presentes"]:
            linhas.append(f"  • {item}")

    if e["itens_hi_presentes"]:
        linhas.append("\nSintomas de HI presentes:")
        for item in e["itens_hi_presentes"]:
            linhas.append(f"  • {item}")

    linhas.append(
        "\n⚠️ ALERTAS CLÍNICOS (Barkley, 2022):\n"
        "• Esta escala avalia apenas os 18 sintomas do Critério A do DSM-5.\n"
        "• O TDAH é um transtorno de autorregulação — avaliar também: persistência, "
        "regulação emocional, motivação, memória de trabalho.\n"
        "• Critérios quantitativos atingidos NÃO equivalem a diagnóstico. "
        "Critérios B (início <12 anos), C (≥2 ambientes), D (prejuízo funcional) "
        "e E (exclusão diferencial) devem ser verificados na entrevista.\n"
        "• Comorbidade TDAH+TEA é substancial — investigar ativamente.\n"
        "• Em mulheres, usar escalas com normas subdivididas por sexo quando disponível."
    )

    return "\n".join(linhas)
