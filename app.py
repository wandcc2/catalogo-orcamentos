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
# FUNÇÃO PARA CALCULAR DESCONTO PROGRESSIVO
# -------------------------------------------------------------------
def calcular_desconto_progressivo(quantidade, preco_venda_original, permite_desconto):
    """
    Aplica a regra de desconto baseada na quantidade:
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
# BANCO DE DADOS
# -------------------------------------------------------------------
UPLOADS_DIR = "uploads"
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

def init_db():
    conn = sqlite3.connect("catalogo.db")
    c = conn.cursor()
    
    # Tabela de Produtos
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

    # Tabela de Clientes
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

# --- FUNÇÕES PRODUTOS ---
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
    """Insere produtos em lote vindos de um DataFrame Pandas."""
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

# --- FUNÇÕES CLIENTES ---
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
        WHERE id = ?
    ''', (nome, documento, email, telefone, endereco, observacoes, cliente_id))
    conn.commit()
    conn.close()

def excluir_cliente(cliente_id):
    conn = sqlite3.connect("catalogo.db")
    c = conn.cursor()
    c.execute('DELETE FROM clientes WHERE id = ?', (cliente_id,))
    conn.commit()
    conn.close()

def listar_clientes():
    conn = sqlite3.connect("catalogo.db")
    df = pd.read_sql_query("SELECT * FROM clientes ORDER BY nome ASC", conn)
    conn.close()
    return df

# -------------------------------------------------------------------
# BARRA LATERAL (NAVEGAÇÃO CORRIGIDA)
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
# ABA 2: CADASTRAR PRODUTO (COM ABAS DE IMPORTAR / EXPORTAR EXCEL)
# -------------------------------------------------------------------
elif menu == "➕ Cadastrar Produto":
    st.header("Cadastro e Gerenciamento de Produtos")

    tab_cad_ind, tab_exp_excel, tab_imp_excel = st.tabs([
        "➕ Cadastro Individual", 
        "📥 Exportar para Excel", 
        "📤 Importar via Excel / CSV"
    ])

    # --- Sub-aba 1: Cadastro Individual ---
    with tab_cad_ind:
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

    # --- Sub-aba 2: Exportar Excel ---
    with tab_exp_excel:
        st.subheader("Download da Tabela de Produtos")
        st.write("Baixe a planilha completa do seu catálogo atual no formato `.xlsx`.")
        
        df_exp = listar_produtos()
        if df_exp.empty:
            st.info("Não há produtos cadastrados para exportar.")
        else:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_exp.to_excel(writer, index=False, sheet_name='Produtos')
            buffer.seek(0)

            st.download_button(
                label="📊 Baixar Tabela de Produtos (.xlsx)",
                data=buffer,
                file_name="catalogo_produtos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # --- Sub-aba 3: Importar Excel ---
    with tab_imp_excel:
        st.subheader("Subir Produtos em Lote")
        st.write("Envie um arquivo do Excel ou CSV para cadastrar vários produtos de uma vez.")
        
        with st.expander("📌 Modelo das Colunas na Planilha"):
            st.markdown("""
            O seu arquivo precisa ter os cabeçalhos das colunas exatamente assim na primeira linha:
            * **`nome`** *(Obrigatório)*
            * **`descricao`**
            * **`preco_custo`**
            * **`preco_venda`**
            * **`permite_desconto`** *(1 = Sim, 0 = Não)*
            """)

        arquivo_upload = st.file_uploader("Selecione a planilha (.xlsx ou .csv)", type=["xlsx", "csv"])

        if arquivo_upload is not None:
            try:
                if arquivo_upload.name.endswith(".csv"):
                    df_upload = pd.read_csv(arquivo_upload)
                else:
                    df_upload = pd.read_excel(arquivo_upload)

                st.write("Preview das primeiras linhas:")
                st.dataframe(df_upload.head(10), use_container_width=True)

                if st.button("🚀 Confirmar Importação para o Catálogo"):
                    qtd = importar_produtos_df(df_upload)
                    st.success(f"Sucesso! {qtd} produto(s) foram importados com sucesso.")
                    st.rerun()

            except Exception as e:
                st.error(f"Erro ao processar a planilha: {e}")

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
            with st.form("form_editar_
