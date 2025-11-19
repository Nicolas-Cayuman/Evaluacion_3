"""crud_detallepedido.py

Operaciones CRUD para la tabla `detalles_pedido`, incluyendo lógica de
cálculo de IVA y totales para mantener consistencia sin repetir código.
"""
from typing import Any, Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import (
    DetallePedido as DetallePedidoORM,
    Menu,
    MenuIngrediente,
    Ingrediente,
)


class DetallePedidoCRUD:
    """Gestiona los registros hijo asociados a cada pedido."""

    IVA_RATE = 0.19

    def create_detalle(self, db: Session, pedido_id: int, nombre_menu: str, cantidad: int, precio_unitario: float):
        """Inserta un detalle calculando subtotal, IVA y total automáticamente."""
        subtotal = precio_unitario * cantidad
        iva_monto = subtotal * self.IVA_RATE
        total = subtotal + iva_monto

        detalle = DetallePedidoORM(
            pedido_id=pedido_id,
            nombre_menu=nombre_menu,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            subtotal=subtotal,
            iva=iva_monto,
            total=total,
        )
        db.add(detalle)
        return detalle

    def get_detalles_by_pedido_id(self, db: Session, pedido_id: int) -> List[DetallePedidoORM]:
        """Obtiene todos los detalles vinculados a un pedido."""
        return db.query(DetallePedidoORM).filter(DetallePedidoORM.pedido_id == pedido_id).all()

    def delete_detalles_by_pedido_id(self, db: Session, pedido_id: int) -> int:
        """Elimina los detalles de un pedido y retorna cuántos registros se borraron."""
        detalles = db.query(DetallePedidoORM).filter(DetallePedidoORM.pedido_id == pedido_id).all()
        count = len(detalles)
        for detalle in detalles:
            db.delete(detalle)
        db.commit()
        return count

    def create_detalles_for_pedido(
        self,
        db: Session,
        pedido_id: int,
        detalles_data: List[Dict[str, Any]],
    ) -> List[DetallePedidoORM]:
        """Inserta múltiples detalles a partir de diccionarios provenientes de DTOs."""
        detalles_creados: List[DetallePedidoORM] = []
        for detalle_data in detalles_data:
            nombre_menu = detalle_data.get("nombre_menu") or detalle_data.get("menu_nombre")
            if not nombre_menu:
                raise ValueError("Cada detalle debe incluir 'nombre_menu'.")

            if "cantidad" not in detalle_data or "precio_unitario" not in detalle_data:
                raise ValueError("Cada detalle debe incluir 'cantidad' y 'precio_unitario'.")

            cantidad = int(detalle_data["cantidad"])
            precio_unitario = float(detalle_data["precio_unitario"])

            subtotal = detalle_data.get("subtotal")
            if subtotal is None:
                subtotal = precio_unitario * cantidad

            iva = detalle_data.get("iva")
            if iva is None:
                iva = subtotal * self.IVA_RATE

            total = detalle_data.get("total")
            if total is None:
                total = subtotal + iva

            detalle = DetallePedidoORM(
                pedido_id=pedido_id,
                nombre_menu=nombre_menu,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=subtotal,
                iva=iva,
                total=total,
            )
            db.add(detalle)
            detalles_creados.append(detalle)

        db.commit()
        for detalle in detalles_creados:
            db.refresh(detalle)
        return detalles_creados

    def update_detalle_by_id(self, db: Session, detalle_id: int, cantidad: int) -> DetallePedidoORM:
        """Actualiza la cantidad de un detalle específico."""
        detalle = db.query(DetallePedidoORM).get(detalle_id)
        if not detalle:
            raise ValueError("Detalle de pedido no encontrado.")
        detalle.cantidad = cantidad
        db.commit()
        db.refresh(detalle)
        return detalle

    def get_detalle_by_id(self, db: Session, detalle_id: int) -> DetallePedidoORM:
        """Recupera un detalle mediante su clave primaria."""
        return db.query(DetallePedidoORM).get(detalle_id)

    def delete_detalle_by_id(self, db: Session, detalle_id: int) -> bool:
        """Elimina un detalle individual."""
        detalle = db.query(DetallePedidoORM).get(detalle_id)
        if not detalle:
            return False
        db.delete(detalle)
        db.commit()
        return True

    def get_totales_por_menu(self, db: Session) -> List[tuple]:
        """Agrega la cantidad vendida por menú para alimentar los gráficos."""
        return (
            db.query(
                DetallePedidoORM.nombre_menu.label("menu"),
                func.sum(DetallePedidoORM.cantidad).label("total"),
            )
            .group_by(DetallePedidoORM.nombre_menu)
            .order_by(func.sum(DetallePedidoORM.cantidad).desc())
            .all()
        )

    def get_consumo_ingredientes(self, db: Session) -> List[tuple]:
        """
        Calcula el uso total de cada ingrediente basándose en recetas y cantidades vendidas.
        Esto permite mostrar el gráfico 'Uso de ingredientes' exigido por la pauta.
        """
        consumo_total = (
            db.query(
                Ingrediente.nombre.label("ingrediente"),
                func.sum(DetallePedidoORM.cantidad * MenuIngrediente.cantidad_requerida).label("total"),
            )
            .join(Menu, Menu.nombre == DetallePedidoORM.nombre_menu)
            .join(MenuIngrediente, MenuIngrediente.menu_id == Menu.id)
            .join(Ingrediente, Ingrediente.id == MenuIngrediente.ingrediente_id)
            .group_by(Ingrediente.nombre)
            .order_by(func.sum(DetallePedidoORM.cantidad * MenuIngrediente.cantidad_requerida).desc())
            .all()
        )
        return consumo_total
