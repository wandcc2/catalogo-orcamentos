import streamlit as st
import os
import sqlite3
import pandas as pd
import io
from pdf_generator import gerar_pdf_cliente, gerar_pdf_interno

# Configuração da página
st.set_page_config(
    page_title="Catálogo & Orçamentos",
    page_icon="📦",
    layout="wide"
)

# -------------------------------------------------------------------
# REGRA DE DESCONTO PROGRESSIVO
# -------------------------------------------------------------------
def calcular_desconto_progressivo(quantidade, preco_venda_original, permite_desconto):
    if not permite_desconto:
        return 0.0, preco_venda_original

    if quantidade >= 51:
        percentual_desconto = 0.25
    elif quantidade >= 41:
        percentual_desconto = 0.22
    elif quantidade >= 31:
        percentual_desconto = 0.20
    elif quantidade >= 21:
        percentual_desconto = 0.15
    elif quantidade >= 11:
        percentual_desconto = 0.10
    else:
        percentual_desconto = 0.0

    preco_com_desconto = preco_venda_original * (1 - percentual_desconto)
    return percentual_desconto, preco_com_desconto

# -------------------------------------------------------------------
# ESTILIZAÇÃO CSS DA BARRA LATERAL
# -------------------------------------------------------------------
st.markdown("""
    <style>
        div[data-testid="stSidebar"] button[kind="secondary"],
        div[data-testid="stSidebar"] button[kind="primary"] {
            width: 100% !important;
            border-radius: 8px !important;
            padding: 10px 16px !important;
            font-size: 15px !important;
            font-weight: 500 !important;
            text-align: left !important;
            justify-content: flex-start !important;
            margin-bottom: 6px !important;
            transition: all 0.3s ease !important;
        }

        div[data-testid="stSidebar"] button[kind="secondary"] {
            background-color: transparent !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #d0d7de !important;
        }

        div[data-testid="stSidebar"] button[kind="secondary"]:hover {
            background-color: rgba(255, 255, 255, 0.08) !important;
            border-color: rgba(255, 255, 255, 0.25) !important;
            color: #ffffff !important;
            transform: translateX(4px);
        }

        div[data-testid="stSidebar"] button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            color: #ffffff !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# BANCO DE DADOS
# -------------------------------------------------------------------
UPLOADS_DIR = "uploads"
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

def init_db():
    conn = sqlite3.connect("catalogo.db")
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            preco_custo REAL NOT NULL,
            preco_venda REAL NOT NULL,
            imagem_path TEXT,
            permite_desconto INTEGER DEFAULT 1
        )
    ''')
    try:
        c.execute('ALTER TABLE produtos ADD COLUMN permite_desconto INTEGER DEFAULT 1')
    except Exception:
        pass

    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            documento TEXT,
            email TEXT,
            telefone TEXT,
            endereco TEXT,
            observacoes TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# --- OPERAÇÕES PRODUTOS ---
def cadastrar_produto(nome, descricao, preco_custo, preco_venda, imagem_path, permite_desconto):
    conn = sqlite3.connect("catalogo.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO produtos (nome, descricao, preco_custo, preco_venda, imagem_path, permite_desconto)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nome, descricao, preco_custo, preco_venda, imagem_path, 1 if permite_desconto else 0))
    conn.commit()
    conn.close()

def atualizar_produto(prod_id, nome, descricao, preco_custo, preco_venda, imagem_path, permite_desconto):
    conn = sqlite3.connect("catalogo.db")
    c = conn.cursor()
    c.execute('''
        UPDATE produtos 
        SET nome = ?, descricao = ?, preco_custo = ?, preco_venda = ?, imagem_path = ?, permite_desconto = ?
        WHERE id = ?
    ''', (nome, descricao, preco_custo, preco_venda, imagem_path, 1 if permite_desconto else 0, prod_id))
    conn.commit()
    conn.close()

def excluir_produto(prod_id):
    conn = sqlite3.connect("catalogo.db")
    c = conn.cursor()
    c.execute('DELETE FROM produtos WHERE id = ?', (prod_id,))
    conn.commit()
    conn.close()

def listar_produtos():
    conn = sqlite3.connect("catalogo.db")
    df = pd.read_sql_query("SELECT * FROM produtos", conn)
    conn.close()
    return df

def importar_produtos_df(df):
    conn = sqlite3.connect("catalogo.db")
    c = conn.cursor()
    qtd_inseridos = 0

    for _, row in df.iterrows():
        nome = str(row.get("nome", "")).strip()
        if not nome or nome.lower() == "nan":
            continue

        descricao = str(row.get("descricao", "")) if pd.notna(row.get("descricao")) else ""
        
        try:
            preco_custo = float(row.get("preco_custo", 0.0))
        except ValueError:
            preco_custo = 0.0

        try:
            preco_venda = float(row.get("preco_venda", 0.0))
        except ValueError:
            preco_venda = 0.0

        permite_desc_raw = row.get("permite_desconto", 1)
        if str(permite_desc_raw).strip().lower() in ["0", "false", "nao", "não", "n"]:
            permite_desconto = 0
        else:
            permite_desconto = 1

        c.execute('''
            INSERT INTO produtos (nome, descricao, preco_custo, preco_venda, imagem_path, permite_desconto)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nome, descricao, preco_custo, preco_venda, "", permite_desconto))
        qtd_inseridos += 1

    conn.commit()
    conn.close()
    return qtd_inseridos

# --- OPERAÇÕES CLIENTES ---
def cadastrar_cliente(nome, documento, email, telefone, endereco, observacoes):
    conn = sqlite3.connect("catalogo.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO clientes (nome, documento, email, telefone, endereco, observacoes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nome, documento, email, telefone, endereco, observacoes))
    conn.commit()
    conn.close()

def atualizar_cliente(cliente_id, nome, documento, email, telefone, endereco, observacoes):
    conn = sqlite3.connect("catalogo.db")
    c = conn.cursor()
    c.execute('''
        UPDATE clientes 
        SET nome = ?, documento = ?, email = ?, telefone = ?, endereco = ?, observacoes = ?
        WHERE id
