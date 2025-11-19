"""database.py

Configura el `Engine`, la `SessionLocal` y la `Base` declarativa que comparte
todo el ORM basado en SQLAlchemy dentro de la aplicación del restaurante.
Cada CRUD importa este módulo para abrir/cerrar sesiones contra el archivo
SQLite `restaurante.db`.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Motor de SQLAlchemy; `echo=True` permitiría inspeccionar las consultas.
engine = create_engine("sqlite:///restaurante.db", echo=False)
# Cada llamada a SessionLocal() devuelve una sesión ORM transaccional.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base que todos los modelos (ver models.py) deben heredar.
Base = declarative_base()


def create_db_and_tables():
    """Crea la base de datos y todas las tablas definidas en la metadata ORM."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Generador helper que produce una sesión y garantiza su cierre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    create_db_and_tables()
