"""populate_db.py

Script idempotente que llena la base de datos con ingredientes, menús,
clientes y pedidos de ejemplo. Útil para demos de la interfaz y pruebas
de los CRUDs basados en SQLAlchemy.
"""
import random
from datetime import datetime

from database import SessionLocal, create_db_and_tables
from models import Cliente, DetallePedido, Ingrediente, Menu, MenuIngrediente, Pedido


def asegurarse_ingrediente(db, nombre, unidad, cantidad):
    existente = db.query(Ingrediente).filter(Ingrediente.nombre == nombre).first()
    if existente:
        return existente
    ingrediente = Ingrediente(nombre=nombre, unidad=unidad, cantidad_stock=cantidad)
    db.add(ingrediente)
    db.commit()
    db.refresh(ingrediente)
    return ingrediente


def asegurarse_menu(db, nombre, precio, icono_path):
    existente = db.query(Menu).filter(Menu.nombre == nombre).first()
    if existente:
        existente.precio = precio
        existente.icono_path = icono_path
        db.commit()
        return existente
    menu = Menu(nombre=nombre, precio=precio, icono_path=icono_path)
    db.add(menu)
    db.commit()
    db.refresh(menu)
    return menu


def asegurarse_cliente(db, nombre, email):
    existente = db.query(Cliente).filter(Cliente.email == email).first()
    if existente:
        existente.nombre = nombre
        db.commit()
        return existente
    cliente = Cliente(nombre=nombre, email=email)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente

def poblar_datos():
    """Inserta datos mínimos sin borrar lo que ya existe."""
    create_db_and_tables()
    db = SessionLocal()

    try:
        ingredientes = {
            "Vienesa": asegurarse_ingrediente(db, "Vienesa", "unid", 100),
            "Pan de completo": asegurarse_ingrediente(db, "Pan de completo", "unid", 100),
            "Palta": asegurarse_ingrediente(db, "Palta", "kg", 5.0),
            "Tomate": asegurarse_ingrediente(db, "Tomate", "kg", 10.0),
            "Pepsi": asegurarse_ingrediente(db, "Pepsi", "unid", 50),
            "Papas": asegurarse_ingrediente(db, "Papas", "kg", 50.0),
            "Carne de vacuno": asegurarse_ingrediente(db, "Carne de vacuno", "kg", 10.0),
            "Huevos": asegurarse_ingrediente(db, "Huevos", "unid", 60),
            "Cebolla": asegurarse_ingrediente(db, "Cebolla", "kg", 5.0),
            "coca cola": asegurarse_ingrediente(db, "coca cola", "unid", 50),
            "Pan de hamburguesa": asegurarse_ingrediente(db, "Pan de hamburguesa", "unid", 50),
            "Lamina de queso": asegurarse_ingrediente(db, "Lamina de queso", "unid", 100),
            "Churrasco de carne": asegurarse_ingrediente(db, "Churrasco de carne", "unid", 50),
            "masa de empanada": asegurarse_ingrediente(db, "masa de empanada", "unid", 100),
            "queso": asegurarse_ingrediente(db, "queso", "unid", 100),
        }

        menus = {
            "Completo": asegurarse_menu(db, "Completo", 1800, "IMG/icono_hotdog_sin_texto_64x64.png"),
            "Bepis": asegurarse_menu(db, "Bepis", 1200, "IMG/icono_cola_64x64.png"),
            "Chorrillana": asegurarse_menu(db, "Chorrillana", 6500, "IMG/icono_chorrillana_64x64.png"),
            "Papas fritas": asegurarse_menu(db, "Papas fritas", 500, "IMG/icono_papas_fritas_64x64.png"),
            "Coca-cola": asegurarse_menu(db, "Coca-cola", 1200, "IMG/icono_cola_lata_64x64.png"),
            "Hamburguesa": asegurarse_menu(db, "Hamburguesa", 3500, "IMG/icono_hamburguesa_negra_64x64.png"),
            "empanada de queso": asegurarse_menu(db, "empanada de queso", 800, "IMG/icono_empanada_queso_64x64.png"),
        }

        for menu_nombre, definicion in [
            ("Completo", [("Vienesa", 1), ("Pan de completo", 1), ("Palta", 0.5), ("Tomate", 0.2)]),
            ("Bepis", [("Pepsi", 1)]),
            ("Chorrillana", [("Papas", 0.2), ("Carne de vacuno", 0.1), ("Huevos", 2), ("Cebolla", 0.05)]),
            ("Papas fritas", [("Papas", 0.3)]),
            ("Coca-cola", [("coca cola", 1)]),
            ("Hamburguesa", [("Pan de hamburguesa", 1), ("Lamina de queso", 1), ("Churrasco de carne", 1)]),
            ("empanada de queso", [("masa de empanada", 1), ("queso", 1)]),
        ]:
            menu = menus[menu_nombre]
            existentes = {assoc.ingrediente.nombre: assoc for assoc in menu.ingredientes_asociados}
            for nombre_ing, cantidad in definicion:
                if nombre_ing in existentes:
                    existentes[nombre_ing].cantidad_requerida = cantidad
                else:
                    db.add(MenuIngrediente(
                        menu_id=menu.id,
                        ingrediente_id=ingredientes[nombre_ing].id,
                        cantidad_requerida=cantidad,
                    ))
            db.commit()

        clientes = [
            asegurarse_cliente(db, "Leoncio Prado Gutierrez", "Quienfueelcoronel@gmail.com"),
            asegurarse_cliente(db, "Patricio Carlos", "Patocarlo298374@gmail.com"),
            asegurarse_cliente(db, "María Juana", "mariiiiiiihxD@gmail.com"),
            asegurarse_cliente(db, "Pedro Picapiedras", "Pedri777@gmail.com"),
            asegurarse_cliente(db, "Laura Larza", "lalarzazaUwU@gmail.com"),
        ]

        lista_clientes = db.query(Cliente).all()
        lista_menus = db.query(Menu).all()

        for i in range(5):
            cliente = lista_clientes[i % len(lista_clientes)]
            menu = random.choice(lista_menus)
            cantidad = random.randint(1, 3)

            total_neto = menu.precio * cantidad
            total_iva = round(total_neto * 0.19, 2)
            total_final = round(total_neto + total_iva, 2)

            pedido = Pedido(
                cliente_id=cliente.id,
                total_neto=total_neto,
                total_iva=total_iva,
                total_final=total_final,
                fecha=datetime.now(),
            )
            db.add(pedido)
            db.commit()

            detalle_subtotal = menu.precio * cantidad
            detalle_iva = round(detalle_subtotal * 0.19, 2)
            detalle_total = round(detalle_subtotal + detalle_iva, 2)

            detalle = DetallePedido(
                pedido_id=pedido.id,
                nombre_menu=menu.nombre,
                precio_unitario=menu.precio,
                cantidad=cantidad,
                subtotal=detalle_subtotal,
                iva=detalle_iva,
                total=detalle_total,
            )
            db.add(detalle)

        db.commit()
        print("Se insertaron todos los registros de 'Menu_catalog.py' correctamente.")

    except Exception as e:
        db.rollback()
        print(f"Error al poblar la base de datos: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    poblar_datos()
