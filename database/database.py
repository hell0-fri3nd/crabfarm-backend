
from dotenv import load_dotenv
from os import getenv
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

load_dotenv()

DB_USER     = getenv("DB_USERNAME")
DB_PASSWORD = getenv("DB_PASSWORD")
DB_HOST     = getenv("DB_HOST", "localhost")
DB_PORT     = getenv("DB_PORT", "3306")
DB_NAME     = getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()