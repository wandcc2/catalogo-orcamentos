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
# FUNÇÃO PARA CALCULAR DESCONTO PROGRESSIVO (FAIXAS ATUALIZADAS)
# -------------------------------------------------------------------
def calcular_desconto_progressivo(quantidade, preco_venda_original, permite_desconto):
    """
    Aplica a nova regra de desconto baseada na quantidade:
    - Até 10 un: 0%
    - 11 a 20 un: 10%
    - 21 a 30 un: 15%
    - 31 a 40 un: 20%
    - 41 a 50 un: 22%
    - 51 ou mais un: 25%
    """
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
# ESTILIZAÇÃO CSS PARA OS BOTÕES DA BARRA LATERAL
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
# AUTENTICAÇÃO
# -------------------------------------------------------------------
def verificar_login():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.subheader("🔒 Acesso Restrito - Faça Login")
            with st.form("form_login"):
                usuario = st.text_input("Usuário")
                senha = st.text_input("Senha", type="password")
                btn_login = st.form_submit_button("Entrar")

                if btn_login:
                    if usuario == "admin" and senha == "050391":
                        st.session_state.autenticado = True
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
        return False
    return True

if not verificar_login():
    st.stop()

# -------------------------------------------------------------------
# CONEXÃO COM O BANCO DE DADOS EM NUVEM (SUPABASE / POSTGRESQL)
# -------------------------------------------------------------------
@st.cache_resource
def get_db_engine():
    db_url = st.secrets["postgres"]["url"]
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return create_engine(db_url, pool_pre_ping=True)

engine = get_db_engine()

UPLOADS_DIR = "uploads"
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS produtos (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                descricao TEXT,
                preco_custo DOUBLE PRECISION NOT NULL,
                preco_venda DOUBLE PRECISION NOT NULL,
                imagem_path TEXT,
                permite_desconto INTEGER DEFAULT 1
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                documento TEXT,
                email TEXT,
                telefone TEXT,
                endereco TEXT,
                observacoes TEXT
            );
        """))

init_db()

# --- FUNÇÕES PRODUTOS ---
def cadastrar_produto(nome, descricao, preco_custo, preco_venda, imagem_path, permite_desconto):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO produtos (nome, descricao, preco_custo, preco_venda, imagem_path, permite_desconto)
            VALUES (:nome, :descricao, :custo, :venda, :img, :permite)
        """), {
            "nome": nome, "descricao": descricao, "custo": preco_custo,
            "venda": preco_venda, "img": imagem_path, "permite": 1 if permite_desconto else 0
        })

def atualizar_produto(prod_id, nome, descricao, preco_custo, preco_venda, imagem_path, permite_desconto):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE produtos 
            SET nome = :nome, descricao = :descricao, preco_custo = :custo, 
                preco_venda = :venda, imagem_path = :img, permite_desconto = :permite
            WHERE id = :id
        """), {
            "nome": nome, "descricao": descricao, "custo": preco_custo,
            "venda": preco_venda, "img": imagem_path, 
            "permite": 1 if permite_desconto else 0, "id": prod_id
        })

def excluir_produto(prod_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM produtos WHERE id = :id"), {"id": prod_id})

def listar_produtos():
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM produtos ORDER BY id DESC"), conn)
    return df

# --- FUNÇÕES CLIENTES ---
def cadastrar_cliente(nome, documento, email, telefone, endereco, observacoes):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO clientes (nome, documento, email, telefone, endereco, observacoes)
            VALUES (:nome, :doc, :email, :tel, :end, :obs)
        """), {
            "nome": nome, "doc": documento, "email": email,
            "tel": telefone, "end": endereco, "obs": observacoes
        })

def atualizar_cliente(cliente_id, nome, documento, email, telefone, endereco, observacoes):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE clientes 
            SET nome = :nome, documento = :doc, email = :email, 
                telefone = :tel, endereco = :end, observacoes = :obs
            WHERE id = :id
        """), {
            "nome": nome, "doc": documento, "email": email,
            "tel": telefone, "end": endereco, "obs": observacoes,
            "id": cliente_id
        })

def excluir_cliente(cliente_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM clientes WHERE id = :id"), {"id": cliente_id})

def listar_clientes():
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM clientes ORDER BY nome ASC"), conn)
    return df

# -------------------------------------------------------------------
# BARRA LATERAL
# -------------------------------------------------------------------
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "📋 Catálogo de Produtos"

with st.sidebar:
    st.markdown("### 📌 Navegação")
    opcoes = [
        "📋 Catálogo de Produtos", 
        "➕ Cadastrar Produto", 
        "✏️ Editar / Excluir Produto", 
        "👤 Gestão de Clientes",
        "📝 Criar Orçamento"
    ]

    for opcao in opcoes:
        tipo_botao = "primary" if st.session_state.pagina_atual == opcao else "secondary"
        if st.button(opcao, key=f"nav_{opcao}", type=tipo_botao, use_container_width=True):
            st.session_state.pagina_atual = opcao
            st.rerun()

    st.divider()
    if st.button("🚪 Sair (Logout)", type="secondary", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

menu = st.session_state.pagina_atual

# -------------------------------------------------------------------
# ABA 1: CATÁLOGO DE PRODUTOS
# -------------------------------------------------------------------
if menu == "📋 Catálogo de Produtos":
    st.header("Catálogo de Produtos")
    df_produtos = listar_produtos()

    if df_produtos.empty:
        st.info("Nenhum produto cadastrado ainda.")
    else:
        busca = st.text_input("🔍 Buscar produto por nome...", "")
        if busca:
            df_produtos = df_produtos[df_produtos["nome"].str.contains(busca, case=False, na=False)]

        st.caption(f"Exibindo {len(df_produtos)} produto(s). Clique em um item para ver detalhes e imagem.")

        for _, row in df_produtos.iterrows():
            tag_desconto = "🏷️ Aceita Desc. Progressivo" if row.get("permite_desconto", 1) == 1 else "🚫 Sem Desc. Progressivo"
            titulo_item = f"📦 {row['nome']}  —  R$ {row['preco_venda']:.2f}  ({tag_desconto})"
            
            with st.expander(titulo_item):
                col_img, col_detalhes = st.columns([1, 2])
                with col_img:
                    if row["imagem_path"] and os.path.exists(row["imagem_path"]):
                        st.image(row["imagem_path"], use_container_width=True)
                    else:
                        st.info("Sem imagem cadastrada")

                with col_detalhes:
                    st.markdown(f"### {row['nome']}")
                    st.write(f"**Descrição:** {row['descricao'] or 'Sem descrição'}")
                    st.caption(f"Configuração de Desconto: **{tag_desconto}**")
                    st.divider()
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Preço de Custo", f"R$ {row['preco_custo']:.2f}")
                    c2.metric("Preço de Venda (Base)", f"R$ {row['preco_venda']:.2f}")
                    c3.metric("Margem Bruta (Base)", f"R$ {row['preco_venda'] - row['preco_custo']:.2f}")

# -------------------------------------------------------------------
# ABA 2: CADASTRAR PRODUTO
# -------------------------------------------------------------------
elif menu == "➕ Cadastrar Produto":
    st.header("Cadastrar Novo Item")

    with st.form("form_produto", clear_on_submit=True):
        nome = st.text_input("Nome do Produto *")
        descricao = st.text_area("Descrição / Especificações")
        
        col1, col2 = st.columns(2)
        with col1:
            preco_custo = st.number_input("Preço de Custo (R$) *", min_value=0.0, format="%.2f")
        with col2:
            preco_venda = st.number_input("Preço de Venda (R$) *", min_value=0.0, format="%.2f")

        permite_desconto = st.checkbox("Permitir Desconto Progressivo por Quantidade para este item", value=True)
        foto = st.file_uploader("Foto do Produto", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("Salvar Produto")

        if submitted:
            if not nome:
                st.error("O nome do produto é obrigatório.")
            else:
                caminho_imagem = ""
                if foto is not None:
                    caminho_imagem = os.path.join(UPLOADS_DIR, foto.name)
                    with open(caminho_imagem, "wb") as f:
                        f.write(foto.getbuffer())

                cadastrar_produto(nome, descricao, preco_custo, preco_venda, caminho_imagem, permite_desconto)
                st.success(f"Produto '{nome}' cadastrado com sucesso!")

# -------------------------------------------------------------------
# ABA 3: EDITAR / EXCLUIR PRODUTO
# -------------------------------------------------------------------
elif menu == "✏️ Editar / Excluir Produto":
    st.header("Editar ou Excluir Produto")
    df_produtos = listar_produtos()

    if df_produtos.empty:
        st.info("Nenhum produto cadastrado para edição.")
    else:
        opcoes_produtos = {f"{row['id']} - {row['nome']}": row for _, row in df_produtos.iterrows()}
        produto_selecionado_str = st.selectbox("Selecione o produto que deseja alterar:", list(opcoes_produtos.keys()))
        produto_atual = opcoes_produtos[produto_selecionado_str]

        col_edit, col_img = st.columns([2, 1])

        with col_img:
            st.subheader("Imagem Atual")
            if produto_atual["imagem_path"] and os
