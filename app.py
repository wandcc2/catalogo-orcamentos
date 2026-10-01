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
# FUNÇÃO PARA CALCULAR DESCONTO PROGRESSIVO
# -------------------------------------------------------------------
def calcular_desconto_progressivo(quantidade, preco_venda_original):
    """
    Aplica a regra de desconto baseada na quantidade:
    - Até 10 peças: 0% de desconto
    - 11 a 19 peças: 10% de desconto
    - 20 ou mais peças: 15% de desconto
    """
    if quantidade >= 20:
        percentual_desconto = 0.15
    elif quantidade >= 11:
        percentual_desconto = 0.10
    else:
        percentual_desconto = 0.0

    preco_com_desconto = preco_venda_original * (1 - percentual_desconto)
    return percentual_desconto, preco_com_desconto

# -------------------------------------------------------------------
# ESTILIZAÇÃO CSS PARA OS BOTÕES
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

def atualizar_produto(prod_id, nome, descricao, preco_custo, preco_venda, imagem_path):
    conn = sqlite3.connect("catalogo.db")
    c = conn.cursor()
    c.execute('''
        UPDATE produtos 
        SET nome = ?, descricao = ?, preco_custo = ?, preco_venda = ?, imagem_path = ?
        WHERE id = ?
    ''', (nome, descricao, preco_custo, preco_venda, imagem_path, prod_id))
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
            titulo_item = f"📦 {row['nome']}  —  R$ {row['preco_venda']:.2f}"
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
            if produto_atual["imagem_path"] and os.path.exists(produto_atual["imagem_path"]):
                st.image(produto_atual["imagem_path"], use_container_width=True)
            else:
                st.caption("Sem imagem cadastrada.")

        with col_edit:
            with st.form("form_editar_produto"):
                novo_nome = st.text_input("Nome do Produto", value=produto_atual["nome"])
                nova_descricao = st.text_area("Descrição", value=produto_atual["descricao"] or "")
                
                c1, c2 = st.columns(2)
                with c1:
                    novo_custo = st.number_input("Preço de Custo (R$)", value=float(produto_atual["preco_custo"]), min_value=0.0, format="%.2f")
                with c2:
                    novo_venda = st.number_input("Preço de Venda (R$)", value=float(produto_atual["preco_venda"]), min_value=0.0, format="%.2f")

                nova_foto = st.file_uploader("Substituir Imagem (Deixe vazio para manter a atual)", type=["png", "jpg", "jpeg"])
                btn_atualizar = st.form_submit_button("💾 Salvar Alterações")

                if btn_atualizar:
                    caminho_imagem = produto_atual["imagem_path"]
                    if nova_foto is not None:
                        caminho_imagem = os.path.join(UPLOADS_DIR, nova_foto.name)
                        with open(caminho_imagem, "wb") as f:
                            f.write(nova_foto.getbuffer())

                    atualizar_produto(produto_atual["id"], novo_nome, nova_descricao, novo_custo, novo_venda, caminho_imagem)
                    st.success("Produto atualizado com sucesso!")
                    st.rerun()

        st.divider()
        st.subheader("⚠️ Zona de Perigo")
        if st.button("🗑 Excluir Produto do Catálogo", type="primary"):
            excluir_produto(produto_atual["id"])
            st.success(f"Produto '{produto_atual['nome']}' foi excluído.")
            st.rerun()

# -------------------------------------------------------------------
# ABA 4: CRIAR ORÇAMENTO (COM DESCONTO PROGRESSIVO)
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
        qtd = st.number_input("Quantidade de Peças", min_value=1, value=1, step=1)

        # Informação em tempo real sobre a faixa de desconto atrelada à quantidade escolhida
        pct_disc, _ = calcular_desconto_progressivo(qtd, 1.0)
        if pct_disc > 0:
            st.info(f"🎉 Desconto Progressivo Aplicado: **{int(pct_disc*100)}% de Desconto** para {qtd} unidades!")
        else:
            st.caption("💡 Dica: A partir de 11 unidades você ganha 10% de desconto, e a partir de 20 unidades ganha 15%!")

        if st.button("Adicionar ao Orçamento"):
            item_dados = df_produtos[df_produtos["nome"] == produto_selecionado].iloc[0].to_dict()
            
            # Aplica a regra de desconto
            pct_desconto, preco_venda_com_desconto = calcular_desconto_progressivo(qtd, item_dados["preco_venda"])
            
            item_dados["quantidade"] = qtd
            item_dados["preco_venda_original"] = item_dados["preco_venda"]
            item_dados["preco_venda"] = preco_venda_com_desconto
            item_dados["desconto_aplicado"] = f"{int(pct_desconto * 100)}%"
            
            st.session_state.carrinho.append(item_dados)
            st.success(f"{qtd}x '{produto_selecionado}' adicionado com {int(pct_desconto * 100)}% de desconto!")

        if st.session_state.carrinho:
            st.subheader("2. Itens no Orçamento Atual")
            
            df_cart = pd.DataFrame(st.session_state.carrinho)
            df_cart["Subtotal Custo"] = df_cart["preco_custo"] * df_cart["quantidade"]
            df_cart["Subtotal Venda"] = df_cart["preco_venda"] * df_cart["quantidade"]

            st.dataframe(
                df_cart[[
                    "nome", 
                    "quantidade", 
                    "preco_venda_original", 
                    "desconto_aplicado", 
                    "preco_venda", 
                    "Subtotal Venda"
                ]].rename(columns={
                    "nome": "Produto",
                    "quantidade": "Qtd",
                    "preco_venda_original": "Preço Tabela (R$)",
                    "desconto_aplicado": "Desconto",
                    "preco_venda": "Preço c/ Desc. (R$)",
                    "Subtotal Venda": "Subtotal (R$)"
                }),
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
