import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from pdf_generator import gerar_pdf_cliente, gerar_pdf_interno

# Configuração da página
st.set_page_config(
    page_title="Catálogo & Orçamentos",
    page_icon="📦",
    layout="wide"
)

# -------------------------------------------------------------------
# CONEXÃO COM BANCO EM NUVEM (SUPABASE / POSTGRESQL)
# -------------------------------------------------------------------
@st.cache_resource
def get_db_engine():
    db_url = st.secrets["postgres"]["url"]
    return create_engine(db_url, pool_pre_ping=True)

engine = get_db_engine()

# -------------------------------------------------------------------
# DESCONTO PROGRESSIVO
# -------------------------------------------------------------------
def calcular_desconto_progressivo(quantidade, preco_original, permite):
    if not permite:
        return 0.0, preco_original

    if quantidade >= 51:
        pct = 0.25
    elif quantidade >= 41:
        pct = 0.22
    elif quantidade >= 31:
        pct = 0.20
    elif quantidade >= 21:
        pct = 0.15
    elif quantidade >= 11:
        pct = 0.10
    else:
        pct = 0.0

    preco_final = preco_original * (1 - pct)
    return pct, preco_final

# -------------------------------------------------------------------
# ESTILO DA BARRA LATERAL
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
            margin-bottom: 6px !important;
        }
        div[data-testid="stSidebar"] button[kind="primary"] {
            background: #2563eb !important;
            color: #ffffff !important;
            border: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# INICIALIZAÇÃO DO BANCO
# -------------------------------------------------------------------
UPLOADS_DIR = "uploads"
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

def init_db():
    sql_prod = (
        "CREATE TABLE IF NOT EXISTS produtos ("
        "id SERIAL PRIMARY KEY, "
        "nome TEXT NOT NULL, "
        "descricao TEXT, "
        "preco_custo DOUBLE PRECISION NOT NULL, "
        "preco_venda DOUBLE PRECISION NOT NULL, "
        "imagem_path TEXT, "
        "permite_desconto INTEGER DEFAULT 1);"
    )
    sql_cli = (
        "CREATE TABLE IF NOT EXISTS clientes ("
        "id SERIAL PRIMARY KEY, "
        "nome TEXT NOT NULL, "
        "documento TEXT, "
        "email TEXT, "
        "telefone TEXT, "
        "endereco TEXT, "
        "observacoes TEXT);"
    )
    with engine.begin() as conn:
        conn.execute(text(sql_prod))
        conn.execute(text(sql_cli))

init_db()

# --- OPERAÇÕES PRODUTOS ---
def cadastrar_produto(nome, desc, custo, venda, img, permite):
    sql = (
        "INSERT INTO produtos "
        "(nome, descricao, preco_custo, preco_venda, imagem_path, permite_desconto) "
        "VALUES (:nome, :desc, :custo, :venda, :img, :permite);"
    )
    params = {
        "nome": nome,
        "desc": desc,
        "custo": custo,
        "venda": venda,
        "img": img,
        "permite": 1 if permite else 0
    }
    with engine.begin() as conn:
        conn.execute(text(sql), params)

def atualizar_produto(p_id, nome, desc, custo, venda, img, permite):
    sql = (
        "UPDATE produtos SET "
        "nome = :nome, "
        "descricao = :desc, "
        "preco_custo = :custo, "
        "preco_venda = :venda, "
        "imagem_path = :img, "
        "permite_desconto = :permite "
        "WHERE id = :id;"
    )
    params = {
        "nome": nome,
        "desc": desc,
        "custo": custo,
        "venda": venda,
        "img": img,
        "permite": 1 if permite else 0,
        "id": p_id
    }
    with engine.begin() as conn:
        conn.execute(text(sql), params)

def excluir_produto(p_id):
    sql = "DELETE FROM produtos WHERE id = :id;"
    with engine.begin() as conn:
        conn.execute(text(sql), {"id": p_id})

def listar_produtos():
    sql = "SELECT * FROM produtos ORDER BY id DESC;"
    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn)
    return df

# --- OPERAÇÕES CLIENTES ---
def cadastrar_cliente(nome, doc, email, tel, end, obs):
    sql = (
        "INSERT INTO clientes "
        "(nome, documento, email, telefone, endereco, observacoes) "
        "VALUES (:nome, :doc, :email, :tel, :end, :obs);"
    )
    params = {
        "nome": nome,
        "doc": doc,
        "email": email,
        "tel": tel,
        "end": end,
        "obs": obs
    }
    with engine.begin() as conn:
        conn.execute(text(sql), params)

def atualizar_cliente(c_id, nome, doc, email, tel, end, obs):
    sql = (
        "UPDATE clientes SET "
        "nome = :nome, "
        "documento = :doc, "
        "email = :email, "
        "telefone = :tel, "
        "endereco = :end, "
        "observacoes = :obs "
        "WHERE id = :id;"
    )
    params = {
        "nome": nome,
        "doc": doc,
        "email": email,
        "tel": tel,
        "end": end,
        "obs": obs,
        "id": c_id
    }
    with engine.begin() as conn:
        conn.execute(text(sql), params)

def excluir_cliente(c_id):
    sql = "DELETE FROM clientes WHERE id = :id;"
    with engine.begin() as conn:
        conn.execute(text(sql), {"id": c_id})

def listar_clientes():
    sql = "SELECT * FROM clientes ORDER BY nome ASC;"
    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn)
    return df

# -------------------------------------------------------------------
# LOGIN
# -------------------------------------------------------------------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.subheader("Acesso Restrito")
        with st.form("form_login"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            btn = st.form_submit_button("Entrar")

            if btn:
                if usuario == "admin" and senha == "050391":
                    st.session_state.autenticado = True
                    st.session_state.pagina_atual = "Catalogo de Produtos"
                    st.rerun()
                else:
                    st.error("Dados incorretos.")
    st.stop()

# -------------------------------------------------------------------
# MENU PRINCIPAL
# -------------------------------------------------------------------
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Catalogo de Produtos"

opcoes_menu = [
    "Catalogo de Produtos",
    "Cadastrar Produto",
    "Editar / Excluir Produto",
    "Gestao de Clientes",
    "Criar Orcamento"
]

if st.session_state.pagina_atual not in opcoes_menu:
    st.session_state.pagina_atual = "Catalogo de Produtos"

with st.sidebar:
    st.markdown("### Navegação")

    for opcao in opcoes_menu:
        is_active = st.session_state.pagina_atual == opcao
        tipo_btn = "primary" if is_active else "secondary"
        if st.button(opcao, key=f"nav_{opcao}", type=tipo_btn, use_container_width=True):
            st.session_state.pagina_atual = opcao
            st.rerun()

    st.divider()
    if st.button("Sair", type="secondary", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

menu = st.session_state.pagina_atual

# -------------------------------------------------------------------
# 1. CATÁLOGO
# -------------------------------------------------------------------
if menu == "Catalogo de Produtos":
    st.header("Catálogo de Produtos")
    df_p = listar_produtos()

    if df_p.empty:
        st.info("Nenhum produto cadastrado.")
    else:
        busca = st.text_input("Buscar produto por nome...", "")
        if busca:
            df_p = df_p[df_p["nome"].str.contains(busca, case=False,
