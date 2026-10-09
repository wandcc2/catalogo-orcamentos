import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from pdf_generator import gerar_pdf_cliente, gerar_pdf_interno

st.set_page_config(
    page_title="Catalogo & Orcamentos",
    page_icon="📦",
    layout="wide"
)

@st.cache_resource
def get_db_engine():
    db_url = st.secrets["postgres"]["url"]
    return create_engine(db_url, pool_pre_ping=True)

engine = get_db_engine()

def calcular_desconto(qtd, preco, permite):
    if not permite:
        return 0.0, preco
    if qtd >= 51:
        pct = 0.25
    elif qtd >= 41:
        pct = 0.22
    elif qtd >= 31:
        pct = 0.20
    elif qtd >= 21:
        pct = 0.15
    elif qtd >= 11:
        pct = 0.10
    else:
        pct = 0.0
    return pct, preco * (1 - pct)

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

def cadastrar_produto(nome, desc, custo, venda, img, permite):
    sql = (
        "INSERT INTO produtos "
        "(nome, descricao, preco_custo, preco_venda, imagem_path, permite_desconto) "
        "VALUES (:nome, :desc, :custo, :venda, :img, :permite);"
    )
    params = {
        "nome": nome, "desc": desc, "custo": custo,
        "venda": venda, "img": img, "permite": 1 if permite else 0
    }
    with engine.begin() as conn:
        conn.execute(text(sql), params)

def atualizar_produto(p_id, nome, desc, custo, venda, img, permite):
    sql = (
        "UPDATE produtos SET nome = :nome, descricao = :desc, "
        "preco_custo = :custo, preco_venda = :venda, "
        "imagem_path = :img, permite_desconto = :permite "
        "WHERE id = :id;"
    )
    params = {
        "nome": nome, "desc": desc, "custo": custo,
        "venda": venda, "img": img, "permite": 1 if permite else 0, "id": p_id
    }
    with engine.begin() as conn:
        conn.execute(text(sql), params)

def excluir_produto(p_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM produtos WHERE id = :id;"), {"id": p_id})

def listar_produtos():
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM produtos ORDER BY id DESC;"), conn)
    return df

def cadastrar_cliente(nome, doc, email, tel, end, obs):
    sql = (
        "INSERT INTO clientes "
        "(nome, documento, email, telefone, endereco, observacoes) "
        "VALUES (:nome, :doc, :email, :tel, :end, :obs);"
    )
    params = {
        "nome": nome, "doc": doc, "email": email,
        "tel": tel, "end": end, "obs": obs
    }
    with engine.begin() as conn:
        conn.execute(text(sql), params)

def atualizar_cliente(c_id, nome, doc, email, tel, end, obs):
    sql = (
        "UPDATE clientes SET nome = :nome, documento = :doc, "
        "email = :email, telefone = :tel, endereco = :end, "
        "observacoes = :obs WHERE id = :id;"
    )
    params = {
        "nome": nome, "doc": doc, "email": email,
        "tel": tel, "end": end, "obs": obs, "id": c_id
    }
    with engine.begin() as conn:
        conn.execute(text(sql), params)

def excluir_cliente(c_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM clientes WHERE id = :id;"), {"id": c_id})

def listar_clientes():
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM clientes ORDER BY nome ASC;"), conn)
    return df

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.subheader("Acesso Restrito")
        with st.form("form_login"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                if usuario == "admin" and senha == "050391":
                    st.session_state.autenticado = True
                    st.session_state.pagina_atual = "Catalogo de Produtos"
                    st.rerun()
                else:
                    st.error("Dados incorretos.")
    st.stop()

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
        ativo = st.session_state.pagina_atual == opcao
        if st.button(opcao, key=f"nav_{opcao}", type="primary" if ativo else "secondary", use_container_width=True):
            st.session_state.pagina_atual = opcao
            st.rerun()
    st.divider()
    if st.button("Sair", type="secondary", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

menu = st.session_state.pagina_atual

if menu == "Catalogo de Produtos":
    st.header("Catálogo de Produtos")
    df_p = listar_produtos()

    if df_p.empty:
        st.info("Nenhum produto cadastrado.")
    else:
        busca = st.text_input("Buscar produto por nome...", "")
        if busca:
            condicao = df_p["nome"].str.contains(busca, case=False, na=False)
            df_p = df_p[condicao]

        st.caption(f"Exibindo {len(df_p)} produto(s).")

        for _, row in df_p.iterrows():
            permite = row.get("permite_desconto", 1) == 1
            tag = "Com Desconto" if permite else "Sem Desconto"
            titulo = f"{row['nome']} - R$ {row['preco_venda']:.2f} ({tag})"

            with st.expander(titulo):
                col_img, col_det = st.columns([1, 2])
                with col_img:
                    if row["imagem_path"] and os.path.exists(row["imagem_path"]):
                        st.image(row["imagem_path"], use_container_width=True)
                    else:
                        st.info("Sem imagem")

                with col_det:
                    st.markdown(f"### {row['nome']}")
                    st.write(f"**Descrição:** {row['descricao'] or 'Sem descrição'}")
                    st.caption(f"Desconto: **{tag}**")
                    st.divider()
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Custo", f"R$ {row['preco_custo']:.2f}")
                    k2.metric("Venda", f"R$ {row['preco_venda']:.2f}")
                    k3.metric("Margem", f"R$ {row['preco_venda'] - row['preco_custo']:.2f}")

elif menu == "Cadastrar Produto":
    st.header("Novo Produto")
    with st.form("form_prod", clear_on_submit=True):
        nome = st.text_input("Nome do Produto *")
        desc = st.text_area("Descrição")
        c1, c2 = st.columns(2)
        with c1:
            custo = st.number_input("Preço Custo (R$) *", min_value=0.0, format="%.2f")
        with c2:
            venda = st.number_input("Preço Venda (R$) *", min_value=0.0, format="%.2f")
        permite = st.checkbox("Permitir Desconto Progressivo", value=True)
        foto = st.file_uploader("Foto", type=["png", "jpg", "jpeg"])
        
        if st.form_submit_button("Salvar Produto"):
            if not nome:
                st.error("Nome é obrigatório.")
            else:
                img_path = ""
                if foto is not None:
                    img_path = os.path.join(UPLOADS_DIR, foto.name)
                    with open(img_path, "wb") as f:
                        f.write(foto.getbuffer())
                cadastrar_produto(nome, desc, custo, venda, img_path, permite)
                st.success("Produto salvo na nuvem!")

elif menu == "Editar / Excluir Produto":
    st.header("Editar / Excluir Produto")
    df_p = listar_produtos()

    if df_p.empty:
        st.info("Nenhum produto cadastrado.")
    else:
        opcoes = {f"{r['id']} - {r['nome']}": r for _, r in df_p.iterrows()}
        prod = opcoes[st.selectbox("Selecione:", list(opcoes.keys()))]

        col_e, col_i = st.columns([2, 1])
        with col_i:
            if prod["imagem_path"] and os.path.exists(prod["imagem_path"]):
                st.image(prod["imagem_path"], use_container_width=True)
            else:
                st.caption("Sem imagem.")

        with col_e:
            with st.form("form_edit_prod"):
                n_nome = st.text_input("Nome", value=prod["nome"])
                n_desc = st.text_area("Descrição", value=prod["descricao"] or "")
                m1, m2 = st.columns(2)
                with m1:
                    n_custo = st.number_input("Custo (R$)", value=float(prod["preco_custo"]), min_value=0.0, format="%.2f")
                with m2:
                    n_venda = st.number_input("Venda (R$)", value=float(prod["preco_venda"]), min_value=0.0, format="%.2f")
                n_permite = st.checkbox("Desconto Progressivo", value=bool(prod.get("permite_desconto", 1)))
                n_foto = st.file_uploader("Trocar Imagem", type=["png", "jpg", "jpeg"])

                if st.form_submit_button("Salvar Alterações"):
                    img_path = prod["imagem_path"]
                    if n_foto is not None:
                        img_path = os.path.join(UPLOADS_DIR, n_foto.name)
                        with open(img_path, "wb") as f:
                            f.write(n_foto.getbuffer())
                    atualizar_produto(prod["id"], n_nome, n_desc, n_custo, n_venda, img_path, n_permite)
                    st.success("Atualizado!")
                    st.rerun()

        st.divider()
        if st.button("Excluir Produto", type="primary"):
            excluir_produto(prod["id"])
            st.success("Removido!")
            st.rerun()

elif menu == "Gestao de Clientes":
    st.header("Gestão de Clientes")
    t_list, t_cad, t_edit = st.tabs(["Lista", "Cadastrar", "Editar / Excluir"])

    with t_list:
        df_c = listar_clientes()
        if df_c.empty:
            st.info("Nenhum cliente cadastrado.")
        else:
            busca_c = st.text_input("Buscar cliente...", "")
            if busca_c:
                cond_c = df_c["nome"].str.contains(busca_c, case=False, na=False) | df_c["documento"].str.contains(busca_c, case=False, na=False)
                df_c = df_c[cond_c]
            st.caption(f"Exibindo {len(df_c)} cliente(s).")
            for _, cli in df_c.iterrows():
                with st.expander(f"{cli['nome']} | Tel: {cli['telefone'] or 'N/A'}"):
                    x1, x2 = st.columns(2)
                    with x1:
                        st.write(f"**Doc:** {cli['documento'] or 'N/A'}")
                        st.write(f"**Email:** {cli['email'] or 'N/A'}")
                    with x2:
                        st.write(f"**Endereço:** {cli['endereco'] or 'N/A'}")
                    st.write(f"**Obs:** {cli['observacoes'] or 'N/A'}")

    with t_cad:
        with st.form("form_cad_cli", clear_on_submit=True):
            nome_c = st.text_input("Nome / Razão Social *")
            d1, d2 = st.columns(2)
            with d1:
                doc_c = st.text_input("CPF / CNPJ")
                email_c = st.text_input("E-mail")
            with d2:
                tel_c = st.text_input("Telefone")
                end_c = st.text_input("Endereço")
            obs_c = st.text_area("Observações")
            if st.form_submit_button("Cadastrar Cliente"):
                if not nome_c:
                    st.error("Nome é obrigatório.")
                else:
                    cadastrar_cliente(nome_c, doc_c, email_c, tel_c, end_c, obs_c)
                    st.success("Cliente cadastrado!")
                    st.rerun()

    with t_edit:
        df_c = listar_clientes()
        if df_c.empty:
            st.info("Nenhum cliente cadastrado.")
        else:
            op_c = {f"{c['id']} - {c['nome']}": c for _, c in df_c.iterrows()}
            cli_atual = op_c[st.selectbox("Selecione:", list(op_c.keys()))]
            with st.form("form_edit_cli"):
                e_nome = st.text_input("Nome", value=cli_atual["nome"])
                w1, w2 = st.columns(2)
                with w1:
                    e_doc = st.text_input("CPF / CNPJ", value=cli_atual["documento"] or "")
                    e_email = st.text_input("E-mail", value=cli_atual["email"] or "")
                with w2:
                    e_tel = st.text_input("Telefone", value=cli_atual["telefone"] or "")
                    e_end = st.text_input("Endereço", value=cli_atual["endereco"] or "")
                e_obs = st.text_area("Observações", value=cli_atual["observacoes"] or "")
                if st.form_submit_button("Salvar Alterações"):
                    atualizar_cliente(cli_atual["id"], e_nome, e_doc, e_email, e_tel, e_end, e_obs)
                    st.success("Atualizado!")
                    st.rerun()
            st.divider()
            if st.button("Excluir Cliente", type="primary"):
                excluir_cliente(cli_atual["id"])
                st.success("Removido!")
                st.rerun()

elif menu == "Criar Orcamento":
    st.header("Montar Orçamento")
    df_p = listar_produtos()

    if df_p.empty:
        st.warning("Cadastre produtos antes de criar um orçamento.")
    else:
        if "carrinho" not in st.session_state:
            st.session_state.carrinho = []

        prod_sel = st.selectbox("Escolha o produto:", df_p["nome"].tolist())
        qtd = st.number_input("Quantidade", min_value=1, value=1, step=1)
        item_dados = df_p[df_p["nome"] == prod_sel].iloc[0].to_dict()
        permite_desc = bool(item_dados.get("permite_desconto", 1))

        pct_d, _ = calcular_desconto(qtd, 1.0, permite_desc)
        if permite_desc and pct_d > 0:
            st.info(f"Desconto aplicado: **{int(pct_d * 100)}%**")

        if st.button("Adicionar ao Orçamento"):
            pct, preco_desc = calcular_desconto(qtd, item_dados["preco_venda"], permite_desc)
            item_dados["quantidade"] = qtd
            item_dados["preco_venda_original"] = item_dados["preco_venda"]
            item_dados["preco_venda"] = preco_desc
            item_dados["desconto_aplicado"] = f"{int(pct * 100)}%" if permite_desc else "N/A"
            st.session_state.carrinho.append(item_dados)
            st.success("Adicionado!")

        if st.session_state.carrinho:
            df_cart = pd.DataFrame(st.session_state.carrinho)
            df_cart["Subtotal"] = df_cart["preco_venda"] * df_cart["quantidade"]
            st.dataframe(df_cart[["nome", "quantidade", "preco_venda", "Subtotal"]], use_container_width=True)

            if st.button("Limpar Orçamento"):
                st.session_state.carrinho = []
                st.rerun()

            st.divider()
            df_c = listar_clientes()
            op_c_orc = ["-- Digitar Manualmente --"] + (df_c["nome"].tolist() if not df_c.empty else [])
            cli_sel_op = st.selectbox("Cliente:", op_c_orc)
            nome_cli_final = st.text_input("Nome do Cliente", value="Cliente") if cli_sel_op == "-- Digitar Manualmente --" else cli_sel_op

            p1, p2 = st.columns(2)
            with p1:
                if st.button("Gerar Orçamento PDF"):
                    pdf_p = gerar_pdf_cliente(st.session_state.carrinho, "orcamento.pdf", nome_cli_final)
                    with open(pdf_p, "rb") as f:
                        st.download_button("Baixar PDF Cliente", f, file_name="Orcamento.pdf", mime="application/pdf")
            with p2:
                if st.button("Gerar Relatório Interno PDF"):
                    pdf_pi = gerar_pdf_interno(st.session_state.carrinho, "relatorio.pdf")
                    with open(pdf_pi, "rb") as f:
                        st.download_button("Baixar Relatório Interno", f, file_name="Relatorio.pdf", mime="application/pdf")
