from typing import List, Optional
from sqlalchemy.orm import Session
from models import Menu, MenuIngrediente, Ingrediente

#crud menu ingrediente
    # obtener ingredientes de un menú
def get_ingredientes_by_menu(db: Session, menu_id: int) -> List[MenuIngrediente]:
    """Obtiene todos los ingredientes asociados a un menú específico."""
    return db.query(MenuIngrediente).filter(MenuIngrediente.menu_id == menu_id).all()
    # agregar ingrediente a un menú
def add_ingrediente_to_menu(db: Session, menu_id: int, ingrediente_id: int, cantidad_requerida: float) -> MenuIngrediente:
    """Agrega un ingrediente a un menú con la cantidad requerida."""
    menu = db.query(Menu).get(menu_id)
    ingrediente = db.query(Ingrediente).get(ingrediente_id)
    if not menu or not ingrediente:
        raise ValueError("Menú o ingrediente no encontrado.")
    menu_ingrediente = MenuIngrediente(
        menu=menu,
        ingrediente=ingrediente,
        cantidad_requerida=cantidad_requerida
    )
    db.add(menu_ingrediente)
    db.commit()
    db.refresh(menu_ingrediente)
    return menu_ingrediente
    # eliminar ingrediente de un menú
def remove_ingrediente_from_menu(db: Session, menu_id: int, ingrediente_id: int) -> bool:
    """Elimina un ingrediente de un menú específico."""
    menu_ingrediente = db.query(MenuIngrediente).filter(
        MenuIngrediente.menu_id == menu_id,
        MenuIngrediente.ingrediente_id == ingrediente_id
    ).first()
    if not menu_ingrediente:
        return False
    db.delete(menu_ingrediente)
    db.commit()
    return True
    # actualizar cantidad requerida de un ingrediente en un menú
def update_ingrediente_quantity_in_menu(db: Session, menu_id: int, ingrediente_id: int, nueva_cantidad: float) -> Optional[MenuIngrediente]:
    """Actualiza la cantidad requerida de un ingrediente en un menú."""
    menu_ingrediente = db.query(MenuIngrediente).filter(
        MenuIngrediente.menu_id == menu_id,
        MenuIngrediente.ingrediente_id == ingrediente_id
    ).first()
    if not menu_ingrediente:
        return None
    menu_ingrediente.cantidad_requerida = nueva_cantidad
    db.commit()
    db.refresh(menu_ingrediente)
    return menu_ingrediente

