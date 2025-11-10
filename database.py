# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# NOTA: Importamos los modelos aquí para que Base.metadata los conozca.
# Ahora importamos 'models' aquí, antes de usarlo en create_db_and_tables,
# pero ¡es mejor dejarlo en el archivo de inicialización si se usa el patrón
# de ejecución de abajo!

engine = create_engine("sqlite:///restaurante.db", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# La clase Base debe definirse una sola vez y no en el bloque __main__
Base = declarative_base()

def create_db_and_tables():
    """Crea la base de datos y todas las tablas definidas."""

    # Se cargan todas las tablas creadas, heredadas de (Base) 
    Base.metadata.create_all(bind=engine)
    
def get_db():
    # ... (el resto del código es igual)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    create_db_and_tables()