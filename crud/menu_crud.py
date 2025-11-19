"""menu_crud.py

Encapsula la gestión de `Menu` y sus relaciones con ingredientes. Usa
`joinedload` para evitar N+1 y delega validaciones de ingredientes al
`IngredienteCRUD`.
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from crud.ingrediente_crud import IngredienteCRUD
from models import Ingrediente, Menu, MenuIngrediente


class MenuCRUD:
    """CRUD de menús que también maneja la tabla intermedia."""

    def __init__(self):
        self.ingrediente_crud = IngredienteCRUD()

    def create_menu(
        self,
        db: Session,
        nombre: str,
        precio: float,
        icono_path: Optional[str],
        ingredientes: List[Dict[str, Any]],
    ) -> Menu:
        """Crea un menú y registra sus ingredientes asociados."""
        nombre_limpio = nombre.strip().title()
        if not nombre_limpio:
            raise ValueError("El nombre del menú no puede estar vacío.")

        menu = Menu(nombre=nombre_limpio, precio=precio, icono_path=icono_path)
        db.add(menu)
        db.flush()

        for item in ingredientes:
            ingrediente = self.ingrediente_crud.get_ingrediente_by_id(db, item["ingrediente_id"])
            if not ingrediente:
                raise ValueError(f"Ingrediente con ID {item['ingrediente_id']} no encontrado.")

            menu_ingrediente = MenuIngrediente(
                menu_id=menu.id,
                ingrediente_id=ingrediente.id,
                cantidad_requerida=item["cantidad_requerida"],
            )
            db.add(menu_ingrediente)

        try:
            db.commit()
            db.refresh(menu)
            return menu
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Error de integridad: Ya existe un menú con el nombre '{nombre_limpio}'.")

    def get_menu_by_id(self, db: Session, menu_id: int) -> Optional[Menu]:
        """Obtiene un menú por ID y carga eager sus ingredientes."""
        return (
            db.query(Menu)
            .options(joinedload(Menu.ingredientes_asociados).joinedload(MenuIngrediente.ingrediente))
            .filter(Menu.id == menu_id)
            .first()
        )

    def get_menu_by_name(self, db: Session, nombre: str) -> Optional[Menu]:
        """Busca por nombre de forma case-insensitive."""
        nombre_limpio = nombre.strip().title()
        return (
            db.query(Menu)
            .options(joinedload(Menu.ingredientes_asociados).joinedload(MenuIngrediente.ingrediente))
            .filter(func.lower(Menu.nombre) == func.lower(nombre_limpio))
            .first()
        )

    def get_all_menus(self, db: Session) -> List[Menu]:
        """Lista todos los menús con sus relaciones cargadas."""
        return (
            db.query(Menu)
            .options(joinedload(Menu.ingredientes_asociados).joinedload(MenuIngrediente.ingrediente))
            .order_by(Menu.nombre)
            .all()
        )

    def delete_menu_by_name(self, db: Session, nombre: str) -> bool:
        """Elimina un menú por nombre."""
        menu = self.get_menu_by_name(db, nombre)
        if not menu:
            return False
        db.delete(menu)
        db.commit()
        return True

    def update_menu(
        self,
        db: Session,
        menu_id: int,
        nombre: Optional[str] = None,
        precio: Optional[float] = None,
        icono_path: Optional[str] = None,
        ingredientes: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Menu]:
        """Actualiza los datos del menú y opcionalmente su receta."""
        menu = self.get_menu_by_id(db, menu_id)
        if not menu:
            return None

        if nombre:
            nombre_limpio = nombre.strip().title()
            if not nombre_limpio:
                raise ValueError("El nombre del menú no puede estar vacío.")
            menu.nombre = nombre_limpio
        if precio is not None:
            menu.precio = precio
        if icono_path is not None:
            menu.icono_path = icono_path

        if ingredientes is not None:
            for assoc in menu.ingredientes_asociados:
                db.delete(assoc)
            db.flush()

            for item in ingredientes:
                ingrediente = self.ingrediente_crud.get_ingrediente_by_id(db, item["ingrediente_id"])
                if not ingrediente:
                    raise ValueError(f"Ingrediente con ID {item['ingrediente_id']} no encontrado.")
                menu_ingrediente = MenuIngrediente(
                    menu_id=menu.id,
                    ingrediente_id=ingrediente.id,
                    cantidad_requerida=item["cantidad_requerida"],
                )
                db.add(menu_ingrediente)

        try:
            db.commit()
            db.refresh(menu)
            return menu
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Error de integridad: Ya existe un menú con el nombre '{menu.nombre}'.")

    def esta_disponible(self, db: Session, menu: Menu, cantidad_pedido: int = 1) -> bool:
        """Verifica si hay stock suficiente para preparar el menú solicitado."""
        if not menu.ingredientes_asociados:
            return False

        for assoc in menu.ingredientes_asociados:
            ingrediente_stock: Ingrediente = assoc.ingrediente
            if not ingrediente_stock:
                return False

            consumo_total = assoc.cantidad_requerida * cantidad_pedido
            if ingrediente_stock.cantidad_stock < consumo_total:
                return False

        return True

    def consumir_stock(self, db: Session, menu: Menu, cantidad_pedido: int):
        """Descuenta el stock de cada ingrediente participante del menú."""
        for assoc in menu.ingredientes_asociados:
            ingrediente = assoc.ingrediente
            consumo_total = assoc.cantidad_requerida * cantidad_pedido
            ingrediente.consumir(db, consumo_total)
        db.commit()

    def restaurar_stock(self, db: Session, menu: Menu, cantidad_pedido: int):
        """Devuelve al stock los ingredientes consumidos para un menú."""
        for assoc in menu.ingredientes_asociados:
            ingrediente = assoc.ingrediente
            ingrediente.cantidad_stock += assoc.cantidad_requerida * cantidad_pedido
        db.commit()
