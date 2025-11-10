# Ingrediente.py
from dataclasses import dataclass
from typing import Optional

@dataclass(eq=True, frozen=False)
class Ingrediente:
    nombre: str
    unidad: Optional[str]  
    cantidad: float          

    def __post_init__(self):
        self.cantidad = float(self.cantidad)

    def __str__(self):
        if self.unidad:
            return f"{self.nombre} ({self.unidad}) x {self.cantidad}"
        return f"{self.nombre} x {self.cantidad}"

    def cantidad_str(self) -> str:
        """Devuelve la cantidad como string sin el '.0' innecesario.

        Ejemplos:
        5.0 -> '5'
        5.5 -> '5.5'
        """
        try:
            val = float(self.cantidad)
            if val.is_integer():
                return str(int(val))

            rounded = round(val, 3)
            s = f"{rounded:.3f}".rstrip('0').rstrip('.')
            return s
        
        except Exception:
            return str(self.cantidad)