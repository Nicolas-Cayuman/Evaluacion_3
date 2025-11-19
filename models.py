"""models.py

Colección de modelos ORM declarativos usados por SQLAlchemy. Cada clase
representa una tabla y describe relaciones bidireccionales para que los
CRUDs puedan navegar entre menús, ingredientes, clientes y pedidos sin
escribir SQL manual.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from database import Base


class MenuIngrediente(Base):
    """Tabla intermedia que materializa la relación muchos-a-muchos."""

    __tablename__ = "menu_ingredientes"

    menu_id = Column(Integer, ForeignKey("menus.id"), primary_key=True)
    ingrediente_id = Column(Integer, ForeignKey("ingredientes.id"), primary_key=True)
    cantidad_requerida = Column(Float, default=0.0)

    # Relaciones ORM para navegar desde ambos extremos.
    menu = relationship("Menu", back_populates="ingredientes_asociados")
    ingrediente = relationship("Ingrediente", back_populates="menus_asociados")


class Ingrediente(Base):
    """Inventario base que se usa tanto en stock como en recetas."""

    __tablename__ = "ingredientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), unique=True, index=True, nullable=False)
    unidad = Column(String(10), default=None)
    cantidad_stock = Column(Float, default=0.0)

    menus_asociados = relationship(
        "MenuIngrediente",
        back_populates="ingrediente",
        cascade="all, delete-orphan"
    )

    def cantidad_str(self) -> str:
        """Devuelve la cantidad formateada, reutilizada por la UI/Tkinter."""
        try:
            val = float(self.cantidad_stock)
            if val.is_integer():
                return str(int(val))
            rounded = round(val, 3)
            return f"{rounded:.3f}".rstrip("0").rstrip(".")
        except Exception:
            return str(self.cantidad_stock)

    def consumir(self, db, cantidad: float):
        """Descuenta stock validando que el ORM tenga suficiente inventario."""
        if self.cantidad_stock < cantidad:
            raise ValueError(f"Stock insuficiente para {self.nombre}.")
        self.cantidad_stock -= cantidad


class Menu(Base):
    """Catálogo de menús que pueden asociarse a múltiples ingredientes."""

    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), unique=True, index=True, nullable=False)
    precio = Column(Float, default=0.0)
    icono_path = Column(String(100), default=None)

    ingredientes_asociados = relationship(
        "MenuIngrediente",
        back_populates="menu",
        cascade="all, delete-orphan",
    )


class Cliente(Base):
    """Clientes registrados que pueden firmar pedidos/boletas."""

    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)

    pedidos = relationship("Pedido", back_populates="cliente")


class Pedido(Base):
    """Cabecera de pedido que agrupa detalles e importes calculados."""

    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    total_neto = Column(Float, nullable=False)
    total_iva = Column(Float, nullable=False)
    total_final = Column(Float, nullable=False)
    fecha = Column(DateTime, default=datetime.now)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), default=None)

    cliente = relationship("Cliente", back_populates="pedidos")
    detalles = relationship(
        "DetallePedido",
        back_populates="pedido",
        cascade="all, delete-orphan",
    )


class DetallePedido(Base):
    """Detalle granular que guarda precio, IVA y total por ítem."""

    __tablename__ = "detalles_pedido"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    nombre_menu = Column(String(50), nullable=False)
    precio_unitario = Column(Float, nullable=False)
    cantidad = Column(Integer, nullable=False)
    subtotal = Column(Float, nullable=False)
    iva = Column(Float, nullable=False)
    total = Column(Float, nullable=False)

    pedido = relationship("Pedido", back_populates="detalles")
