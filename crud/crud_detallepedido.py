#detallepedido
from sqlalchemy.orm import Session
from models import DetallePedido
from typing import List

class DetallePedidoCRUD:
    # obtener detalles por pedido id
    def get_detalles_by_pedido_id(self, db: Session, pedido_id: int) -> List[DetallePedido]:
        """[READ] Obtiene todos los detalles de un pedido por su ID."""
        return db.query(DetallePedido).filter(DetallePedido.pedido_id == pedido_id).all()
    
    # eliminar detalles por pedido id
    def delete_detalles_by_pedido_id(self, db: Session, pedido_id: int) -> int:
        """[DELETE] Elimina todos los detalles de un pedido por su ID. Retorna el número de detalles eliminados."""
        detalles = db.query(DetallePedido).filter(DetallePedido.pedido_id == pedido_id).all()
        count = len(detalles)
        for detalle in detalles:
            db.delete(detalle)
        db.commit()
        return count
    
    # crear detalles para un pedido
    def create_detalles_for_pedido(self, db: Session, pedido_id: int, detalles_data: List[dict]) -> List[DetallePedido]:
        """[CREATE] Crea detalles para un pedido dado su ID y una lista de datos de detalles."""
        detalles_creados = []
        for detalle_data in detalles_data:
            detalle = DetallePedido(
                pedido_id=pedido_id,
                menu_id=detalle_data['menu_id'],
                cantidad=detalle_data['cantidad'],
                precio_unitario=detalle_data['precio_unitario'],
                subtotal=detalle_data['subtotal'],
                iva=detalle_data['iva'],
                total=detalle_data['total']
            )
            db.add(detalle)
            detalles_creados.append(detalle)
        db.commit()
        for detalle in detalles_creados:
            db.refresh(detalle)
        return detalles_creados
    
    # actualizar detalle por id
    
    def update_detalle_by_id(self, db: Session, detalle_id: int, cantidad: int) -> DetallePedido:
        """[UPDATE] Actualiza la cantidad de un detalle de pedido por su ID."""
        detalle = db.query(DetallePedido).get(detalle_id)
        if not detalle:
            raise ValueError("Detalle de pedido no encontrado.")
        detalle.cantidad = cantidad
        db.commit()
        db.refresh(detalle)
        return detalle
    
    # obtener detalle por id
    def get_detalle_by_id(self, db: Session, detalle_id: int) -> DetallePedido:
        """[READ] Obtiene un detalle de pedido por su ID."""
        return db.query(DetallePedido).get(detalle_id)
    
    # eliminar detalle por id
    def delete_detalle_by_id(self, db: Session, detalle_id: int) -> bool:
        """[DELETE] Elimina un detalle de pedido por su ID."""
        detalle = db.query(DetallePedido).get(detalle_id)
        if not detalle:
            return False
        db.delete(detalle)
        db.commit()
        return True
        