# menu CRUD
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import Menu, MenuIngrediente, Ingrediente
from typing import List, Optional, Dict, Any

class MenuCRUD:
    # crear menú
    def create_menu(self, db: Session, nombre: str, precio: float, icono_path: Optional[str], ingredientes: List[Dict[str, Any]]) -> Menu:
        """[CREATE] Crea un nuevo menú con sus ingredientes asociados."""
        nombre_limpio = nombre.strip().title()
        if not nombre_limpio:
            raise ValueError("El nombre del menú no puede estar vacío.")
        
        menu = Menu(nombre=nombre_limpio, precio=precio, icono_path=icono_path)
        db.add(menu)
        
        # Asociar ingredientes
        for item in ingredientes:
            ingrediente = db.query(Ingrediente).get(item['ingrediente_id'])
            if not ingrediente:
                raise ValueError(f"Ingrediente con ID {item['ingrediente_id']} no encontrado.")
            menu_ingrediente = MenuIngrediente(
                menu=menu,
                ingrediente=ingrediente,
                cantidad_requerida=item['cantidad_requerida']
            )
            db.add(menu_ingrediente)
        
        try:
            db.commit()
            db.refresh(menu)
            return menu
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Error de integridad: Ya existe un menú con el nombre '{nombre_limpio}'.")
        except Exception as e:
            db.rollback()
            raise e
        
    # obtener menú por id
    def get_menu_by_id(self, db: Session, menu_id: int) -> Optional[Menu]:
        """[READ] Obtiene un menú por su ID."""
        return db.query(Menu).get(menu_id)
    
    # obtener todos los menús
    def get_all_menus(self, db: Session) -> List[Menu]:
        """[READ] Obtiene todos los menús."""
        return db.query(Menu).order_by(Menu.nombre).all()
    
    # eliminar menú por nombre
    def delete_menu_by_name(self, db: Session, nombre: str) -> bool:
        """[DELETE] Elimina un menú por su nombre."""
        nombre_limpio = nombre.strip().title()
        menu = db.query(Menu).filter(Menu.nombre == nombre_limpio).first()
        if not menu:
            return False
        db.delete(menu)
        db.commit()
        return True
    
    # actualizar menú
    def update_menu(self, db: Session, menu_id: int, nombre: Optional[str] = None, precio: Optional[float] = None, icono_path: Optional[str] = None, ingredientes: Optional[List[Dict[str, Any]]] = None) -> Optional[Menu]:
        """[UPDATE] Actualiza los datos de un menú."""
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
            # Eliminar asociaciones existentes
            menu.ingredientes_asociados.clear()
            db.flush()  # Asegura que los cambios se reflejen antes de agregar nuevos
            
            # Asociar nuevos ingredientes
            for item in ingredientes:
                ingrediente = db.query(Ingrediente).get(item['ingrediente_id'])
                if not ingrediente:
                    raise ValueError(f"Ingrediente con ID {item['ingrediente_id']} no encontrado.")
                menu_ingrediente = MenuIngrediente(
                    menu=menu,
                    ingrediente=ingrediente,
                    cantidad_requerida=item['cantidad_requerida']
                )
                db.add(menu_ingrediente)
        
        try:
            db.commit()
            db.refresh(menu)
            return menu
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Error de integridad: Ya existe un menú con el nombre '{menu.nombre}'.")
        except Exception as e:
            db.rollback()
            raise e
        
        
  
    
