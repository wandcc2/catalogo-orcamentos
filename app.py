@st.cache_resource
def get_db_engine():
    db_url = st.secrets["postgres"]["url"]
    # Garante que o SQLAlchemy use explicitamente o psycopg2
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return create_engine(db_url, pool_pre_ping=True)
