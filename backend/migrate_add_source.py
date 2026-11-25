from sqlalchemy import text

from app.core.database import engine


with engine.begin() as connection:
    connection.execute(text("""
        ALTER TABLE burned_areas
        ADD COLUMN IF NOT EXISTS source VARCHAR NOT NULL DEFAULT 'modis';
    """))

print("OK : colonne source ajoutée ou déjà existante.")