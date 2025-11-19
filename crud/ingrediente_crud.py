"""ingrediente_crud.py

Operaciones ORM para la tabla `ingredientes`, incluyendo carga masiva
desde CSV para acelerar la inicialización del stock.
"""
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Ingrediente


class IngredienteCRUD:
    """CRUD de ingredientes con helpers adicionales para importaciones."""

    def create_ingrediente(self, db: Session, nombre: str, unidad: Optional[str], cantidad_stock: float) -> Ingrediente:
        """Inserta un ingrediente validando el nombre y la unicidad."""
        nombre_limpio = nombre.strip().title()
        if not nombre_limpio:
            raise ValueError("El nombre del ingrediente no puede estar vacío.")

        if cantidad_stock is None or float(cantidad_stock) <= 0:
            raise ValueError("El stock debe ser un número mayor que cero.")

        ingrediente = Ingrediente(nombre=nombre_limpio, unidad=unidad, cantidad_stock=cantidad_stock)
        db.add(ingrediente)
        try:
            db.commit()
            db.refresh(ingrediente)
            return ingrediente
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Error de integridad: Ya existe un ingrediente con el nombre '{nombre_limpio}'.")

    def get_ingrediente_by_id(self, db: Session, ingrediente_id: int) -> Optional[Ingrediente]:
        """Obtiene un ingrediente por ID."""
        return db.query(Ingrediente).get(ingrediente_id)

    def get_ingrediente_by_nombre(self, db: Session, nombre: str) -> Optional[Ingrediente]:
        """Busca por nombre ignorando mayúsculas/minúsculas."""
        if not nombre:
            return None
        return (
            db.query(Ingrediente)
            .filter(func.lower(Ingrediente.nombre) == func.lower(nombre.strip()))
            .first()
        )

    def get_all_ingredientes(self, db: Session) -> List[Ingrediente]:
        """Lista los ingredientes ordenados por nombre."""
        return db.query(Ingrediente).order_by(Ingrediente.nombre).all()

    def get_ingredientes_with_filter(self, db: Session, filters: Dict[str, Any]) -> List[Ingrediente]:
        """Permite filtrar dinámicamente usando atributos del modelo."""
        query = db.query(Ingrediente)
        for attr, value in filters.items():
            if hasattr(Ingrediente, attr):
                query = query.filter(getattr(Ingrediente, attr) == value)
        return query.all()

    def delete_ingrediente_by_id(self, db: Session, ingrediente_id: int) -> bool:
        """Elimina un ingrediente existente."""
        ingrediente = self.get_ingrediente_by_id(db, ingrediente_id)
        if not ingrediente:
            return False
        # Si el ingrediente está en recetas, se eliminarán las asociaciones
        for asociacion in list(getattr(ingrediente, "menus_asociados", [])):
            db.delete(asociacion)
        db.delete(ingrediente)
        db.commit()
        return True

    def update_ingrediente(
        self,
        db: Session,
        ingrediente_id: int,
        nombre: Optional[str] = None,
        unidad: Optional[str] = None,
        cantidad_stock: Optional[float] = None,
    ) -> Optional[Ingrediente]:
        """Actualiza cualquier campo editable del ingrediente."""
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
            if float(cantidad_stock) <= 0:
                raise ValueError("El stock debe ser mayor que cero.")
            ingrediente.cantidad_stock = cantidad_stock

        try:
            db.commit()
            db.refresh(ingrediente)
            return ingrediente
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Error de integridad: Ya existe un ingrediente con el nombre '{ingrediente.nombre}'.")

    def load_ingredientes_from_csv(self, db: Session, file_path: str) -> List[Ingrediente]:
        """Carga ingredientes desde un CSV usando pandas."""
        df = pd.read_csv(file_path)
        ingredientes_creados = []

        for _, row in df.iterrows():
            try:
                cantidad = row.get("cantidad_stock", 0.0)
                if cantidad is None or float(cantidad) <= 0:
                    raise ValueError("La cantidad debe ser positiva.")
                ingrediente = self.create_ingrediente(
                    db,
                    nombre=row["nombre"],
                    unidad=row.get("unidad"),
                    cantidad_stock=cantidad,
                )
                ingredientes_creados.append(ingrediente)
            except ValueError as ve:
                print(f"Error al crear ingrediente '{row['nombre']}': {ve}")
            except Exception as e:
                print(f"Error inesperado al crear ingrediente '{row['nombre']}': {e}")

        return ingredientes_creados
