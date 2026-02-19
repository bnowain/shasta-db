from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from .settings import settings

def _sqlite_url(path: str) -> str:
    norm = path.replace("\\", "/")
    return f"sqlite+aiosqlite:///{norm}"

engine = create_async_engine(_sqlite_url(settings.sqlite_path), future=True, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def _column_exists(conn, table: str, column: str) -> bool:
    rows = (await conn.execute(text(f"PRAGMA table_info({table});"))).fetchall()
    return any(r[1] == column for r in rows)

async def _migrate(conn):
    # Add new columns to instances if missing
    if not await _column_exists(conn, "instances", "display_title"):
        await conn.execute(text("ALTER TABLE instances ADD COLUMN display_title VARCHAR(512);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_instances_display_title ON instances(display_title);"))
    if not await _column_exists(conn, "instances", "category"):
        await conn.execute(text("ALTER TABLE instances ADD COLUMN category VARCHAR(64);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_instances_category ON instances(category);"))

    # Ensure people and instance_people exist (create_all covers it for new DBs; for existing DBs, create explicitly)
    await conn.execute(text("""
    CREATE TABLE IF NOT EXISTS people (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(160) NOT NULL UNIQUE
    );
    """))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_people_name ON people(name);"))

    await conn.execute(text("""
    CREATE TABLE IF NOT EXISTS instance_people (
        instance_id INTEGER NOT NULL,
        person_id INTEGER NOT NULL,
        source VARCHAR(32) NOT NULL DEFAULT 'manual',
        created_utc DATETIME,
        PRIMARY KEY (instance_id, person_id),
        FOREIGN KEY(instance_id) REFERENCES instances(id) ON DELETE CASCADE,
        FOREIGN KEY(person_id) REFERENCES people(id) ON DELETE CASCADE
    );
    """))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_instance_people_instance ON instance_people(instance_id);"))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_instance_people_person ON instance_people(person_id);"))

async def init_db():
    from .models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.execute(text("PRAGMA synchronous=NORMAL;"))
        await conn.execute(text("PRAGMA foreign_keys=ON;"))
        await _migrate(conn)
