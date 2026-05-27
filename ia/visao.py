"""
Módulo de visão computacional — lê fotos de testes físicos.
Suporta: Claude (Anthropic), Gemini (Google), GPT-4o (OpenAI).
"""

import os
import base64
import json
import re
from typing import Optional


def ler_foto_teste(
    imagem_bytes: bytes,
    tipo_teste: str,
    provedor: str = "claude",
    api_key: Optional[str] = None,
) -> dict:
    """
    imagem_bytes : bytes da imagem (JPG/PNG)
    tipo_teste   : "RAVLT", "BDI2", "BAI", "ETDAH", "SRS2", "FDT", "TMT"
    provedor     : "claude" | "gemini" | "openai"
    api_key      : chave do provedor
    """
    key = api_key or os.getenv(_env_var(provedor), "")
    if not key:
        return {"erro": f"Chave API de {provedor.upper()} não configurada."}

    prompt = _prompt_por_teste(tipo_teste)
    if not prompt:
        return {"erro": f"Tipo de teste '{tipo_teste}' não suportado para leitura por foto."}

    if provedor == "claude":
        return _visao_claude(imagem_bytes, prompt, key)
    elif provedor == "gemini":
        return _visao_gemini(imagem_bytes, prompt, key)
    elif provedor == "openai":
        return _visao_openai(imagem_bytes, prompt, key)
    else:
        return {"erro": f"Provedor '{provedor}' não reconhecido."}


# ──────────────────────────────────────────────────────────────────────────────
# Implementações por provedor
# ──────────────────────────────────────────────────────────────────────────────

def _visao_claude(imagem_bytes, prompt, api_key):
    try:
        import anthropic
        img_b64    = base64.standard_b64encode(imagem_bytes).decode("utf-8")
        media_type = "image/png" if imagem_bytes[:8] == b'\x89PNG\r\n\x1a\n' else "image/jpeg"

        client = anthropic.Anthropic(api_key=api_key)
        resp   = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_b64}},
                    {"type": "text",  "text": prompt},
                ],
            }],
        )
        return _processar_resposta(resp.content[0].text, "claude")
    except ImportError:
        return {"erro": "Pacote 'anthropic' não instalado. Execute: pip install anthropic"}
    except Exception as e:
        return {"erro": f"Erro Claude Vision: {e}"}


def _visao_gemini(imagem_bytes, prompt, api_key):
    try:
        from google import genai
        from google.genai import types
        client    = genai.Client(api_key=api_key)
        media_type = "image/png" if imagem_bytes[:8] == b'\x89PNG\r\n\x1a\n' else "image/jpeg"
        part_img  = types.Part.from_bytes(data=imagem_bytes, mime_type=media_type)
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, part_img],
        )
        return _processar_resposta(resp.text, "gemini")
    except ImportError:
        return {"erro": "Pacote 'google-genai' não instalado. Execute: pip install google-genai"}
    except Exception as e:
        return {"erro": f"Erro Gemini Vision: {e}"}


def _visao_openai(imagem_bytes, prompt, api_key):
    try:
        from openai import OpenAI
        img_b64    = base64.standard_b64encode(imagem_bytes).decode("utf-8")
        media_type = "image/png" if imagem_bytes[:8] == b'\x89PNG\r\n\x1a\n' else "image/jpeg"

        client = OpenAI(api_key=api_key)
        resp   = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text",       "text": prompt},
                    {"type": "image_url",  "image_url": {"url": f"data:{media_type};base64,{img_b64}"}},
                ],
            }],
        )
        return _processar_resposta(resp.choices[0].message.content, "openai")
    except ImportError:
        return {"erro": "Pacote 'openai' não instalado. Execute: pip install openai"}
    except Exception as e:
        return {"erro": f"Erro OpenAI Vision: {e}"}


# ──────────────────────────────────────────────────────────────────────────────
# Utilitários
# ──────────────────────────────────────────────────────────────────────────────

def _processar_resposta(texto, provedor_nome):
    dados = _extrair_json(texto)
    if dados:
        dados["_fonte"]    = f"visao_{provedor_nome}"
        dados["_confianca_extracao"] = "verificar_manualmente"
        return dados
    return {
        "texto_bruto": texto,
        "_fonte": f"visao_{provedor_nome}",
        "_aviso": "Não foi possível estruturar automaticamente. Verifique o texto acima.",
    }


def _extrair_json(texto):
    matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', texto, re.DOTALL)
    for m in matches:
        try:
            return json.loads(m)
        except Exception:
            continue
    try:
        return json.loads(texto.strip())
    except Exception:
        return None


def _env_var(provedor):
    return {"claude": "ANTHROPIC_API_KEY", "gemini": "GOOGLE_API_KEY", "openai": "OPENAI_API_KEY"}.get(provedor, "")


def _prompt_por_teste(tipo_teste):
    prompts = {
        "RAVLT": """Esta é uma folha de registro do RAVLT.
Extraia os dados e retorne APENAS um JSON:
{"A1":<int>,"A2":<int>,"A3":<int>,"A4":<int>,"A5":<int>,"B1":<int>,"A6":<int>,"A7":<int>,"rec_hits":<int>,"rec_fa":<int>,"observacoes":"<string>"}
Use null se ilegível. Retorne APENAS o JSON.""",

        "BDI2": """Esta é uma folha de resposta do BDI-II (21 itens, opções 0-3).
Retorne APENAS: {"respostas":[<21 valores 0-3>]}
Use null se ilegível.""",

        "BAI": """Esta é uma folha de resposta do BAI (21 itens, opções 0-3).
Retorne APENAS: {"respostas":[<21 valores 0-3>]}
Use null se ilegível.""",

        "ETDAH": """Escala de TDAH DSM-5. Primeiros 9 itens = Desatenção, próximos 9 = HI.
Frequência: 0=Nunca, 1=Raramente, 2=Às vezes, 3=Frequentemente, 4=Sempre.
Retorne APENAS: {"desatencao":[<9 valores>],"hiperatividade":[<9 valores>]}
Use null se ilegível.""",

        "SRS2": """Folha de resposta SRS-2 (65 itens, escala 1-4).
Retorne APENAS: {"respostas":{"1":<val>,"2":<val>,...,"65":<val>}}
Use null se ilegível.""",

        "FDT": """Folha de registro FDT (tempos em segundos e erros por condição).
Retorne APENAS: {"contar_tempo":<float>,"contar_erros":<int>,"ler_tempo":<float>,"ler_erros":<int>,"escolher_tempo":<float>,"escolher_erros":<int>,"alternar_tempo":<float>,"alternar_erros":<int>}
Use null se ilegível.""",

        "TMT": """Folha de registro TMT (Partes A e B).
Retorne APENAS: {"tempo_a":<float>,"erros_a":<int>,"tempo_b":<float>,"erros_b":<int>}
Use null se ilegível.""",
    }
    return prompts.get(tipo_teste)
