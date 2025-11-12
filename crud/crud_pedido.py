#crud pedido
from sqlalchemy.orm import Session
from models import Pedido
from schemas import PedidoCreate, PedidoUpdate
from typing import List, Optional

# Crear un nuevo pedido
def create_pedido(db: Session, pedido: PedidoCreate) -> Pedido:
    db_pedido = Pedido(**pedido.dict())
    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)
    return db_pedido
# Obtener un pedido por su ID
def get_pedido(db: Session, pedido_id: int) -> Optional[Pedido]:
    return db.query(Pedido).filter(Pedido.id == pedido_id).first()

# Obtener todos los pedidos
def get_pedidos(db: Session, skip: int = 0, limit: int = 100) -> List[Pedido]:
    return db.query(Pedido).offset(skip).limit(limit).all()

# Actualizar un pedido existente
def update_pedido(db: Session, pedido_id: int, pedido_update: PedidoUpdate) -> Optional[Pedido]:
    db_pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if db_pedido:
        for key, value in pedido_update.dict(exclude_unset=True).items():
            setattr(db_pedido, key, value)
        db.commit()
        db.refresh(db_pedido)
    return db_pedido

# Eliminar un pedido por su ID
def delete_pedido(db: Session, pedido_id: int) -> Optional[Pedido]:
    db_pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if db_pedido:
        db.delete(db_pedido)
        db.commit()
    return db_pedido
        