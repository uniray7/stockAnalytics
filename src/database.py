import os
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

# PostgreSQL connection string. Provided via DATABASE_PUBLIC_URL (user, password,
# host/fqdn, port, db name all embedded in the URL).
#   - Local dev: start.sh runs Postgres in a Docker container and exports a URL
#     pointing at localhost.
#   - Production (Railway): set DATABASE_PUBLIC_URL in the dashboard (Variables).
DATABASE_URL = os.environ.get("DATABASE_PUBLIC_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_PUBLIC_URL is not set. Point it at a PostgreSQL instance, e.g. "
        "postgresql://user:password@host:5432/dbname"
    )

# SQLAlchemy expects the 'postgresql://' scheme; some providers hand out the
# legacy 'postgres://' alias, so normalize it.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# pool_pre_ping avoids stale connections being handed out after the DB or a
# managed proxy drops idle ones (common with hosted Postgres).
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class StockData(Base):
    __tablename__ = 'stock_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

# Create tables
Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()
