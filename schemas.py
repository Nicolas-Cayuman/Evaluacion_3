from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- INGREDIENTE ---
class IngredienteBase(BaseModel):
    nombre: str
    unidad: Optional[str] = None
    cantidad_stock: float

class IngredienteCreate(IngredienteBase):
    pass

class Ingrediente(IngredienteBase):
    id: int
    class Config:
        orm_mode = True


# --- MENU ---
class MenuBase(BaseModel):
    nombre: str
    precio: float
    icono_path: Optional[str] = None

class MenuCreate(MenuBase):
    pass

class Menu(MenuBase):
    id: int
    class Config:
        orm_mode = True


# --- CLIENTE ---
class ClienteBase(BaseModel):
    nombre: str
    email: str

class ClienteCreate(ClienteBase):
    pass

class Cliente(ClienteBase):
    id: int
    class Config:
        orm_mode = True


# --- DETALLE PEDIDO ---
class DetallePedidoBase(BaseModel):
    nombre_menu: str
    precio_unitario: float
    cantidad: int

class DetallePedidoCreate(DetallePedidoBase):
    pass

class DetallePedido(DetallePedidoBase):
    id: int
    class Config:
        orm_mode = True


# --- PEDIDO ---
class PedidoBase(BaseModel):
    total_neto: float
    total_iva: float
    total_final: float
    cliente_id: Optional[int] = None

class PedidoCreate(PedidoBase):
    detalles: List[DetallePedidoCreate] = []  # si quieres incluir los menús dentro del pedido

class Pedido(PedidoBase):
    id: int
    fecha: datetime
    cliente: Optional[Cliente] = None
    detalles: List[DetallePedido] = []
    class Config:
        orm_mode = True
