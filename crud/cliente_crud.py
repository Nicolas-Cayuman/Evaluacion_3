from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Cliente


class ClienteCRUD:
    """CRUD básico que opera sobre el modelo `Cliente`."""

    def create_cliente(self, db: Session, nombre: str, email: Optional[str] = None) -> Cliente:
        """Crea un cliente validando nombre y unicidad de email."""
        nombre_limpio = nombre.strip().title()
        if not nombre_limpio:
            raise ValueError("El nombre del cliente no puede estar vacío.")

        cliente = Cliente(nombre=nombre_limpio, email=email)
        db.add(cliente)
        try:
            db.commit()
            db.refresh(cliente)
            return cliente
        except IntegrityError:
            db.rollback()
            raise ValueError("Error de integridad: Ya existe un cliente con ese email.")

    def get_cliente_by_id(self, db: Session, cliente_id: int) -> Optional[Cliente]:
        """Obtiene un cliente por ID utilizando el ORM."""
        return db.query(Cliente).get(cliente_id)

    def get_all_clientes(self, db: Session) -> List[Cliente]:
        """Lista todos los clientes ordenados alfabéticamente."""
        return db.query(Cliente).order_by(Cliente.nombre).all()

    def delete_cliente_by_id(self, db: Session, cliente_id: int) -> bool:
        """Elimina un cliente siempre que no tenga pedidos asociados."""
        cliente = self.get_cliente_by_id(db, cliente_id)
        if not cliente:
            return False

        if cliente.pedidos:
            raise Exception("No se puede eliminar un cliente con pedidos asociados.")

        db.delete(cliente)
        db.commit()
        return True

    def update_cliente(
        self,
        db: Session,
        cliente_id: int,
        nombre: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Optional[Cliente]:
        """Actualiza campos individuales del cliente."""
        cliente = self.get_cliente_by_id(db, cliente_id)
        if not cliente:
            return None

        if nombre:
            nombre_limpio = nombre.strip().title()
            if not nombre_limpio:
                raise ValueError("El nombre del cliente no puede estar vacío.")
            cliente.nombre = nombre_limpio
        if email is not None:
            cliente.email = email

        try:
            db.commit()
            db.refresh(cliente)
            return cliente
        except IntegrityError:
            db.rollback()
            raise ValueError("Error de integridad: Ya existe un cliente con ese email.")
