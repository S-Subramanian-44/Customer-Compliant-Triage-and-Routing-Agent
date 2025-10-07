from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    from . import models
    Base.metadata.create_all(bind=engine)
    # Run a lightweight direct sqlite migration to add missing columns
    try:
        run_sqlite_migrations(DATABASE_URL)
    except Exception:
        # don't crash startup on migration problems; SLA loop will handle schema errors gracefully
        pass


def run_sqlite_migrations(database_url: str):
    """For sqlite DATABASE_URL like sqlite:///./complaints.db, open the file and add missing columns.

    This uses sqlite3 directly to ensure ALTER TABLE statements run against the file.
    """
    import sqlite3

    if not database_url.startswith('sqlite'):
        return

    # extract file path
    path = None
    if database_url.startswith('sqlite:///'):
        path = database_url.split('sqlite:///', 1)[1]
    elif database_url.startswith('sqlite://'):
        path = database_url.split('sqlite://', 1)[1]
    if not path:
        return

    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info('complaints')")
    rows = cur.fetchall()
    existing = {r[1] for r in rows}
    if 'llm_classification' not in existing:
        try:
            cur.execute("ALTER TABLE complaints ADD COLUMN llm_classification TEXT")
        except Exception:
            pass
    if 'llm_routing' not in existing:
        try:
            cur.execute("ALTER TABLE complaints ADD COLUMN llm_routing TEXT")
        except Exception:
            pass
    conn.commit()
    conn.close()
