"""Pedido.py

DTO mutable que representa el pedido en construcción desde la interfaz.
Se mantiene separado de los modelos ORM para controlar la lógica antes
de persistir los datos mediante `PedidoCRUD`.
"""
from ElementoMenu import CrearMenu


class Pedido:
    """Agrupa menús seleccionados y ofrece helpers de agregación."""

    def __init__(self):
        self.menus = []

    def agregar_menu(self, menu: CrearMenu):
        """Agrega un menú o incrementa su cantidad si ya existe."""
        for m in self.menus:
            if m.nombre == menu.nombre:
                m.cantidad = int(m.cantidad) + 1
                return True

        id_de_menu_orm = getattr(menu, "id_orm", None)

        try:
            nueva = CrearMenu(
                menu.nombre,
                list(menu.ingredientes),
                precio=menu.precio,
                icono_path=getattr(menu, "icono_path", None),
                cantidad=1,
                id_orm=id_de_menu_orm,
            )
        except Exception:
            nueva = CrearMenu(
                menu.nombre,
                menu.ingredientes,
                precio=getattr(menu, "precio", 0.0),
                icono_path=getattr(menu, "icono_path", None),
                cantidad=1,
                id_orm=id_de_menu_orm,
            )

        self.menus.append(nueva)
        return True

    def eliminar_menu(self, nombre_menu: str):
        """Disminuye la cantidad o elimina un menú del pedido."""
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
        """Retorna una lista de tuplas apta para poblar Treeviews."""
        return [(m.nombre, m.cantidad, m.precio) for m in self.menus]

    def calcular_total(self) -> float:
        """Calcula el total bruto del pedido (sin IVA adicional)."""
        total = 0.0
        for m in self.menus:
            try:
                total += float(m.precio) * int(m.cantidad)
            except Exception:
                pass
        return float(total)
