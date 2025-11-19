"""ElementoMenu.py

Define el DTO `CrearMenu` que se usa en la capa de presentación para
interactuar con los menús provenientes del ORM. Al separar este objeto
de los modelos SQLAlchemy evitamos pasar instancias pesadas a la UI.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from Ingrediente import Ingrediente
from IMenu import IMenu


@dataclass
class CrearMenu(IMenu):
    """DTO simple que representa un menú disponible para venta."""

    nombre: str
    ingredientes: List[Ingrediente]
    precio: float = 0.0
    icono_path: Optional[str] = None
    cantidad: int = field(default=0, compare=False)
    # `id_orm` permite saber qué registro SQLAlchemy originó este DTO.
    id_orm: Optional[int] = field(default=None, compare=False)
