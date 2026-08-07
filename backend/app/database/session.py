import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from .env file if present
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(dotenv_path=env_path)
load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/aivoa_qms"
)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency generator function for FastAPI routes to manage database session lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
