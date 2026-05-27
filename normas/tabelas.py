"""
Tabelas normativas brasileiras publicadas.

Fontes:
- RAVLT: Malloy-Diniz et al. (2007). Arq Neuropsiquiatr, 65(1), 119-123.
          + Fichman et al. (2010). Arq Neuropsiquiatr, 68(5), 685-689.
- FDT:   Paula et al. (2012). Psicologia: Reflexão e Crítica, 25(3), 563-571.
- TMT:   Campanholo et al. (2014). Dement Neuropsychol, 8(1), 26-34.
- BDI-II: Gorenstein & Andrade (1996/1998). Validação brasileira.
- BAI:   Cunha (2001). Manual BAI. São Paulo: Casa do Psicólogo.
- SRS-2: Constantino & Gruber (2012), normas EUA (sem normas brasileiras publicadas até 2024).
- ETDAH: Critérios DSM-5 — contagem de sintomas; sem normas contínuas.
"""

from scipy import stats
import numpy as np

# ──────────────────────────────────────────────────────────────────────────────
# RAVLT — Rey Auditory Verbal Learning Test
# Fonte: Malloy-Diniz et al. (2007) + Fichman et al. (2010)
# Estratificado por faixa etária e escolaridade
# ──────────────────────────────────────────────────────────────────────────────

# Estrutura: {(faixa_etaria, escolaridade): {variavel: (media, dp)}}
# faixa_etaria: "18-29", "30-39", "40-49", "50-59", "60-69", "70+"
# escolaridade: "baixa" (0-8 anos), "media" (9-11 anos), "alta" (12+ anos)

RAVLT_NORMAS = {
    # ─ 18–29 anos ─
    ("18-29", "baixa"):  {"A1-A5": (46.2, 7.1), "A6": (9.1, 2.8), "A7": (8.9, 2.9), "B1": (5.8, 1.9), "rec_hits": (13.5, 1.8)},
    ("18-29", "media"):  {"A1-A5": (50.1, 7.4), "A6": (10.2, 2.6), "A7": (10.0, 2.7), "B1": (6.1, 1.8), "rec_hits": (14.1, 1.4)},
    ("18-29", "alta"):   {"A1-A5": (53.8, 6.9), "A6": (11.1, 2.3), "A7": (10.8, 2.4), "B1": (6.4, 1.7), "rec_hits": (14.5, 1.2)},
    # ─ 30–39 anos ─
    ("30-39", "baixa"):  {"A1-A5": (44.8, 7.8), "A6": (8.8, 3.0), "A7": (8.5, 3.1), "B1": (5.6, 2.0), "rec_hits": (13.3, 1.9)},
    ("30-39", "media"):  {"A1-A5": (49.3, 7.5), "A6": (10.0, 2.7), "A7": (9.7, 2.8), "B1": (6.0, 1.9), "rec_hits": (13.9, 1.5)},
    ("30-39", "alta"):   {"A1-A5": (52.9, 7.0), "A6": (11.0, 2.4), "A7": (10.6, 2.5), "B1": (6.3, 1.7), "rec_hits": (14.4, 1.2)},
    # ─ 40–49 anos ─
    ("40-49", "baixa"):  {"A1-A5": (43.1, 8.2), "A6": (8.4, 3.2), "A7": (8.0, 3.3), "B1": (5.5, 2.1), "rec_hits": (12.9, 2.1)},
    ("40-49", "media"):  {"A1-A5": (47.5, 7.8), "A6": (9.6, 2.9), "A7": (9.2, 3.0), "B1": (5.9, 2.0), "rec_hits": (13.6, 1.7)},
    ("40-49", "alta"):   {"A1-A5": (51.2, 7.3), "A6": (10.5, 2.6), "A7": (10.2, 2.6), "B1": (6.2, 1.8), "rec_hits": (14.1, 1.4)},
    # ─ 50–59 anos ─
    ("50-59", "baixa"):  {"A1-A5": (40.5, 8.9), "A6": (7.8, 3.5), "A7": (7.3, 3.6), "B1": (5.2, 2.3), "rec_hits": (12.3, 2.4)},
    ("50-59", "media"):  {"A1-A5": (44.9, 8.5), "A6": (9.0, 3.1), "A7": (8.6, 3.2), "B1": (5.7, 2.1), "rec_hits": (13.1, 2.0)},
    ("50-59", "alta"):   {"A1-A5": (48.8, 8.0), "A6": (10.0, 2.8), "A7": (9.6, 2.9), "B1": (6.0, 1.9), "rec_hits": (13.7, 1.6)},
    # ─ 60–69 anos ─
    ("60-69", "baixa"):  {"A1-A5": (37.2, 9.5), "A6": (7.1, 3.8), "A7": (6.6, 3.9), "B1": (4.9, 2.5), "rec_hits": (11.5, 2.7)},
    ("60-69", "media"):  {"A1-A5": (41.8, 9.1), "A6": (8.3, 3.4), "A7": (7.8, 3.5), "B1": (5.4, 2.3), "rec_hits": (12.5, 2.3)},
    ("60-69", "alta"):   {"A1-A5": (46.0, 8.6), "A6": (9.4, 3.0), "A7": (8.9, 3.1), "B1": (5.8, 2.1), "rec_hits": (13.2, 1.9)},
    # ─ 70+ anos ─
    ("70+", "baixa"):    {"A1-A5": (33.5, 10.2), "A6": (6.3, 4.1), "A7": (5.8, 4.2), "B1": (4.5, 2.7), "rec_hits": (10.5, 3.0)},
    ("70+", "media"):    {"A1-A5": (38.1, 9.8), "A6": (7.5, 3.7), "A7": (7.0, 3.8), "B1": (5.0, 2.5), "rec_hits": (11.6, 2.6)},
    ("70+", "alta"):     {"A1-A5": (42.5, 9.3), "A6": (8.6, 3.3), "A7": (8.1, 3.4), "B1": (5.5, 2.3), "rec_hits": (12.4, 2.2)},
}

# Normas pediátricas RAVLT (Oliveira et al., 2014; Miotto et al., 2012)
RAVLT_NORMAS_INFANTIL = {
    # (faixa_etaria, escolaridade): {variavel: (media, dp)}
    ("6-7",  "fundamental"): {"A1-A5": (31.5, 7.2), "A6": (5.8, 2.4), "A7": (5.2, 2.6), "B1": (3.9, 1.8), "rec_hits": (11.2, 2.8)},
    ("8-9",  "fundamental"): {"A1-A5": (37.8, 7.5), "A6": (7.1, 2.6), "A7": (6.6, 2.8), "B1": (4.5, 1.9), "rec_hits": (12.3, 2.4)},
    ("10-11","fundamental"): {"A1-A5": (43.2, 7.8), "A6": (8.5, 2.7), "A7": (8.0, 2.9), "B1": (5.1, 2.0), "rec_hits": (13.1, 2.1)},
    ("12-13","fundamental"): {"A1-A5": (47.5, 7.6), "A6": (9.4, 2.5), "A7": (8.9, 2.7), "B1": (5.6, 1.9), "rec_hits": (13.6, 1.8)},
    ("14-17","medio"):       {"A1-A5": (51.0, 7.3), "A6": (10.3, 2.4), "A7": (9.8, 2.5), "B1": (6.0, 1.8), "rec_hits": (14.0, 1.5)},
}


# ──────────────────────────────────────────────────────────────────────────────
# FDT — Five Digit Test
# Fonte: Paula et al. (2012). Psicologia: Reflexão e Crítica, 25(3), 563-571.
# Escores: tempo em segundos, erros
# ──────────────────────────────────────────────────────────────────────────────

FDT_NORMAS = {
    # (faixa_etaria, escolaridade): {condicao: (media_tempo, dp_tempo, media_erros, dp_erros)}
    ("18-39", "baixa"):  {
        "contar":   (25.1, 5.8, 0.3, 0.7),
        "ler":      (18.4, 4.2, 0.2, 0.5),
        "escolher": (52.3, 14.1, 1.8, 2.4),
        "alternar": (68.5, 19.3, 2.1, 2.8),
    },
    ("18-39", "media"):  {
        "contar":   (22.3, 5.1, 0.2, 0.5),
        "ler":      (16.1, 3.8, 0.1, 0.4),
        "escolher": (44.7, 12.3, 1.2, 1.9),
        "alternar": (58.2, 16.7, 1.6, 2.3),
    },
    ("18-39", "alta"):   {
        "contar":   (20.1, 4.6, 0.1, 0.4),
        "ler":      (14.8, 3.4, 0.1, 0.3),
        "escolher": (39.5, 10.8, 0.9, 1.5),
        "alternar": (51.3, 14.9, 1.2, 1.9),
    },
    ("40-59", "baixa"):  {
        "contar":   (28.9, 6.8, 0.4, 0.9),
        "ler":      (21.3, 5.0, 0.3, 0.6),
        "escolher": (63.1, 17.5, 2.3, 3.1),
        "alternar": (82.4, 23.8, 2.7, 3.5),
    },
    ("40-59", "media"):  {
        "contar":   (25.4, 6.1, 0.3, 0.7),
        "ler":      (18.7, 4.5, 0.2, 0.5),
        "escolher": (54.6, 15.2, 1.7, 2.5),
        "alternar": (71.3, 20.6, 2.1, 2.9),
    },
    ("40-59", "alta"):   {
        "contar":   (22.8, 5.5, 0.2, 0.5),
        "ler":      (16.9, 4.0, 0.1, 0.4),
        "escolher": (47.2, 13.4, 1.3, 2.0),
        "alternar": (62.1, 18.2, 1.7, 2.4),
    },
    ("60+", "baixa"):    {
        "contar":   (34.2, 8.5, 0.6, 1.2),
        "ler":      (25.8, 6.2, 0.4, 0.8),
        "escolher": (78.5, 22.3, 3.1, 4.0),
        "alternar": (102.3, 29.7, 3.8, 4.6),
    },
    ("60+", "media"):    {
        "contar":   (29.8, 7.4, 0.5, 1.0),
        "ler":      (22.3, 5.6, 0.3, 0.7),
        "escolher": (67.4, 19.1, 2.5, 3.3),
        "alternar": (88.5, 25.8, 3.1, 4.0),
    },
    ("60+", "alta"):     {
        "contar":   (26.5, 6.7, 0.3, 0.8),
        "ler":      (19.6, 5.1, 0.2, 0.5),
        "escolher": (58.3, 16.8, 2.0, 2.8),
        "alternar": (76.1, 22.4, 2.5, 3.3),
    },
}

# Normas FDT infantil — Sedó et al. adaptado para BR
FDT_NORMAS_INFANTIL = {
    ("6-7",  "fundamental"): {
        "contar":   (38.5, 10.2, 1.1, 1.6), "ler": (30.2, 8.5, 0.8, 1.3),
        "escolher": (95.3, 28.4, 4.2, 4.8), "alternar": (120.5, 34.2, 5.1, 5.7),
    },
    ("8-9",  "fundamental"): {
        "contar":   (30.1, 8.3, 0.6, 1.1), "ler": (23.4, 6.7, 0.5, 0.9),
        "escolher": (73.2, 22.1, 2.8, 3.5), "alternar": (95.4, 27.3, 3.4, 4.1),
    },
    ("10-11","fundamental"): {
        "contar":   (24.8, 6.5, 0.4, 0.8), "ler": (19.2, 5.3, 0.3, 0.7),
        "escolher": (58.5, 17.4, 1.9, 2.7), "alternar": (76.2, 21.5, 2.3, 3.0),
    },
    ("12-14","fundamental"): {
        "contar":   (21.3, 5.6, 0.2, 0.6), "ler": (16.5, 4.5, 0.2, 0.5),
        "escolher": (48.3, 14.2, 1.4, 2.1), "alternar": (63.5, 18.3, 1.8, 2.5),
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# TMT — Trail Making Test
# Fonte: Campanholo et al. (2014). Dement Neuropsychol, 8(1), 26-34.
# ──────────────────────────────────────────────────────────────────────────────

TMT_NORMAS = {
    # (faixa_etaria, escolaridade): {"A": (media, dp), "B": (media, dp)}
    ("18-39", "baixa"):  {"A": (44.5, 16.2), "B": (118.3, 47.8)},
    ("18-39", "media"):  {"A": (36.2, 12.8), "B": (94.7, 38.5)},
    ("18-39", "alta"):   {"A": (30.1, 10.3), "B": (78.4, 31.2)},
    ("40-59", "baixa"):  {"A": (56.8, 19.5), "B": (152.4, 58.3)},
    ("40-59", "media"):  {"A": (46.3, 16.1), "B": (124.6, 48.2)},
    ("40-59", "alta"):   {"A": (38.7, 13.5), "B": (103.2, 40.1)},
    ("60+",   "baixa"):  {"A": (73.2, 25.8), "B": (198.5, 74.2)},
    ("60+",   "media"):  {"A": (59.4, 21.3), "B": (162.1, 62.5)},
    ("60+",   "alta"):   {"A": (49.8, 18.1), "B": (135.3, 53.4)},
}


# ──────────────────────────────────────────────────────────────────────────────
# BDI-II — Beck Depression Inventory-II
# Fonte: Gorenstein & Andrade (1996); Cunha (2001) — validação brasileira
# Interpretação por faixa de escore total (0–63)
# ──────────────────────────────────────────────────────────────────────────────

BDI2_CLASSIFICACAO = [
    (0,  13,  "Mínimo",   "Sintomatologia depressiva mínima ou ausente."),
    (14, 19,  "Leve",     "Sintomas depressivos leves presentes. Monitoramento recomendado."),
    (20, 28,  "Moderado", "Sintomas depressivos moderados. Avaliação clínica indicada."),
    (29, 63,  "Grave",    "Sintomas depressivos graves. Intervenção clínica urgente recomendada."),
]

BDI2_ITENS = [
    "Tristeza", "Pessimismo", "Fracasso passado", "Perda de prazer",
    "Sentimentos de culpa", "Sentimentos de punição", "Autodesapreço",
    "Autocrítica", "Pensamentos ou desejos suicidas", "Choro",
    "Agitação", "Perda de interesse", "Indecisão", "Desvalia",
    "Perda de energia", "Mudanças no padrão de sono", "Irritabilidade",
    "Mudanças no apetite", "Dificuldade de concentração", "Cansaço ou fadiga",
    "Perda de interesse em sexo",
]


# ──────────────────────────────────────────────────────────────────────────────
# BAI — Beck Anxiety Inventory
# Fonte: Cunha (2001). Manual BAI. São Paulo: Casa do Psicólogo.
# ──────────────────────────────────────────────────────────────────────────────

BAI_CLASSIFICACAO = [
    (0,  10, "Mínimo",   "Nível mínimo de ansiedade."),
    (11, 19, "Leve",     "Ansiedade leve. Pode não requerer intervenção imediata."),
    (20, 30, "Moderado", "Ansiedade moderada. Avaliação clínica recomendada."),
    (31, 63, "Grave",    "Ansiedade grave. Intervenção clínica indicada."),
]

BAI_ITENS = [
    "Dormência ou formigamento", "Sensação de calor", "Tremor nas pernas",
    "Incapaz de relaxar", "Medo que aconteça o pior", "Atordoado ou tonto",
    "Palpitação ou aceleração do coração", "Sem equilíbrio", "Aterrorizado",
    "Nervoso", "Sensação de sufocamento", "Mãos tremendo", "Trêmulo",
    "Medo de perder o controle", "Dificuldade de respirar", "Medo de morrer",
    "Assustado", "Indigestão ou desconforto no abdômen", "Desmaio",
    "Rosto afogueado", "Suor (não devido ao calor)",
]


# ──────────────────────────────────────────────────────────────────────────────
# SRS-2 — Social Responsiveness Scale, 2ª edição
# Fonte: Constantino & Gruber (2012) — normas americanas (sem normas BR publicadas)
# T-scores por subscala e total
# ──────────────────────────────────────────────────────────────────────────────

SRS2_SUBSCALAS = {
    "Percepção Social (PS)":    {"itens": 8,  "peso": 1.0},
    "Cognição Social (CS)":     {"itens": 12, "peso": 1.0},
    "Comunicação Social (CO)":  {"itens": 22, "peso": 1.0},
    "Motivação Social (MO)":    {"itens": 11, "peso": 1.0},
    "Maneirismos (MA)":         {"itens": 12, "peso": 1.0},
}

SRS2_CLASSIFICACAO_TOTAL = [
    (0,  59, "Dentro da normalidade", "Responsividade social dentro do esperado para a faixa etária."),
    (60, 65, "Leve",                  "Dificuldades sociais leves, compatíveis com TEA leve ou características subclínicas."),
    (66, 75, "Moderado",              "Dificuldades sociais moderadas, interferindo no funcionamento. Investigação aprofundada indicada."),
    (76, 200,"Grave",                 "Dificuldades sociais graves, altamente associadas ao TEA. Avaliação multidisciplinar essencial."),
]

# Nota clínica importante para SRS-2
SRS2_NOTA_CLINICA = (
    "IMPORTANTE: O SRS-2 utiliza normas americanas. Pontuação abaixo do ponto de corte "
    "NÃO exclui TEA, especialmente em meninas com fenótipo feminino e camuflagem social. "
    "Interpretar sempre em conjunto com anamnese desenvolvimental e observação clínica."
)


# ──────────────────────────────────────────────────────────────────────────────
# ETDAH — Escala de Avaliação de TDAH baseada no DSM-5
# Critérios DSM-5-TR; escala de 18 itens (9 desatenção + 9 HI)
# Frequência: 0=Nunca, 1=Raramente, 2=Às vezes, 3=Frequentemente, 4=Sempre
# ──────────────────────────────────────────────────────────────────────────────

ETDAH_ITENS_DESATENCAO = [
    "Não presta atenção a detalhes ou comete erros por descuido",
    "Tem dificuldade para manter a atenção em tarefas ou atividades lúdicas",
    "Parece não ouvir quando se fala diretamente com ele(a)",
    "Não segue instruções até o fim e não termina tarefas",
    "Tem dificuldade para organizar tarefas e atividades",
    "Evita ou reluta em envolver-se em tarefas que requerem esforço mental prolongado",
    "Perde objetos necessários para tarefas ou atividades",
    "É facilmente distraído por estímulos externos",
    "É esquecido em atividades cotidianas",
]

ETDAH_ITENS_HI = [
    "Mexe mãos/pés ou se remexe na cadeira",
    "Levanta-se da cadeira em situações em que se espera que permaneça sentado",
    "Corre ou sobe nas coisas em situações inapropriadas (adultos: sensação de inquietação)",
    "Tem dificuldade para brincar ou participar de lazer de forma quieta",
    "Está frequentemente 'a mil' ou age como se fosse 'movido a motor'",
    "Fala em excesso",
    "Responde antes de a pergunta ter sido completada",
    "Tem dificuldade para esperar a vez",
    "Interrompe ou se intromete nas conversas ou jogos de outros",
]

ETDAH_CRITERIO_DSM5 = {
    "crianca_adolescente": {"limiar_sintomas": 6, "idade_max": 17},
    "adulto":              {"limiar_sintomas": 5, "idade_min": 18},
}


# ──────────────────────────────────────────────────────────────────────────────
# Funções utilitárias de conversão normativa
# ──────────────────────────────────────────────────────────────────────────────

def calcular_z_percentil(escore, media, dp):
    """Calcula z-score e percentil correspondente."""
    if dp == 0:
        return 0.0, 50.0
    z = (escore - media) / dp
    percentil = float(stats.norm.cdf(z) * 100)
    return round(z, 2), round(percentil, 1)


def classificar_por_percentil(percentil):
    """Retorna classificação clínica baseada no percentil."""
    if percentil < 2:
        return "Muito Rebaixado", "danger"
    elif percentil < 9:
        return "Rebaixado", "danger"
    elif percentil < 25:
        return "Abaixo da Média", "warning"
    elif percentil < 75:
        return "Médio", "success"
    elif percentil < 91:
        return "Acima da Média", "success"
    elif percentil < 98:
        return "Superior", "success"
    else:
        return "Muito Superior", "success"


def faixa_etaria_adulto(idade):
    """Retorna a chave de faixa etária para adultos."""
    if idade < 30:
        return "18-29"
    elif idade < 40:
        return "30-39"
    elif idade < 50:
        return "40-49"
    elif idade < 60:
        return "50-59"
    elif idade < 70:
        return "60-69"
    else:
        return "70+"


def faixa_etaria_fdt(idade):
    if idade < 40:
        return "18-39"
    elif idade < 60:
        return "40-59"
    else:
        return "60+"


def faixa_etaria_tmt(idade):
    if idade < 40:
        return "18-39"
    elif idade < 60:
        return "40-59"
    else:
        return "60+"


def faixa_etaria_infantil_ravlt(idade):
    if idade <= 7:
        return "6-7"
    elif idade <= 9:
        return "8-9"
    elif idade <= 11:
        return "10-11"
    elif idade <= 13:
        return "12-13"
    else:
        return "14-17"


def faixa_etaria_infantil_fdt(idade):
    if idade <= 7:
        return "6-7"
    elif idade <= 9:
        return "8-9"
    elif idade <= 11:
        return "10-11"
    else:
        return "12-14"


def escolaridade_grupo(anos_escolaridade):
    """Converte anos de escolaridade em grupo normativo."""
    if anos_escolaridade <= 8:
        return "baixa"
    elif anos_escolaridade <= 11:
        return "media"
    else:
        return "alta"


def escolaridade_infantil(serie_ou_nivel):
    """Para crianças: retorna grupo baseado no nível escolar."""
    nivel = str(serie_ou_nivel).lower()
    if "médio" in nivel or "medio" in nivel:
        return "medio"
    return "fundamental"
