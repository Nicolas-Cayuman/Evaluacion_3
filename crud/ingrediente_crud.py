# crud/ingrediente_crud.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import Ingrediente 
from typing import List, Optional, Dict, Any
import pandas as pd

class IngredienteCRUD:
    # crear ingrediente
    def create_ingrediente(self, db: Session, nombre: str, unidad: Optional[str], cantidad_stock: float) -> Ingrediente:
        """[CREATE] Crea un nuevo ingrediente."""
        nombre_limpio = nombre.strip().title()
        if not nombre_limpio:
            raise ValueError("El nombre del ingrediente no puede estar vacío.")
        
        ingrediente = Ingrediente(nombre=nombre_limpio, unidad=unidad, cantidad_stock=cantidad_stock)
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
    
    # obtener ingrediente por id
    def get_ingrediente_by_id(self, db: Session, ingrediente_id: int) -> Optional[Ingrediente]:
        """[READ] Obtiene un ingrediente por su ID."""
        return db.query(Ingrediente).get(ingrediente_id)
    
    # obtener todos los ingredientes
    def get_all_ingredientes(self, db: Session) -> List[Ingrediente]:
        """[READ] Obtiene todos los ingredientes."""
        return db.query(Ingrediente).order_by(Ingrediente.nombre).all()
    
    # obtener ingredientes con filtro
    def get_ingredientes_with_filter(self, db: Session, filters: Dict[str, Any]) -> List[Ingrediente]:
        """[READ] Obtiene ingredientes aplicando filtros dinámicos."""
        query = db.query(Ingrediente)
        for attr, value in filters.items():
            if hasattr(Ingrediente, attr):
                query = query.filter(getattr(Ingrediente, attr) == value)
        return query.all()
  
    
    # eliminar ingrediente por id
    def delete_ingrediente_by_id(self, db: Session, ingrediente_id: int) -> bool:
        """[DELETE] Elimina un ingrediente por su ID."""
        ingrediente = self.get_ingrediente_by_id(db, ingrediente_id)
        if not ingrediente:
            return False
        db.delete(ingrediente)
        db.commit()
        return True
    
    # actualizar ingrediente
    def update_ingrediente(self, db: Session, ingrediente_id: int, nombre: Optional[str] = None, unidad: Optional[str] = None, cantidad_stock: Optional[float] = None) -> Optional[Ingrediente]:
        """[UPDATE] Actualiza los datos de un ingrediente."""
        ingrediente = self.get_ingrediente_by_id(db, ingrediente_id)
        if not ingrediente:
            return None
        
        if nombre:
            nombre_limpio = nombre.strip().title()
            if not nombre_limpio:
                raise ValueError("El nombre del ingrediente no puede estar vacío.")
            ingrediente.nombre = nombre_limpio
        if unidad is not None:
            ingrediente.unidad = unidad
        if cantidad_stock is not None:
            ingrediente.cantidad_stock = cantidad_stock
        
        try:
            db.commit()
            db.refresh(ingrediente)
            return ingrediente
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Error de integridad: Ya existe un ingrediente con el nombre '{ingrediente.nombre}'.")
        except Exception as e:
            db.rollback()
            raise e
        
    # cargar ingredientes desde un csv
    def load_ingredientes_from_csv(self, db: Session, file_path: str) -> List[Ingrediente]:
        """Carga ingredientes desde un archivo CSV."""
        df = pd.read_csv(file_path)
        ingredientes_creados = []
        
        for _, row in df.iterrows():
            try:
                ingrediente = self.create_ingrediente(
                    db,
                    nombre=row['nombre'],
                    unidad=row.get('unidad'),
                    cantidad_stock=row.get('cantidad_stock', 0.0)
                )
                ingredientes_creados.append(ingrediente)
            except ValueError as ve:
                print(f"Error al crear ingrediente '{row['nombre']}': {ve}")
            except Exception as e:
                print(f"Error inesperado al crear ingrediente '{row['nombre']}': {e}")
        
        return ingredientes_creados
    
