import sys
import os
from urllib.parse import urlparse
import psycopg2
from dotenv import load_dotenv

# Add backend directory to sys.path to allow absolute imports when executing script standalone
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))


def ensure_database_exists():
    """
    Connect to default 'postgres' database and create target database if it doesn't exist.
    """
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/aivoa_qms"
    )
    result = urlparse(db_url)
    target_db = result.path.lstrip("/") or "aivoa_qms"
    username = result.username or "postgres"
    password = result.password or ""
    hostname = result.hostname or "localhost"
    port = result.port or 5432

    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=username,
            password=password,
            host=hostname,
            port=port
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (target_db,))
        exists = cur.fetchone()
        if not exists:
            print(f"Database '{target_db}' does not exist. Creating it now...")
            cur.execute(f'CREATE DATABASE "{target_db}";')
            print(f"Database '{target_db}' created successfully!")
        else:
            print(f"Database '{target_db}' already exists.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Notice during database check: {e}")


def init_db(reset: bool = True):
    """
    Ensure database exists, then initialize tables. If reset=True, drop tables first.
    """
    ensure_database_exists()

    from app.database.session import engine, Base
    from app.models.complaint import Complaint, ChatMessage  # Register metadata

    if reset:
        print("Dropping existing tables to start fresh...")
        Base.metadata.drop_all(bind=engine)
        print("Existing tables dropped successfully.")

    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db(reset=True)
