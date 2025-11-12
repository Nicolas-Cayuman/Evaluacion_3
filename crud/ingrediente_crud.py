# crud/ingrediente_crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from models import Ingrediente # Importa tu modelo 1.x
from typing import List, Optional, Dict, Any
import pandas as pd

class IngredienteCRUD:
    
    # create o update stock
    def create_or_update_stock(self, db: Session, nombre: str, unidad: Optional[str], cantidad: float) -> Ingrediente:
        """
        [CREATE/UPDATE] Crea un ingrediente o incrementa la cantidad si ya existe.
        """
        nombre_limpio = nombre.strip().capitalize()
        if not nombre_limpio:
            raise ValueError("El nombre del ingrediente no puede estar vacío.") 
        if cantidad <= 0:
            raise ValueError("La cantidad de stock debe ser positiva y mayor que cero.") 

        # Busca el ingrediente (sin importar mayúsculas/minúsculas)
        ingrediente = self.get_ingrediente_by_name(db, nombre_limpio)
        
        if ingrediente:
            # Si existe, actualiza el stock (UPDATE)
            ingrediente.cantidad_stock += cantidad
            ingrediente.unidad = unidad if unidad else ingrediente.unidad
        else:
            # Si no existe, lo crea (CREATE)
            ingrediente = Ingrediente(nombre=nombre_limpio, unidad=unidad, cantidad_stock=cantidad)
            db.add(ingrediente)

        try:
            db.commit() 
            db.refresh(ingrediente)
            return ingrediente
        except IntegrityError:
            db.rollback() 
            raise ValueError(f"Error de integridad: Ya existe un ingrediente con el nombre '{nombre_limpio}'.")
        except Exception as e:
            db.rollback()
            raise e

    # leer por id
    def get_ingrediente_by_id(self, db: Session, ingrediente_id: int) -> Optional[Ingrediente]:
        """[READ] Obtiene un ingrediente por su ID."""
        return db.query(Ingrediente).get(ingrediente_id)

    # leer por nombre
    def get_ingrediente_by_name(self, db: Session, nombre: str) -> Optional[Ingrediente]:
        """[READ] Obtiene un ingrediente por su nombre (insensible a mayúsculas)."""
        nombre_limpio = nombre.strip().lower()
        return db.query(Ingrediente).filter(func.lower(Ingrediente.nombre) == nombre_limpio).first()

    # leer todos
    def get_all_ingredientes(self, db: Session) -> List[Ingrediente]:
        """[READ] Obtiene todos los ingredientes."""
        return db.query(Ingrediente).order_by(Ingrediente.nombre).all()

    # eliminar por nombre
    def delete_ingrediente_by_name(self, db: Session, nombre: str) -> bool:
        """[DELETE] Elimina un ingrediente por su nombre."""
        # Usamos la función de lectura que ya tenemos
        db_ingrediente = self.get_ingrediente_by_name(db, nombre)
        if not db_ingrediente:
            return False
        db.delete(db_ingrediente)
        db.commit()
        return True
        
    # carga desde CSV
    def load_from_csv(self, db: Session, df: pd.DataFrame) -> int:
        """Carga datos desde un DataFrame (CSV) actualizando el stock."""
        rows_processed = 0
        for index, row in df.iterrows():
            try:
                nombre = str(row['nombre']).strip()
                cantidad = float(row['cantidad'])
                unidad = str(row.get('unidad', '')).strip() if 'unidad' in row and row['unidad'] else None
                
                if not nombre or cantidad <= 0:
                    continue 
                
                # Reutiliza la lógica de CREATE/UPDATE
                self.create_or_update_stock(db, nombre, unidad, cantidad)
                rows_processed += 1
            except Exception as e:
                print(f"Error al procesar la fila {index+1} del CSV: {e}")
        return rows_processed

