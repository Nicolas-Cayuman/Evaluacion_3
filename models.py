from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, create_engine, func
)
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# ingrediente en un menú (tabla intermedia) 
class MenuIngrediente(Base):
    __tablename__ = "menu_ingredientes"

    menu_id = Column(Integer, ForeignKey("menus.id"), primary_key=True)
    ingrediente_id = Column(Integer, ForeignKey("ingredientes.id"), primary_key=True)
    
    cantidad_requerida = Column(Float, default=0.0)

    # Relaciones bidireccionales
    menu = relationship("Menu", back_populates="ingredientes_asociados")
    ingrediente = relationship("Ingrediente", back_populates="menus_asociados")

# ingrediente
class Ingrediente(Base):
    __tablename__ = "ingredientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), unique=True, index=True, nullable=False)
    unidad = Column(String(10), default=None)
    cantidad_stock = Column(Float, default=0.0)

    menus_asociados = relationship("MenuIngrediente", back_populates="ingrediente")
    # Métodos cantidad como string
    def cantidad_str(self) -> str:
        try:
            val = float(self.cantidad_stock)
            if val.is_integer():
                return str(int(val))
            rounded = round(val, 3)
            return f"{rounded:.3f}".rstrip('0').rstrip('.')
        except Exception:
            return str(self.cantidad_stock)
    # Método para consumir stock
    def consumir(self, db, cantidad):
        if self.cantidad_stock < cantidad:
            raise ValueError(f"Stock insuficiente para {self.nombre}.")
        self.cantidad_stock -= cantidad
       

# --- MODELO DE MENU ---
class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), unique=True, index=True, nullable=False)
    precio = Column(Float, default=0.0)
    icono_path = Column(String(100), default=None)

    ingredientes_asociados = relationship("MenuIngrediente", back_populates="menu", cascade="all, delete-orphan")

# --- CLIENTE ---
class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    
    pedidos = relationship("Pedido", back_populates="cliente")

# --- PEDIDO ---
class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Campos SIN default
    total_neto = Column(Float, nullable=False)
    total_iva = Column(Float, nullable=False)
    total_final = Column(Float, nullable=False)

    # Campos CON default
    fecha = Column(DateTime, default=datetime.now)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), default=None)

    # Relaciones
    cliente = relationship("Cliente", back_populates="pedidos")
    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")

# --- DETALLE DEL PEDIDO ---
class DetallePedido(Base):
    __tablename__ = "detalles_pedido"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    nombre_menu = Column(String(50), nullable=False)
    precio_unitario = Column(Float, nullable=False)
    cantidad = Column(Integer, nullable=False)
    
    pedido = relationship("Pedido", back_populates="detalles")
