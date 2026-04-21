from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

try:
    from .config import DATABASE_URL, DATABASE_TYPE
except ImportError:
    from config import DATABASE_URL, DATABASE_TYPE

# Database engine configuration - supports SQLite, PostgreSQL, and MySQL
if DATABASE_TYPE == "sqlite":
    # SQLite doesn't use connection pooling
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # MySQL and PostgreSQL use connection pooling
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
