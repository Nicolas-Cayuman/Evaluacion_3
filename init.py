# init_db.py
from database import Base, engine, create_db_and_tables
import models # <--- ¡CLAVE! Aquí forzamos la importación de todos los modelos

def initialize_database():
    print("Forzando la importación de modelos para el registro...")
    # La importación de 'models' arriba asegura que todas las clases (Cliente, Menu, etc.)
    # hereden de 'Base' y se registren en 'Base.metadata'.
    
    print("Creando la base de datos y las tablas...")
    create_db_and_tables()
    print("¡Base de datos y tablas creadas con éxito en restaurante.db!")
    
if __name__ == "__main__":
    initialize_database()