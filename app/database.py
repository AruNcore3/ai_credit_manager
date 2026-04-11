from sqlalchemy.orm.session import Session
import os
from dotenv import load_dotenv

print("current working:dir",os.getcwd())
load_dotenv()
print("ENV VALUE:",os.getenv("DATABASE_URL"))

DB_URL = os.getenv("DATABASE_URL")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


engine = create_engine(DB_URL)
SessionLocal = sessionmaker[Session](autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

from typing import Generator
# ... keep your existing engine/Base code

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
