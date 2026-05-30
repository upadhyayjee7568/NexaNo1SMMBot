from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.settings import settings


def _normalize_url(url: str) -> str:
    # SQLAlchemy needs the postgresql:// scheme; some providers hand out postgres://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    # Neon requires SSL. Append sslmode if it isn't already present.
    if "sslmode=" not in url and url.startswith("postgresql"):
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"
    return url


DATABASE_URL = _normalize_url(settings.database_url)

# NullPool is the safe choice on serverless (Vercel) where each invocation is short-lived
# and long-lived pooled connections would leak across frozen lambdas. Neon's own pooler
# handles connection pooling on its side.
engine = create_engine(DATABASE_URL, poolclass=NullPool, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables if they do not exist. Safe to call repeatedly."""
    # Import models so they register on Base.metadata before create_all.
    from app.db import models  # noqa: F401
    from app.db.base import Base
    from app.core.settings import settings

    Base.metadata.create_all(bind=engine)
    
    # Create default admin user if ADMIN_TELEGRAM_ID is set and user doesn't exist
    if settings.admin_telegram_id:
        db = SessionLocal()
        try:
            existing = db.query(models.User).filter(
                models.User.telegram_id == settings.admin_telegram_id
            ).first()
            if not existing:
                admin_user = models.User(
                    telegram_id=settings.admin_telegram_id,
                    role="admin",
                    is_banned=False
                )
                db.add(admin_user)
                db.commit()
                import logging
                logging.info(f"[SEED] Created admin user with telegram_id={settings.admin_telegram_id}")
        except Exception as e:
            import logging
            logging.error(f"[SEED] Failed to create admin user: {e}")
            db.rollback()
        finally:
            db.close()
