"""Ingrediente.py

Dataclass ligero utilizado en la capa de presentación (stock CSV y DTOs).
No es un modelo ORM sino un contenedor mutable que se puede serializar a
CSV y mostrar en la interfaz antes de persistirlo mediante SQLAlchemy.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(eq=True, frozen=False)
class Ingrediente:
    """Representa un ingrediente con nombre, unidad y cantidad."""

    nombre: str
    unidad: Optional[str]
    cantidad: float

    def __post_init__(self):
        """Asegura que la cantidad siempre se maneje como float."""
        self.cantidad = float(self.cantidad)

    def __str__(self):
        """Devuelve una representación legible usada en tablas/logs."""
        if self.unidad:
            return f"{self.nombre} ({self.unidad}) x {self.cantidad}"
        return f"{self.nombre} x {self.cantidad}"

    def cantidad_str(self) -> str:
        """Formatea la cantidad sin ceros innecesarios para CSV/UI."""
        try:
            val = float(self.cantidad)
            if val.is_integer():
                return str(int(val))

            rounded = round(val, 3)
            return f"{rounded:.3f}".rstrip("0").rstrip(".")
        except Exception:
            return str(self.cantidad)
