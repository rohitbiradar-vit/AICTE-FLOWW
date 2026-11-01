import os
import sys
import time
import logging
from typing import Optional
from sqlalchemy import text, create_engine
from alembic.config import Config
from alembic import command
from app.core.config import settings

logger = logging.getLogger("aicte_flowguard.migration")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [Migration] %(message)s"))
    logger.addHandler(handler)

ADVISORY_LOCK_ID = 26262  # SIH Problem Statement ID 26262


def wait_for_db(engine, max_retries: int = 30, retry_delay: float = 1.0) -> bool:
    """Waits for the database engine to become ready to accept connections."""
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            logger.info(
                f"Waiting for database connection (attempt {attempt}/{max_retries}): {exc}"
            )
            time.sleep(retry_delay)
    return False


def get_alembic_config(database_url: Optional[str] = None) -> Config:
    """Constructs an Alembic Config instance resolving absolute paths."""
    current_dir = os.path.dirname(os.path.abspath(__file__))  # backend/app/core
    backend_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))  # backend
    ini_path = os.path.join(backend_dir, "alembic.ini")
    script_dir = os.path.join(backend_dir, "alembic")

    if not os.path.exists(ini_path):
        raise FileNotFoundError(f"alembic.ini not found at expected path: {ini_path}")

    cfg = Config(ini_path)
    cfg.set_main_option("script_location", script_dir)
    target_url = database_url or settings.DATABASE_URL
    cfg.set_main_option("sqlalchemy.url", target_url)
    return cfg


def run_db_migrations(database_url: Optional[str] = None, max_retries: int = 30) -> None:
    """
    Executes authoritative Alembic database migrations up to 'head'.
    Uses a PostgreSQL advisory lock to prevent concurrent migrations
    when multiple backend workers or containers start simultaneously.
    """
    target_url = database_url or settings.DATABASE_URL
    is_postgres = "postgres" in target_url

    engine = create_engine(target_url, pool_pre_ping=True)

    if not wait_for_db(engine, max_retries=max_retries):
        raise RuntimeError("Database connection timed out. Migration aborted.")

    lock_conn = None
    lock_acquired = False

    try:
        if is_postgres:
            lock_conn = engine.connect()
            # Acquire PostgreSQL session-level advisory lock
            lock_conn.execute(text(f"SELECT pg_advisory_lock({ADVISORY_LOCK_ID})"))
            lock_acquired = True
            logger.info(f"Acquired database migration lock (ID: {ADVISORY_LOCK_ID}).")

        # Execute Alembic migration to head
        alembic_cfg = get_alembic_config(target_url)
        logger.info("Executing Alembic migrations up to 'head'...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Alembic database migrations completed successfully.")

    except Exception as exc:
        logger.error(f"Database migration failed: {exc}")
        raise exc
    finally:
        if lock_conn and lock_acquired:
            try:
                lock_conn.execute(text(f"SELECT pg_advisory_unlock({ADVISORY_LOCK_ID})"))
                logger.info("Released database migration lock.")
            except Exception as e:
                logger.warning(f"Failed to release advisory lock: {e}")
            finally:
                lock_conn.close()
        engine.dispose()


def reset_db_schema(database_url: Optional[str] = None, max_retries: int = 30) -> None:
    """
    Safely resets the database schema using Alembic:
    downgrades to 'base' (dropping all tables in reverse dependency order),
    and upgrades to 'head' (re-creating all tables, indexes, and constraints).
    Used primarily for clean database seeding and testing.
    """
    target_url = database_url or settings.DATABASE_URL
    is_postgres = "postgres" in target_url

    engine = create_engine(target_url, pool_pre_ping=True)

    if not wait_for_db(engine, max_retries=max_retries):
        raise RuntimeError("Database connection timed out. Schema reset aborted.")

    lock_conn = None
    lock_acquired = False

    try:
        if is_postgres:
            lock_conn = engine.connect()
            lock_conn.execute(text(f"SELECT pg_advisory_lock({ADVISORY_LOCK_ID})"))
            lock_acquired = True
            logger.info(f"Acquired database reset lock (ID: {ADVISORY_LOCK_ID}).")

        alembic_cfg = get_alembic_config(target_url)

        # Check if alembic_version exists
        with engine.connect() as check_conn:
            has_alembic = check_conn.execute(
                text("SELECT 1 FROM information_schema.tables WHERE table_name = 'alembic_version'")
            ).scalar()

        if has_alembic:
            logger.info("Downgrading database schema to base...")
            try:
                command.downgrade(alembic_cfg, "base")
            except Exception as e:
                logger.warning(f"Alembic downgrade error, proceeding with fallback drop: {e}")

        # Fallback drop to ensure completely clean slate
        from app.core.database import Base
        import app.models  # noqa
        Base.metadata.drop_all(bind=engine)
        with engine.begin() as cleanup_conn:
            cleanup_conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))

        logger.info("Re-creating database schema to head via Alembic...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Alembic database schema reset and upgrade completed successfully.")

    except Exception as exc:
        logger.error(f"Database reset failed: {exc}")
        raise exc
    finally:
        if lock_conn and lock_acquired:
            try:
                lock_conn.execute(text(f"SELECT pg_advisory_unlock({ADVISORY_LOCK_ID})"))
                logger.info("Released database reset lock.")
            except Exception as e:
                logger.warning(f"Failed to release advisory lock: {e}")
            finally:
                lock_conn.close()
        engine.dispose()

