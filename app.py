import streamlit as st
import os
import sqlite3
import pandas as pd
from pdf_generator import gerar_pdf_cliente, gerar_pdf_interno

# Configuração da página
st.set_page_config(
    page_title="Catálogo & Orçamentos",
    page_icon="📦",
    layout="wide"
)

# -------------------------------------------------------------------
# SISTEMA DE AUTENTICAÇÃO (LOGIN)
# -------------------------------------------------------------------
def verificar_login():
    """Gere a tela de login e valida usuario e senha."""
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

# Se não estiver logado, interrompe a execução aqui
if not verificar_login():
    st.stop()

# -------------------------------------------------------------------
# APLICAÇÃO PRINCIPAL (SÓ ACESSÍVEL APÓS LOGIN)
# -------------------------------------------------------------------

# Botão de Logout na Barra Lateral
st.sidebar.button("🚪 Sair (Logout)", on_click=lambda: st.session_state.update({"autenticado": False}))

UPLOADS_DIR = "uploads"
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

# Inicialização do Banco de Dados
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
            imagem_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def cadastrar_produto(nome, descricao, preco_custo, preco_venda, imagem_path):
    conn = sqlite3.connect("catalogo.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO produtos (nome, descricao, preco_custo, preco_venda, imagem_path)
        VALUES (?, ?, ?, ?, ?)
    ''', (nome, descricao, preco_custo, preco_venda, imagem_path))
    conn.commit()
    conn.close()

def listar_produtos():
    conn = sqlite3.connect("catalogo.db")
    df = pd.read_sql_query("SELECT * FROM produtos", conn)
    conn.close()
    return df

st.title("📦 Sistema de Catálogo e Orçamentos")

menu = st.sidebar.radio("Navegação", ["📋 Catálogo de Produtos", "➕ Cadastrar Produto", "📝 Criar Orçamento"])

# -------------------------------------------------------------------
# ABA 1: CATÁLOGO DE PRODUTOS
# -------------------------------------------------------------------
if menu == "📋 Catálogo de Produtos":
    st.header("Catálogo de Produtos")
    df_produtos = listar_produtos()

    if df_produtos.empty:
        st.info("Nenhum produto cadastrado ainda.")
    else:
        cols = st.columns(3)
        for index, row in df_produtos.iterrows():
            col = cols[index % 3]
            with col:
                st.subheader(row["nome"])
                if row["imagem_path"] and os.path.exists(row["imagem_path"]):
                    st.image(row["imagem_path"], use_container_width=True)
                else:
                    st.caption("Sem imagem cadastrada")
                
                st.write(f"**Descrição:** {row['descricao']}")
                st.write(f"**Custo (Interno):** R$ {row['preco_custo']:.2f}")
                st.write(f"**Venda (Cliente):** R$ {row['preco_venda']:.2f}")
                
                margem = row['preco_venda'] - row['preco_custo']
                st.caption(f"Margem Bruta: R$ {margem:.2f}")
                st.divider()

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

                cadastrar_produto(nome, descricao, preco_custo, preco_venda, caminho_imagem)
                st.success(f"Produto '{nome}' cadastrado com sucesso!")

# -------------------------------------------------------------------
# ABA 3: CRIAR ORÇAMENTO
# -------------------------------------------------------------------
elif menu == "📝 Criar Orçamento":
    st.header("Montar Orçamento")
    
    df_produtos = listar_produtos()

    if df_produtos.empty:
        st.warning("Cadastre produtos antes de criar um orçamento.")
    else:
        st.subheader("1. Seleção de Itens")
        
        if "carrinho" not in st.session_state:
            st.session_state.carrinho = []

        produto_selecionado = st.selectbox("Escolha um produto", df_produtos["nome"].tolist())
        qtd = st.number_input("Quantidade", min_value=1, value=1, step=1)

        if st.button("Adicionar ao Orçamento"):
            item_dados = df_produtos[df_produtos["nome"] == produto_selecionado].iloc[0].to_dict()
            item_dados["quantidade"] = qtd
            st.session_state.carrinho.append(item_dados)
            st.success(f"{qtd}x '{produto_selecionado}' adicionado!")

        if st.session_state.carrinho:
            st.subheader("2. Itens no Orçamento Atual")
            
            df_cart = pd.DataFrame(st.session_state.carrinho)
            df_cart["Subtotal Custo"] = df_cart["preco_custo"] * df_cart["quantidade"]
            df_cart["Subtotal Venda"] = df_cart["preco_venda"] * df_cart["quantidade"]

            st.dataframe(
                df_cart[["nome", "quantidade", "preco_custo", "preco_venda", "Subtotal Custo", "Subtotal Venda"]],
                use_container_width=True
            )

            total_custo = df_cart["Subtotal Custo"].sum()
            total_venda = df_cart["Subtotal Venda"].sum()
            lucro_estimado = total_venda - total_custo

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Total Custo (Interno)", f"R$ {total_custo:.2f}")
            col_b.metric("Total Venda (Cliente)", f"R$ {total_venda:.2f}")
            col_c.metric("Lucro Bruto", f"R$ {lucro_estimado:.2f}")

            if st.button("Limpar Orçamento"):
                st.session_state.carrinho = []
                st.rerun()

            st.divider()
            st.subheader("3. Gerar e Baixar Relatórios PDF")

            nome_cliente = st.text_input("Nome do Cliente (para o Orçamento)", value="Cliente")

            col_pdf1, col_pdf2 = st.columns(2)

            with col_pdf1:
                if st.button("📄 Gerar Orçamento do Cliente (PDF)"):
                    pdf_path = gerar_pdf_cliente(st.session_state.carrinho, "orcamento_cliente.pdf", nome_cliente)
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="📥 Baixar Orçamento do Cliente",
                            data=f,
                            file_name=f"Orcamento_{nome_cliente.replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )

            with col_pdf2:
                if st.button("📊 Gerar Relatório de Custo Interno (PDF)"):
                    pdf_path_interno = gerar_pdf_interno(st.session_state.carrinho, "relatorio_custos_interno.pdf")
                    with open(pdf_path_interno, "rb") as f:
                        st.download_button(
                            label="📥 Baixar Relatório Interno (Custos)",
                            data=f,
                            file_name="Relatorio_Interno_Custos.pdf",
                            mime="application/pdf"
                        )
