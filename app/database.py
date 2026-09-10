"""
Database connection layer.

Defaults to SQLite (zero setup, file-based) so the project runs immediately.
To use PostgreSQL or SQL Server instead, set the DATABASE_URL environment
variable before starting the app, e.g.:

  PostgreSQL:  postgresql+psycopg2://user:password@localhost:5432/apm_db
  SQL Server:  mssql+pyodbc://user:password@dsn_name

(You'll need to `pip install psycopg2-binary` or `pyodbc` respectively.)
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./apm_system.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
