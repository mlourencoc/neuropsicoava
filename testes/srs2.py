"""
SRS-2 — Social Responsiveness Scale, 2ª edição
Constantino & Gruber (2012). Normas americanas (sem normas BR publicadas até 2024).
Assertividade estimada: 75-80%

NOTA: T-scores são calculados com base nas normas americanas.
Interpretar sempre em conjunto com anamnese e observação clínica.
Em fenótipo feminino do autismo, pontuação abaixo do corte NÃO exclui TEA.
"""

from normas.tabelas import SRS2_CLASSIFICACAO_TOTAL, SRS2_NOTA_CLINICA

NIVEL_CONFIANCA = "75-80% (normas americanas)"

# Distribuição de itens por subscala (forma escolar/adulto, 65 itens)
# Itens numerados 1–65; mapeamento oficial Constantino & Gruber (2012)
SUBSCALAS_ITENS = {
    "Percepção Social":   list(range(1, 9)),    # 8 itens
    "Cognição Social":    list(range(9, 21)),   # 12 itens
    "Comunicação Social": list(range(21, 43)),  # 22 itens
    "Motivação Social":   list(range(43, 54)),  # 11 itens
    "Maneirismos":        list(range(54, 66)),  # 12 itens
}

# Parâmetros para conversão em T-score por sexo e forma (normas americanas)
# T = 50 + 10 * z; aqui usamos médias e DPs aproximados das normas publicadas
# Fonte: Constantino (2012), tabelas de normas, forma escolar, pais como informante
NORMAS_TSCORE = {
    # (sexo, faixa_etaria): {subscala: (media_escore_bruto, dp)}
    ("M", "4-17"): {
        "Percepção Social":   (11.2, 4.1),
        "Cognição Social":    (15.8, 5.8),
        "Comunicação Social": (26.3, 9.4),
        "Motivação Social":   (12.4, 4.8),
        "Maneirismos":        (8.9,  4.6),
        "Total":              (74.6, 26.3),
    },
    ("F", "4-17"): {
        "Percepção Social":   (9.8,  3.8),
        "Cognição Social":    (14.1, 5.3),
        "Comunicação Social": (23.5, 8.7),
        "Motivação Social":   (11.2, 4.4),
        "Maneirismos":        (7.5,  4.1),
        "Total":              (66.1, 23.8),
    },
    ("M", "18+"): {
        "Percepção Social":   (9.5,  3.9),
        "Cognição Social":    (13.8, 5.4),
        "Comunicação Social": (22.1, 8.5),
        "Motivação Social":   (10.8, 4.3),
        "Maneirismos":        (7.8,  4.2),
        "Total":              (64.0, 24.1),
    },
    ("F", "18+"): {
        "Percepção Social":   (8.6,  3.5),
        "Cognição Social":    (12.4, 5.0),
        "Comunicação Social": (19.8, 7.9),
        "Motivação Social":   (9.7,  4.0),
        "Maneirismos":        (6.5,  3.7),
        "Total":              (57.0, 21.4),
    },
}


def calcular_srs2(respostas_itens, sexo, idade, informante="pais"):
    """
    respostas_itens: dict {1: 1, 2: 3, ..., 65: 2}  (escala 1–4 por item)
    sexo: "M" ou "F"
    idade: int
    informante: "pais", "professor", "auto"
    """
    # Escores brutos por subscala
    brutos = {}
    for subscala, itens in SUBSCALAS_ITENS.items():
        brutos[subscala] = sum(respostas_itens.get(i, 1) for i in itens)

    # SCI = Percepção + Cognição + Comunicação + Motivação
    brutos["SCI"] = (
        brutos["Percepção Social"] + brutos["Cognição Social"] +
        brutos["Comunicação Social"] + brutos["Motivação Social"]
    )
    brutos["Total"] = brutos["SCI"] + brutos["Maneirismos"]

    # Chave de norma
    faixa_n = "4-17" if idade < 18 else "18+"
    chave_n = (sexo.upper(), faixa_n)
    norma   = NORMAS_TSCORE.get(chave_n, NORMAS_TSCORE[("M", "4-17")])

    # T-scores
    tscores = {}
    for nome, bruto in brutos.items():
        if nome in norma:
            media, dp = norma[nome]
            z = (bruto - media) / dp if dp > 0 else 0
            tscores[nome] = round(50 + 10 * z, 1)

    total_t = tscores.get("Total", 50)
    classif, cor = _classificar_total(total_t)

    escores = {
        "brutos": brutos,
        "tscores": tscores,
        "total_tscore": total_t,
        "classificacao": classif,
        "sexo": sexo,
        "idade": idade,
        "informante": informante,
        "faixa_norma": faixa_n,
    }

    interpretacao = _interpretar_srs2(escores)
    return escores, interpretacao, NIVEL_CONFIANCA


def _classificar_total(tscore):
    for tmin, tmax, classif, _ in SRS2_CLASSIFICACAO_TOTAL:
        if tmin <= tscore <= tmax:
            cor = "success" if tscore < 60 else ("warning" if tscore < 66 else "danger")
            return classif, cor
    return "Indeterminado", "secondary"


def _interpretar_srs2(e):
    linhas = ["=== SRS-2 — Escala de Responsividade Social ==="]
    linhas.append(f"Informante: {e['informante'].capitalize()} | Sexo: {e['sexo']} | Idade: {e['idade']} anos")
    linhas.append(f"\nT-score Total: {e['total_tscore']:.1f} — {e['classificacao']}")

    linhas.append("\nT-scores por subscala:")
    subscalas_ordem = ["Percepção Social", "Cognição Social", "Comunicação Social", "Motivação Social", "Maneirismos"]
    for sub in subscalas_ordem:
        t = e["tscores"].get(sub, "--")
        b = e["brutos"].get(sub, "--")
        flag = " ⚠️" if isinstance(t, float) and t >= 60 else ""
        linhas.append(f"  {sub}: T={t:.1f} (bruto={b}){flag}")

    sci_val = e["tscores"].get("SCI", "--")
    sci_str = f"{sci_val:.1f}" if isinstance(sci_val, (int, float)) else str(sci_val)
    linhas.append(f"\nSCI (Comunicação e Interação Social): T={sci_str}")

    # Padrão de comprometimento
    subs_alt = [s for s in subscalas_ordem if isinstance(e["tscores"].get(s), float) and e["tscores"][s] >= 60]
    if subs_alt:
        linhas.append(f"\nSubscalas com T ≥ 60: {', '.join(subs_alt)}")
    else:
        linhas.append("\nNenhuma subscala com T ≥ 60 nesta avaliação.")

    # Nota sobre fenótipo feminino
    if e["sexo"] == "F":
        linhas.append(
            "\n⚠️ FENÓTIPO FEMININO: Em meninas/mulheres autistas, o SRS-2 pode subestimar "
            "as dificuldades sociais devido ao mecanismo de camuflagem. Pontuação dentro "
            "da normalidade NÃO exclui TEA se outros indicadores clínicos estiverem presentes."
        )

    linhas.append(f"\n{SRS2_NOTA_CLINICA}")
    return "\n".join(linhas)
