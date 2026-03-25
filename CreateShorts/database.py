from sqlmodel import SQLModel, create_engine, Session
import os
from dotenv import load_dotenv

load_dotenv()

# Sacamos los datos del .env para no hardcodear
DB_USER = os.getenv("POSTGRES_USER", "user_shorts")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "password_shorts")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "shorts_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# El engine es el equivalente al DataSource en Java
engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    """Crea las tablas si no existen (hibernate.hbm2ddl.auto=update)"""
    from CreateShorts.Models.database_models import SFXAsset, SFXTag, SFXAssetTagLink  # local import to avoid circular imports
    SQLModel.metadata.create_all(engine)

def get_session():
    """Generador de sesiones para FastAPI o scripts locales"""
    with Session(engine) as session:
        yield session