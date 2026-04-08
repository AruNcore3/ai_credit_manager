from sqlalchemy.orm.session import Session


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql+psycopg2://Servers:9244009798@localhost:5432/ai_credit_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker[Session](autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
