import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Em produção (Docker) usa /data; localmente usa a pasta do projeto
_DATA_DIR = Path("/data") if Path("/data").exists() else Path(__file__).parent.parent
DB_PATH = _DATA_DIR / "dados_neuropsico.db"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_banco():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            data_nascimento TEXT,
            escolaridade TEXT,
            sexo TEXT,
            queixa_principal TEXT,
            observacoes TEXT,
            criado_em TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS avaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
            data_avaliacao TEXT DEFAULT (date('now')),
            testes_aplicados TEXT,
            observacoes_comportamentais TEXT,
            status TEXT DEFAULT 'em_andamento',
            criado_em TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS resultados_testes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            avaliacao_id INTEGER NOT NULL REFERENCES avaliacoes(id),
            teste_codigo TEXT NOT NULL,
            dados_brutos TEXT,
            escores_calculados TEXT,
            interpretacao TEXT,
            nivel_confianca TEXT,
            criado_em TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS insights_ia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            avaliacao_id INTEGER NOT NULL REFERENCES avaliacoes(id),
            tipo TEXT,
            conteudo TEXT,
            modelo_usado TEXT,
            criado_em TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


# ── Pacientes ──────────────────────────────────────────────────────────────

def criar_paciente(nome, data_nascimento, escolaridade, sexo, queixa, obs=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO pacientes (nome, data_nascimento, escolaridade, sexo, queixa_principal, observacoes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (nome, data_nascimento, escolaridade, sexo, queixa, obs),
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def listar_pacientes():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM pacientes ORDER BY criado_em DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_paciente(pid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM pacientes WHERE id = ?", (pid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def atualizar_paciente(pid, **campos):
    conn = get_connection()
    sets = ", ".join(f"{k} = ?" for k in campos)
    conn.execute(f"UPDATE pacientes SET {sets} WHERE id = ?", (*campos.values(), pid))
    conn.commit()
    conn.close()


# ── Avaliações ─────────────────────────────────────────────────────────────

def criar_avaliacao(paciente_id, testes_aplicados=None, obs_comportamentais=""):
    conn = get_connection()
    cur = conn.cursor()
    testes_json = json.dumps(testes_aplicados or [])
    cur.execute(
        """INSERT INTO avaliacoes (paciente_id, testes_aplicados, observacoes_comportamentais)
           VALUES (?, ?, ?)""",
        (paciente_id, testes_json, obs_comportamentais),
    )
    conn.commit()
    aid = cur.lastrowid
    conn.close()
    return aid


def buscar_avaliacoes_paciente(paciente_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM avaliacoes WHERE paciente_id = ? ORDER BY data_avaliacao DESC",
        (paciente_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_avaliacao(avaliacao_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM avaliacoes WHERE id = ?", (avaliacao_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def finalizar_avaliacao(avaliacao_id):
    conn = get_connection()
    conn.execute(
        "UPDATE avaliacoes SET status = 'concluida' WHERE id = ?", (avaliacao_id,)
    )
    conn.commit()
    conn.close()


# ── Resultados de testes ───────────────────────────────────────────────────

def salvar_resultado_teste(avaliacao_id, teste_codigo, dados_brutos, escores, interpretacao, confianca):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO resultados_testes
               (avaliacao_id, teste_codigo, dados_brutos, escores_calculados, interpretacao, nivel_confianca)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT DO NOTHING""",
        (
            avaliacao_id,
            teste_codigo,
            json.dumps(dados_brutos, ensure_ascii=False),
            json.dumps(escores, ensure_ascii=False),
            interpretacao,
            confianca,
        ),
    )
    # upsert manual
    existing = conn.execute(
        "SELECT id FROM resultados_testes WHERE avaliacao_id=? AND teste_codigo=?",
        (avaliacao_id, teste_codigo),
    ).fetchone()
    if existing:
        conn.execute(
            """UPDATE resultados_testes
               SET dados_brutos=?, escores_calculados=?, interpretacao=?, nivel_confianca=?, criado_em=datetime('now')
               WHERE avaliacao_id=? AND teste_codigo=?""",
            (
                json.dumps(dados_brutos, ensure_ascii=False),
                json.dumps(escores, ensure_ascii=False),
                interpretacao,
                confianca,
                avaliacao_id,
                teste_codigo,
            ),
        )
    conn.commit()
    conn.close()


def buscar_resultados_avaliacao(avaliacao_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM resultados_testes WHERE avaliacao_id = ?", (avaliacao_id,)
    ).fetchall()
    conn.close()
    resultados = []
    for r in rows:
        d = dict(r)
        d["dados_brutos"] = json.loads(d["dados_brutos"] or "{}")
        d["escores_calculados"] = json.loads(d["escores_calculados"] or "{}")
        resultados.append(d)
    return resultados


# ── Insights IA ────────────────────────────────────────────────────────────

def salvar_insight(avaliacao_id, tipo, conteudo, modelo="claude-sonnet-4-6"):
    conn = get_connection()
    conn.execute(
        "INSERT INTO insights_ia (avaliacao_id, tipo, conteudo, modelo_usado) VALUES (?,?,?,?)",
        (avaliacao_id, tipo, conteudo, modelo),
    )
    conn.commit()
    conn.close()


def buscar_insights(avaliacao_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM insights_ia WHERE avaliacao_id = ? ORDER BY criado_em DESC",
        (avaliacao_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
