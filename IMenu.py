"""IMenu.py

Protocolo estructural que describe los atributos mínimos que debe tener
un menú dentro de la aplicación. Facilita el tipado y permite desacoplar
los DTOs (`CrearMenu`) de los modelos ORM reales.
"""
from typing import Protocol, List, Optional

from Ingrediente import Ingrediente


class IMenu(Protocol):
    """Contrato básico para cualquier objeto que represente un menú."""

    nombre: str
    ingredientes: List[Ingrediente]
    precio: float
    icono_path: Optional[str]
    cantidad: int
