import streamlit as st
import os
import pandas as pd
from sqlalchemy import create_engine, text
from pdf_generator import gerar_pdf_cliente, gerar_pdf_interno

# Configuração da página
st.set_page_config(
    page_title="Catálogo & Orçamentos",
    page_icon="📦",
    layout="wide"
)

# -------------------------------------------------------------------
# CONEXÃO COM O BANCO DE DADOS EM NUVEM (SUPABASE / POSTGRESQL)
# -------------------------------------------------------------------
@st.cache_resource
def get_db_engine():
    db_url = st.secrets["postgres"]["url"]
    return create_engine(db_url, pool_pre_ping=True)

engine = get_db_engine()

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
# BANCO DE DADOS - INICIALIZAÇÃO DAS TABELAS
# -------------------------------------------------------------------
UPLOADS_DIR = "uploads"
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

def init_db():
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS produtos (id SERIAL PRIMARY KEY, nome TEXT NOT NULL, descricao TEXT, preco_custo DOUBLE PRECISION NOT NULL, preco_venda DOUBLE PRECISION NOT NULL, imagem_path TEXT, permite_desconto INTEGER DEFAULT 1);"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS clientes (id SERIAL PRIMARY KEY, nome TEXT NOT NULL, documento TEXT, email TEXT, telefone TEXT, endereco TEXT, observacoes TEXT);"))

init_db()

# --- OPERAÇÕES PRODUTOS ---
def cadastrar_produto(nome, descricao, preco_custo, preco_venda, imagem_path, permite_desconto):
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO produtos (nome, descricao, preco_custo, preco_venda, imagem_path, permite_desconto) VALUES (:nome, :descricao, :preco_custo, :preco_venda, :imagem_path, :permite_desconto)"), {
            "nome": nome,
            "descricao": descricao,
            "preco_custo": preco_custo,
            "preco_venda": preco_venda,
            "imagem_path": imagem_path,
            "permite_desconto": 1 if permite_desconto else 0
        })

def atualizar_produto(prod_id, nome, descricao, preco_custo, preco_venda, imagem_path, permite_desconto):
    with engine.begin() as conn:
        conn.execute(text("UPDATE produtos SET nome = :nome, descricao = :descricao, preco_custo = :preco_custo, preco_venda = :preco_venda, imagem_path = :imagem_path, permite_desconto = :permite_desconto WHERE id = :id"), {
            "nome": nome,
            "descricao": descricao,
            "preco_custo": preco_custo,
            "preco_venda": preco_venda,
            "imagem_path": imagem_path,
            "permite_desconto": 1 if permite_desconto else 0,
            "id": prod_id
        })

def excluir_produto(prod_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM produtos WHERE id = :id"), {"id": prod_id})

def listar_produtos():
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM produtos ORDER BY id DESC"), conn)
    return df

# --- OPERAÇÕES CLIENTES ---
def cadastrar_cliente(nome, documento, email, telefone, endereco, observacoes):
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO clientes (nome, documento, email, telefone, endereco, observacoes) VALUES (:nome, :documento, :email, :telefone, :endereco, :observacoes)"), {
            "nome": nome,
            "documento": documento,
            "email": email,
            "telefone": telefone,
            "endereco": endereco,
            "observacoes": observacoes
        })

def atualizar_cliente(cliente_id, nome, documento, email, telefone, endereco, observacoes):
    with engine.begin() as conn:
        conn.execute(text("UPDATE clientes SET nome = :nome, documento = :documento, email = :email, telefone = :telefone, endereco = :endereco, observacoes = :observacoes WHERE id = :id"), {
            "nome": nome,
            "documento": documento,
            "email": email,
            "telefone": telefone,
            "endereco": endereco,
            "observacoes": observacoes,
            "id": cliente_id
        })

def excluir_cliente(cliente_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM clientes WHERE id = :id"), {"id": cliente_id})

def listar_clientes():
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT *
