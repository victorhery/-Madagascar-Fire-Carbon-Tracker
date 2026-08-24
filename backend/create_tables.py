"""
Crée les tables PostgreSQL définies dans app/models/ (si elles n'existent pas déjà).

Usage :
    python create_tables.py
"""
from app.core.init_db import init_db

if __name__ == "__main__":
    init_db()
    print("Tables créées avec succès (ou déjà existantes).")