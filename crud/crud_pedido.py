#crud pedido
from typing import List, Optional
from django import db
from sqlalchemy.orm import Session
from models import Pedido, Menu, Cliente, DetallePedido
from crud.crud_menuingrediente import get_ingredientes_by_menu
from models import Ingrediente
from sqlalchemy.exc import IntegrityError  

class PedidoCRUD:
    # crear pedido
    def create_pedido(self, db: Session, cliente_id: Optional[int], detalles: List[dict]) -> Pedido:
        """[CREATE] Crea un nuevo pedido con sus detalles asociados."""
        total_neto = 0.0
        total_iva = 0.0
        total_final = 0.0

        pedido = Pedido(cliente_id=cliente_id)

        db.add(pedido)
        db.flush()  # Para obtener el ID del pedido antes de agregar detalles

        for item in detalles:
            menu = db.query(Menu).get(item['menu_id'])
            if not menu:
                raise ValueError(f"Menú con ID {item['menu_id']} no encontrado.")
            
            cantidad = item['cantidad']
            precio_unitario = menu.precio
            subtotal = precio_unitario * cantidad
            iva = subtotal * 0.19  # Asumiendo un IVA del 19%
            total = subtotal + iva

            detalle_pedido = DetallePedido(
                pedido_id=pedido.id,
                nombre_menu=menu.nombre,
                precio_unitario=precio_unitario,
                cantidad=cantidad
            )
            db.add(detalle_pedido)

            total_neto += subtotal
            total_iva += iva
            total_final += total

        pedido.total_neto = total_neto
        pedido.total_iva = total_iva
        pedido.total_final = total_final

        try:
            db.commit()
            db.refresh(pedido)
            return pedido
        except IntegrityError:
            db.rollback()
            raise ValueError("Error de integridad al crear el pedido.")
        except Exception as e:
            db.rollback()
            raise e
    # obtener tdoos los pedidos
    def get_all_pedidos(self, db: Session) -> List[Pedido]:
        """[READ] Obtiene todos los pedidos."""
        return db.query(Pedido).order_by(Pedido.fecha.desc()).all()
    
    # obtener pedido por id
    def get_pedido_by_id(self, db: Session, pedido_id: int) -> Optional[Pedido]:
        """[READ] Obtiene un pedido por su ID."""
        return db.query(Pedido).get(pedido_id)
    
    # eliminar pedido por id
    def delete_pedido_by_id(self, db: Session, pedido_id: int) -> bool:
        """[DELETE] Elimina un pedido por su ID."""
        pedido = db.query(Pedido).get(pedido_id)
        if not pedido:
            return False
        db.delete(pedido)
        db.commit()
        return True
    
    # actualizar pedido
    def update_pedido(self, db: Session, pedido_id: int, cliente_id: Optional[int] = None, detalles: Optional[List[dict]] = None) -> Optional[Pedido]:
        """[UPDATE] Actualiza los datos de un pedido."""
        pedido = self.get_pedido_by_id(db, pedido_id)
        if not pedido:
            return None
        
        if cliente_id is not None:
            pedido.cliente_id = cliente_id
        
        if detalles is not None:
            # Eliminar detalles existentes
            for detalle in pedido.detalles:
                db.delete(detalle)
            db.flush()

            total_neto = 0.0
            total_iva = 0.0
            total_final = 0.0

            for item in detalles:
                menu = db.query(Menu).get(item['menu_id'])
                if not menu:
                    raise ValueError(f"Menú con ID {item['menu_id']} no encontrado.")
                
                cantidad = item['cantidad']
                precio_unitario = menu.precio
                subtotal = precio_unitario * cantidad
                iva = subtotal * 0.19  # Asumiendo un IVA del 19%
                total = subtotal + iva

                detalle_pedido = DetallePedido(
                    pedido_id=pedido.id,
                    nombre_menu=menu.nombre,
                    precio_unitario=precio_unitario,
                    cantidad=cantidad
                )
                db.add(detalle_pedido)

                total_neto += subtotal
                total_iva += iva
                total_final += total

            pedido.total_neto = total_neto
            pedido.total_iva = total_iva
            pedido.total_final = total_final

        try:
            db.commit()
            db.refresh(pedido)
            return pedido
        except IntegrityError:
            db.rollback()
            raise ValueError("Error de integridad al actualizar el pedido.")
        except Exception as e:
            db.rollback()
            raise e
        