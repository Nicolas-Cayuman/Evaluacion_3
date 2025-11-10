from ElementoMenu import CrearMenu
from dataclasses import replace


class Pedido:
    def __init__(self):
        self.menus = []

    def agregar_menu(self, menu: CrearMenu):
        """Agrega un menú al pedido. Si ya existe, incrementa su cantidad."""
        for m in self.menus:
            if m.nombre == menu.nombre:
                m.cantidad = int(m.cantidad) + 1
                return True

        try:
            nueva = CrearMenu(menu.nombre, list(menu.ingredientes), precio=menu.precio, icono_path=getattr(menu, 'icono_path', None), cantidad=1)
        except Exception:
            nueva = CrearMenu(menu.nombre, menu.ingredientes, precio=getattr(menu, 'precio', 0.0), icono_path=getattr(menu, 'icono_path', None), cantidad=1)
        self.menus.append(nueva)
        return True

    def eliminar_menu(self, nombre_menu: str):
        """Disminuye la cantidad de un menú o lo elimina si la cantidad llega a 0."""
        for m in list(self.menus):
            if m.nombre == nombre_menu:
                try:
                    if int(m.cantidad) > 1:
                        m.cantidad = int(m.cantidad) - 1
                    else:
                        self.menus.remove(m)
                    return True
                except Exception:
                    
                    self.menus.remove(m)
                    return True
        return False

    def mostrar_pedido(self):
        """Retorna una lista de tuplas (nombre, cantidad, precio_unitario)."""
        return [(m.nombre, m.cantidad, m.precio) for m in self.menus]

    def calcular_total(self) -> float:
        total = 0.0
        for m in self.menus:
            try:
                total += float(m.precio) * int(m.cantidad)
            except Exception:
                pass
        return float(total)
