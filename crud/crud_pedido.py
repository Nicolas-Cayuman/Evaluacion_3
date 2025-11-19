"""crud_pedido.py

Lógica de acceso al ORM para la tabla `pedidos`, incluyendo utilidades
para convertir DTOs provenientes de la UI y generar agregaciones.
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from crud.crud_detallepedido import DetallePedidoCRUD
from models import Cliente, Pedido


class PedidoCRUD:
    """CRUD de pedidos que trabaja codo a codo con DetallePedidoCRUD."""

    def create_pedido_from_dto(self, db: Session, pedido_dto, cliente_id: int):
        """Convierte un DTO en registros ORM y crea sus detalles relacionados."""
        detalle_crud = DetallePedidoCRUD()

        total_final = pedido_dto.calcular_total()
        iva_rate = 0.19
        total_neto = total_final / (1 + iva_rate)
        total_iva = total_final - total_neto

        nuevo_pedido_orm = Pedido(
            cliente_id=cliente_id,
            total_neto=total_neto,
            total_iva=total_iva,
            total_final=total_final,
        )

        db.add(nuevo_pedido_orm)
        db.flush()

        for item_menu in pedido_dto.menus:
            detalle_crud.create_detalle(
                db=db,
                pedido_id=nuevo_pedido_orm.id,
                nombre_menu=item_menu.nombre,
                cantidad=item_menu.cantidad,
                precio_unitario=item_menu.precio,
            )

        db.commit()
        return nuevo_pedido_orm

    def create_pedido(self, db: Session, data: Dict[str, Any]) -> Pedido:
        """Permite crear pedidos genéricos a partir de diccionarios."""
        db_pedido = Pedido(**data)
        db.add(db_pedido)
        db.commit()
        db.refresh(db_pedido)
        return db_pedido

    def get_pedido(self, db: Session, pedido_id: int) -> Optional[Pedido]:
        """Recupera un pedido por su clave primaria."""
        return db.query(Pedido).filter(Pedido.id == pedido_id).first()

    def get_pedidos(self, db: Session, skip: int = 0, limit: int = 100) -> List[Pedido]:
        """Pagina pedidos completos."""
        return db.query(Pedido).offset(skip).limit(limit).all()

    def update_pedido(self, db: Session, pedido_id: int, data: Dict[str, Any]) -> Optional[Pedido]:
        """Actualiza campos básicos del pedido."""
        db_pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
        if db_pedido:
            for key, value in data.items():
                if key == "id":
                    continue
                setattr(db_pedido, key, value)
            db.commit()
            db.refresh(db_pedido)
        return db_pedido

    def delete_pedido(self, db: Session, pedido_id: int) -> Optional[Pedido]:
        """Elimina un pedido y, por cascada, sus detalles."""
        db_pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
        if db_pedido:
            db.delete(db_pedido)
            db.commit()
        return db_pedido

    def get_pedidos_con_cliente(self, db: Session):
        """Devuelve pedidos junto al nombre del cliente usando JOIN externo."""
        return (
            db.query(Pedido, Cliente.nombre)
            .join(Cliente, Pedido.cliente_id == Cliente.id, isouter=True)
            .order_by(Pedido.fecha.desc())
            .all()
        )

    def get_totales_por_cliente(self, db: Session) -> List[tuple]:
        """Agrupa las ventas por cliente para alimentar el gráfico de la UI."""
        cliente_nombre = func.coalesce(Cliente.nombre, "Sin Cliente")
        total_sum = func.sum(Pedido.total_final).label("total")
        resultados = (
            db.query(cliente_nombre.label("cliente"), total_sum)
            .join(Cliente, Pedido.cliente_id == Cliente.id, isouter=True)
            .group_by(cliente_nombre)
            .order_by(total_sum.desc())
            .all()
        )
        return resultados

    def get_totales_por_fecha(self, db: Session, periodo: str = "day", limit: int = 12) -> List[tuple]:
        """
        Agrega ventas por fecha. `periodo` puede ser 'day', 'month' o 'year'.
        Retorna lista de tuplas (periodo, total).
        """
        formatos = {
            "day": "%Y-%m-%d",
            "week": "%Y-W%W",
            "month": "%Y-%m",
            "year": "%Y",
        }
        pattern = formatos.get(periodo, "%Y-%m-%d")
        periodo_label = func.strftime(pattern, Pedido.fecha).label("periodo")
        query = (
            db.query(periodo_label, func.sum(Pedido.total_final).label("total"))
            .group_by(periodo_label)
            .order_by(periodo_label.desc())
        )
        if limit:
            query = query.limit(limit)
        resultados = query.all()
        return list(reversed(resultados))
