"""
PostgreSQL connection setup using SQLAlchemy.
Reads DATABASE_URL from .env file.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping = True,   # prevents stale connection errors
    pool_size = 5,
    max_overflow = 10
)

SessionLocal = sessionmaker(
    autocommit = False,
    autoflush = False,
    bind = engine
)

Base = declarative_base()


def get_db():
    """Dependency — yields DB session, closes after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":

    try:
        print(f"Database URL : {DATABASE_URL}")

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        print(" SQLAlchemy imported successfully.")
        print(" Engine created successfully.")
        print(" PostgreSQL connection successful.")
        print(" database.py is working correctly!")

    except Exception as e:
        print(" Database setup failed!")
        print(f"Error: {e}")

