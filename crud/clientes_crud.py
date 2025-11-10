# crud de clientes

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import Cliente
from typing import List, Optional

class ClienteCRUD:
    # crear cliente
    def create_cliente(self, db: Session, nombre: str, correo: Optional[str] = None) -> Cliente:
        """[CREATE] Crea un nuevo cliente."""
        nombre_limpio = nombre.strip().title()
        if not nombre_limpio:
            raise ValueError("El nombre del cliente no puede estar vacío.")
        
        cliente = Cliente(nombre=nombre_limpio, correo=correo)
        db.add(cliente)
        try:
            db.commit()
            db.refresh(cliente)
            return cliente
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Error de integridad: Ya existe un cliente con el nombre '{nombre_limpio}'.")
        except Exception as e:
            db.rollback()
            raise e
    
    # obtener cliente por id
    def get_cliente_by_id(self, db: Session, cliente_id: int) -> Optional[Cliente]:
        """[READ] Obtiene un cliente por su ID."""
        return db.query(Cliente).get(cliente_id)
    
    # obtener todos los clientes
    def get_all_clientes(self, db: Session) -> List[Cliente]:
        """[READ] Obtiene todos los clientes."""
        return db.query(Cliente).order_by(Cliente.nombre).all()
    
    # eliminar cliente por id
    def delete_cliente_by_id(self, db: Session, cliente_id: int) -> bool:
        """[DELETE] Elimina un cliente por su ID."""
        cliente = self.get_cliente_by_id(db, cliente_id)
        if not cliente:
            return False
        db.delete(cliente)
        db.commit()
        return True
    
    # actualizar cliente
    def update_cliente(self, db: Session, cliente_id: int, nombre: Optional[str] = None, correo: Optional[str] = None) -> Optional[Cliente]:
        """[UPDATE] Actualiza los datos de un cliente."""
        cliente = self.get_cliente_by_id(db, cliente_id)
        if not cliente:
            return None
        
        if nombre:
            nombre_limpio = nombre.strip().title()
            if not nombre_limpio:
                raise ValueError("El nombre del cliente no puede estar vacío.")
            cliente.nombre = nombre_limpio
        if correo is not None:
            cliente.correo = correo
        
        try:
            db.commit()
            db.refresh(cliente)
            return cliente
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Error de integridad: Ya existe un cliente con el nombre '{cliente.nombre}'.")
        except Exception as e:
            db.rollback()
            raise e
    
cliente_crud = ClienteCRUD()
