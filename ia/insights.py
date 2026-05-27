"""
Módulo de insights clínicos com suporte a três provedores de IA:
  - offline  : análise por regras, sem custo, sem internet
  - claude   : Claude Sonnet (Anthropic)
  - gemini   : Gemini 2.5 Flash (Google)
  - openai   : GPT-4o (OpenAI)
"""

import os
import json
from typing import Optional


def gerar_insights(
    resultados: list,
    paciente: dict,
    provedor: str = "offline",
    api_key: Optional[str] = None,
) -> str:
    """
    provedor: "offline" | "claude" | "gemini" | "openai"
    api_key: chave do provedor escolhido (ou variável de ambiente correspondente)
    """
    if provedor == "offline" or not api_key:
        texto = _insights_offline(resultados, paciente)
        if provedor != "offline" and not api_key:
            texto += "\n\n⚠️ Modo offline: chave API não configurada para o provedor selecionado."
        return texto

    prompt = _montar_prompt(resultados, paciente)

    if provedor == "claude":
        return _com_claude(prompt, api_key)
    elif provedor == "gemini":
        return _com_gemini(prompt, api_key)
    elif provedor == "openai":
        return _com_openai(prompt, api_key)
    else:
        return _insights_offline(resultados, paciente)


# ──────────────────────────────────────────────────────────────────────────────
# Provedores
# ──────────────────────────────────────────────────────────────────────────────

def _com_claude(prompt, api_key):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return f"=== ANÁLISE INTEGRADA (Claude Sonnet) ===\n\n{resp.content[0].text}"
    except ImportError:
        return _insights_offline(None, None) + "\n\n⚠️ Pacote 'anthropic' não instalado. Execute: pip install anthropic"
    except Exception as e:
        return _insights_offline(None, None) + f"\n\n⚠️ Erro Claude API: {e}"


def _com_gemini(prompt, api_key):
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return f"=== ANÁLISE INTEGRADA (Gemini 2.5 Flash) ===\n\n{resp.text}"
    except ImportError:
        return _insights_offline(None, None) + "\n\n⚠️ Pacote 'google-genai' não instalado. Execute: pip install google-genai"
    except Exception as e:
        return _insights_offline(None, None) + f"\n\n⚠️ Erro Gemini API: {e}"


def _com_openai(prompt, api_key):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return f"=== ANÁLISE INTEGRADA (GPT-4o) ===\n\n{resp.choices[0].message.content}"
    except ImportError:
        return _insights_offline(None, None) + "\n\n⚠️ Pacote 'openai' não instalado. Execute: pip install openai"
    except Exception as e:
        return _insights_offline(None, None) + f"\n\n⚠️ Erro OpenAI API: {e}"


# ──────────────────────────────────────────────────────────────────────────────
# Prompt compartilhado
# ──────────────────────────────────────────────────────────────────────────────

def _montar_prompt(resultados, paciente):
    resumo = []
    for r in resultados:
        resumo.append({
            "teste": r["teste_codigo"],
            "interpretacao": r.get("interpretacao", ""),
            "escores_resumo": _resumir_escores(r.get("escores_calculados", {})),
        })

    return f"""Você é um assistente clínico especializado em neuropsicologia, atuando como parceiro de raciocínio de uma neuropsicóloga experiente.

PACIENTE:
- Nome: {paciente.get('nome', 'N/D')}
- Idade: {paciente.get('idade', 'N/D')} anos
- Sexo: {paciente.get('sexo', 'N/D')}
- Escolaridade: {paciente.get('escolaridade', 'N/D')}
- Queixa principal: {paciente.get('queixa_principal', 'N/D')}

RESULTADOS DOS TESTES:
{json.dumps(resumo, ensure_ascii=False, indent=2)}

Com base nesses dados, forneça:

## Perfil Cognitivo por Domínio
Para cada domínio avaliado: desempenho (preservado / limítrofe / rebaixado / muito rebaixado) + dados que embasam.

## Padrões e Dissociações
O que os dados têm em comum? Onde há contradições? Consistência interna do perfil?

## Hipóteses Diagnósticas (DSM-5)
Liste em ordem de probabilidade, com justificativa. Use linguagem de hipótese ("os dados sugerem", "compatível com", "não se pode descartar").

## Domínios que Merecem Investigação Adicional

## Considerações para o Laudo

IMPORTANTE: Nunca seja categórico sobre diagnóstico. Este texto apoia a neuropsicóloga — ela decide. Escreva em português brasileiro."""


# ──────────────────────────────────────────────────────────────────────────────
# Análise offline por regras
# ──────────────────────────────────────────────────────────────────────────────

def _insights_offline(resultados, paciente):
    if not resultados:
        return "=== ANÁLISE INTEGRADA (Modo Offline) ===\n\nNenhum dado disponível."

    linhas = ["=== ANÁLISE INTEGRADA (Modo Offline) ===\n"]
    dados = {r["teste_codigo"]: r.get("escores_calculados", {}) for r in resultados}

    alertas, padroes, hipoteses, pontos_at = [], [], [], []

    # Memória (RAVLT)
    if "RAVLT" in dados:
        r = dados["RAVLT"]
        pct_tot = r.get("percentil_total", 50)
        pct_a7  = r.get("percentil_a7", 50)
        if pct_tot < 9:
            alertas.append("Memória episódica verbal gravemente comprometida (RAVLT < P9).")
            hipoteses.append("Disfunção hipocampal/temporal mesial — investigar causas neurológicas.")
        elif pct_tot < 25:
            padroes.append("Memória episódica verbal rebaixada.")
        else:
            pontos_at.append("Memória episódica verbal preservada.")
        if pct_a7 < pct_tot - 15:
            padroes.append("Queda desproporcional na evocação tardia — possível esquecimento acelerado.")

    # Funções Executivas (FDT / TMT)
    fe_comprometida = False
    if "FDT" in dados:
        conds = dados["FDT"].get("condicoes", {})
        if conds.get("alternar", {}).get("percentil_tempo", 50) < 25:
            padroes.append("Flexibilidade cognitiva reduzida (FDT-Alternar).")
            fe_comprometida = True
        if conds.get("escolher", {}).get("percentil_tempo", 50) < 25:
            padroes.append("Controle inibitório reduzido (FDT-Escolher).")
            fe_comprometida = True
        if conds.get("contar", {}).get("percentil_tempo", 50) < 25:
            padroes.append("Velocidade de processamento basal lentificada (FDT-Contar).")

    if "TMT" in dados:
        t = dados["TMT"]
        razao = t.get("razao_B_A")
        if t.get("percentil_b", 50) < 25:
            padroes.append("TMT-B comprometido — alternância atencional reduzida.")
            fe_comprometida = True
        if razao and razao > 3.5:
            padroes.append(f"Razão B/A = {razao:.2f}: comprometimento executivo desproporcional à velocidade basal.")

    if fe_comprometida:
        hipoteses.append("Disfunção frontal-executiva identificada em ≥1 instrumento.")

    # Aspectos Emocionais
    humor_alt, ansiedade_alt = False, False
    if "BDI2" in dados:
        b = dados["BDI2"]
        classif = b.get("classificacao", "")
        if classif in ("Moderado", "Grave"):
            alertas.append(f"Sintomatologia depressiva {classif.lower()} (BDI-II = {b.get('total','--')}).")
            humor_alt = True
        elif classif == "Leve":
            padroes.append(f"Sintomatologia depressiva leve (BDI-II = {b.get('total','--')}).")
            humor_alt = True
        if b.get("alerta_ideacao_suicida"):
            alertas.append("🔴 ALERTA: Ideação suicida presente no BDI-II. Avaliar risco imediatamente.")

    if "BAI" in dados:
        a = dados["BAI"]
        classif = a.get("classificacao", "")
        if classif in ("Moderado", "Grave"):
            alertas.append(f"Sintomatologia ansiosa {classif.lower()} (BAI = {a.get('total','--')}).")
            ansiedade_alt = True
        elif classif == "Leve":
            padroes.append(f"Sintomatologia ansiosa leve (BAI = {a.get('total','--')}).")
            ansiedade_alt = True

    if (humor_alt or ansiedade_alt) and ("RAVLT" in dados or "FDT" in dados):
        padroes.append(
            "Alterações emocionais presentes podem impactar cognição — "
            "considerar diagnóstico diferencial entre déficit primário vs. secundário ao humor/ansiedade."
        )

    # TEA / Social (SRS-2)
    if "SRS2" in dados:
        s = dados["SRS2"]
        total_t = s.get("total_tscore", 50)
        classif = s.get("classificacao", "")
        if total_t >= 66:
            padroes.append(f"SRS-2: dificuldades sociais {classif.lower()} (T={total_t:.0f}).")
            hipoteses.append("Compatível com TEA ou características do espectro — investigação aprofundada indicada.")
        elif total_t >= 60:
            padroes.append(f"SRS-2: dificuldades sociais leves (T={total_t:.0f}) — monitorar.")
        if s.get("sexo") == "F":
            alertas.append(
                "SRS-2 em paciente feminina: avaliar possibilidade de camuflagem social "
                "(fenótipo feminino do autismo). Pontuação normal não exclui TEA."
            )

    # TDAH (ETDAH)
    if "ETDAH" in dados:
        e = dados["ETDAH"]
        if e.get("criterios_quantitativos_met"):
            apresent = e.get("apresentacao_sugerida", "")
            padroes.append(f"Critérios DSM-5 para TDAH atingidos: {apresent}.")
            hipoteses.append(
                f"TDAH — {apresent} — confirmar Critérios B, C e D na entrevista."
            )
            if "SRS2" in dados and dados["SRS2"].get("total_tscore", 0) >= 60:
                alertas.append("TDAH + indicadores sociais alterados: investigar comorbidade TDAH+TEA.")

    # Montagem
    if alertas:
        linhas.append("ALERTAS CLÍNICOS:")
        for a in alertas:
            linhas.append(f"  • {a}")
        linhas.append("")

    if padroes:
        linhas.append("PADRÕES IDENTIFICADOS:")
        for p in padroes:
            linhas.append(f"  • {p}")
        linhas.append("")

    if hipoteses:
        linhas.append("HIPÓTESES DIAGNÓSTICAS SUGERIDAS (dados sugerem — não substituem julgamento clínico):")
        for h in hipoteses:
            linhas.append(f"  • {h}")
        linhas.append("")

    if pontos_at:
        linhas.append("FUNÇÕES PRESERVADAS:")
        for p in pontos_at:
            linhas.append(f"  • {p}")
        linhas.append("")

    testes_aplicados = [r["teste_codigo"] for r in resultados]
    nao_cobertos = _dominios_nao_cobertos(testes_aplicados)
    if nao_cobertos:
        linhas.append("DOMÍNIOS NÃO AVALIADOS NESTA SESSÃO:")
        for d in nao_cobertos:
            linhas.append(f"  • {d}")
        linhas.append("")

    linhas.append(
        "Esta análise automática é um auxiliar clínico. "
        "O diagnóstico neuropsicológico requer integração com anamnese, "
        "observação clínica e julgamento profissional."
    )
    return "\n".join(linhas)


def _dominios_nao_cobertos(codigos):
    mapa = {
        "Memória episódica verbal": ["RAVLT"],
        "Funções executivas / Velocidade": ["FDT", "TMT"],
        "Sintomatologia depressiva": ["BDI2"],
        "Sintomatologia ansiosa": ["BAI"],
        "Cognição social / TEA": ["SRS2"],
        "TDAH": ["ETDAH"],
        "Inteligência geral / QI": ["WAIS", "WISC"],
        "Atenção (BPA)": ["BPA"],
    }
    return [d for d, testes in mapa.items() if not any(t in codigos for t in testes)]


def _resumir_escores(escores):
    if not isinstance(escores, dict):
        return escores
    campos = [
        "classificacao", "classif_total", "total", "percentil_total",
        "percentil_a7", "retencao_percentual", "apresentacao_sugerida",
        "total_tscore", "sintomas_desatencao", "sintomas_hi",
        "criterios_quantitativos_met", "inibicao", "flexibilidade",
        "razao_B_A", "percentil_b", "alerta_ideacao_suicida",
    ]
    resumo = {c: escores[c] for c in campos if c in escores}
    if "condicoes" in escores:
        resumo["condicoes"] = {
            k: {"percentil_tempo": v.get("percentil_tempo"), "classificacao": v.get("classificacao")}
            for k, v in escores["condicoes"].items()
        }
    return resumo
