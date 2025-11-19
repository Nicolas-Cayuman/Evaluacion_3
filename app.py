"""app.py

Aplicación de escritorio basada en Tkinter/CustomTkinter que orquesta
la gestión de inventario, clientes y ventas del restaurante. Toda la
persistencia se realiza mediante SQLAlchemy (ORM) contra SQLite y se
apoya en CRUDs especializados para mantener el código desacoplado.
También se incluyen transformaciones funcionales (lambda/filter/map/
reduce) y generación de PDFs y gráficos a partir de los datos.
"""

# --- Imports Base ---
# ... (imports de ctk, ttk, PIL, etc.) ...
from ElementoMenu import CrearMenu
import customtkinter as ctk
from tkinter import ttk, Toplevel, Label, messagebox
import re
from PIL import Image
from CTkMessagebox import CTkMessagebox
from Pedido import Pedido
from BoletaFacade import BoletaFacade
import pandas as pd
from tkinter import filedialog
from menu_pdf import create_menu_pdf
from ctk_pdf_viewer import CTkPDFViewer
import os
from tkinter.font import nametofont
from functools import reduce 
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from graficos import render_bar_chart, resolver_dataset
# --- Imports de Base de Datos y CRUDs ---
from database import SessionLocal, create_db_and_tables
from models import Menu, Cliente 
from crud.ingrediente_crud import IngredienteCRUD
from crud.menu_crud import MenuCRUD
from crud.cliente_crud import ClienteCRUD
from crud.crud_pedido import PedidoCRUD 
from crud.crud_detallepedido import DetallePedidoCRUD 
from populate_db import poblar_datos
from Ingrediente import Ingrediente as IngredienteDTO
 

class AplicacionConPestanas(ctk.CTk):
    """Ventana principal que conecta la UI con los CRUDs del ORM."""
    
    def __init__(self):
        """Configura fuentes, pestañas y servicios ORM compartidos."""
        super().__init__()
        
        self.title("Gestión de Restaurante - ORM (SQLAlchemy 1.x)")
        self.geometry("950x750")
        nametofont("TkHeadingFont").configure(size=14)
        nametofont("TkDefaultFont").configure(size=11)

        create_db_and_tables() 
        poblar_datos() 
        
        self.db_session = SessionLocal() 
        
        self.ingrediente_crud = IngredienteCRUD()
        self.menu_crud = MenuCRUD()
        self.cliente_crud = ClienteCRUD()
        self.pedido_crud = PedidoCRUD()
        self.detalle_pedido_crud = DetallePedidoCRUD()
        
        self.pedido = Pedido() 
        self.menus = self.menu_crud.get_all_menus(self.db_session)
        self.menu_temp_ingredientes = []  # Receta temporal para nuevos menús
        self.menu_en_edicion = None       # ID del menú en modo edición
        self.tipo_grafico_var = ctk.StringVar(value="Ventas por Cliente")
        self.periodo_fecha_var = ctk.StringVar(value="Diario")
        self._mapa_ingredientes_combobox = {}
        self.figure_ventas = None
        self.canvas_ventas = None

        self.tabview = ctk.CTkTabview(self,command=self.on_tab_change)
        self.tabview.pack(expand=True, fill="both", padx=10, pady=10)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.crear_pestanas()
        self._boleta_mostrable = False

    def on_tab_change(self):
        """Refresca el contenido según la pestaña actual para mantener los datos ORM sincronizados."""
        selected_tab = self.tabview.get()
        if selected_tab == "Stock":
            self.actualizar_treeview()
        if selected_tab == "Pedido":
            self.actualizar_treeview()
            # --- CAMBIO 1 ---
            # self.generar_menus() # ELIMINADO: Ya no se genera automáticamente
            self.actualizar_combobox_clientes() 
        if selected_tab == "Gestión de Clientes":
            self.actualizar_treeview_clientes()
        if selected_tab == "Gestión de Pedidos":
            self.actualizar_treeview_gestion_pedidos()
        if selected_tab == "Gestión de Menús":
            self.actualizar_treeview_menus()
            self.actualizar_combobox_ingredientes_menu()
        if selected_tab == "Grafico de Ventas":
            self.actualizar_grafico_ventas()

    def crear_pestanas(self):
        """Instancia todas las CTkTabview tabs y delega el layout a helpers."""
        self.tab3 = self.tabview.add("Carga CSV")  
        self.tab1 = self.tabview.add("Stock")
        self.tab4 = self.tabview.add("Carta restorante")  
        self.tab2 = self.tabview.add("Pedido")
        self.tab5 = self.tabview.add("Boleta")
        self.tab_clientes = self.tabview.add("Gestión de Clientes")
        self.tab_gestion_pedidos = self.tabview.add("Gestión de Pedidos")
        self.tab_grafico_ventas = self.tabview.add("Grafico de Ventas")
        self.tab_gestion_menus = self.tabview.add("Gestión de Menús")  # Nueva pestaña CRUD de menús
        
        self.configurar_pestana1()
        self.configurar_pestana2()
        self.configurar_pestana3()
        self._configurar_pestana_crear_menu()
        self._configurar_pestana_ver_boleta()
        self.configurar_pestana_clientes()
        self.configurar_pestana_gestion_pedidos()
        self.configurar_pestana_gestion_menus()
        self.configurar_pestana_grafico_ventas()

    # ----------------------------------------------------
    # PESTAÑA 1: STOCK (Conectada a CRUD)
    # ----------------------------------------------------

    def configurar_pestana1(self):
        """Construye la vista de stock enlazada a IngredienteCRUD (ORM)."""
        frame_formulario = ctk.CTkFrame(self.tab1)
        frame_formulario.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        frame_treeview = ctk.CTkFrame(self.tab1)
        frame_treeview.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        label_nombre = ctk.CTkLabel(frame_formulario, text="Nombre del Ingrediente:")
        label_nombre.pack(pady=5)
        self.entry_nombre = ctk.CTkEntry(frame_formulario)
        self.entry_nombre.pack(pady=5)
        label_cantidad = ctk.CTkLabel(frame_formulario, text="Unidad:")
        label_cantidad.pack(pady=5)
        self.combo_unidad = ctk.CTkComboBox(frame_formulario, values=["kg", "unid", "L"])
        self.combo_unidad.pack(pady=5)
        label_cantidad = ctk.CTkLabel(frame_formulario, text="Cantidad:")
        label_cantidad.pack(pady=5)
        self.entry_cantidad = ctk.CTkEntry(frame_formulario)
        self.entry_cantidad.pack(pady=5)
        self.boton_ingresar = ctk.CTkButton(frame_formulario, text="Ingresar Ingrediente")
        self.boton_ingresar.configure(command=self.ingresar_ingrediente)
        self.boton_ingresar.pack(pady=10)
        self.boton_eliminar = ctk.CTkButton(frame_treeview, text="Eliminar Ingrediente", fg_color="#B11919", text_color="white")
        self.boton_eliminar.configure(command=self.eliminar_ingrediente)
        self.boton_eliminar.pack(pady=10)
        self.tree = ttk.Treeview(self.tab1, columns=("ID", "Nombre", "Unidad","Cantidad"), show="headings",height=25)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Unidad", text="Unidad")
        self.tree.heading("Cantidad", text="Cantidad")
        self.tree.column("ID", width=50)
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)
        
        # --- CAMBIO 2: Botón actualizado ---
        self.boton_generar_menu = ctk.CTkButton(frame_treeview, text="Generar Menús Disponibles", command=self.generar_menus_disponibles_y_cambiar_tab)
        self.boton_generar_menu.pack(pady=10)
        
        self.actualizar_treeview() 

    # --- CAMBIO 3: Nueva función de lógica ---
    def generar_menus_disponibles_y_cambiar_tab(self):
        """
        Usa MenuCRUD (ORM) para filtrar con `filter/lambda` los menús que
        sí tienen stock y reconstruye las tarjetas en la pestaña de pedidos.
        """
        # 1. Limpiar tarjetas existentes
        global tarjetas_frame
        try:
            for child in tarjetas_frame.winfo_children():
                child.destroy()
        except Exception as e:
            print(f"Error limpiando tarjetas_frame: {e}")
        
        # 2. Obtener todos los menús de la DB
        # Asegúrate de que tu get_all_menus cargue las relaciones (joinedload)
        menus_db = self.menu_crud.get_all_menus(self.db_session)
        
        menus_creados = 0
        max_cols = 4
        
        # 3. Filtrar y crear tarjetas (Uso de filter - Requisito Pauta)
        # `filter` + `lambda` evalúa disponibilidad sin construir listas intermedias
        menus_disponibles = list(filter(
            lambda menu_orm: self.menu_crud.esta_disponible(self.db_session, menu_orm),
            menus_db
        ))

        for menu_orm in menus_disponibles:
            try:
                menu_dto = self._convert_menu_orm_to_dto(menu_orm) 
                fila = menus_creados // max_cols
                columna = menus_creados % max_cols
                self.crear_tarjeta(menu_dto, row=fila, column=columna)
                menus_creados += 1
            except Exception as e:
                print(f"Error creando tarjeta para {getattr(menu_orm,'nombre',str(menu_orm))}: {e}")

        if menus_creados == 0:
             CTkMessagebox(title="Stock Vacío", message="No hay ingredientes suficientes para preparar ningún menú.", icon="info")
        else:
             CTkMessagebox(title="Menú Generado", message=f"Se generaron {menus_creados} menús disponibles.", icon="check")

        # 4. Cambiar a la pestaña de Pedido
        self.tabview.set("Pedido")

    def actualizar_treeview(self):
        """Llama al ORM para repoblar el Treeview con el stock vigente."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        ingredientes_db = self.ingrediente_crud.get_all_ingredientes(self.db_session)
        for ingrediente in ingredientes_db:
            try:
                cantidad_mostrada = ingrediente.cantidad_str()
            except Exception:
                cantidad_mostrada = ingrediente.cantidad_stock
            self.tree.insert("", "end", values=(ingrediente.id, ingrediente.nombre, ingrediente.unidad if ingrediente.unidad else '', cantidad_mostrada))

    def ingresar_ingrediente(self):
        """Inserta o acumula ingredientes usando operaciones ORM transaccionales."""
        nombre = self.entry_nombre.get().strip()
        unidad = self.combo_unidad.get().strip()
        cantidad = self.entry_cantidad.get().strip()
        if not nombre:
            CTkMessagebox(title="Error", message="Ingrese un nombre de ingrediente.", icon="warning")
            return
        try:
            cantidad_val = float(cantidad)
        except Exception:
            CTkMessagebox(title="Error", message="La cantidad debe ser un número.", icon="warning")
            return
        if cantidad_val <= 0:
            CTkMessagebox(title="Error", message="La cantidad debe ser mayor que cero.", icon="warning")
            return
        try:
            existente = self.ingrediente_crud.get_ingrediente_by_nombre(self.db_session, nombre)
            if existente:
                existente.cantidad_stock = float(existente.cantidad_stock or 0) + cantidad_val
                if unidad:
                    existente.unidad = unidad
                self.db_session.commit()
                self.db_session.refresh(existente)
                mensaje = f"Se sumaron {cantidad_val} {unidad or ''} a {existente.nombre}."
            else:
                self.ingrediente_crud.create_ingrediente(
                    self.db_session, 
                    nombre=nombre, 
                    unidad=unidad if unidad else None, 
                    cantidad_stock=cantidad_val
                )
                mensaje = f"{nombre.capitalize()} agregado al stock."
            CTkMessagebox(title="Stock actualizado", message=mensaje, icon="check")
            self.entry_nombre.delete(0, 'end')
            self.entry_cantidad.delete(0, 'end')
            self.actualizar_treeview()
        except Exception as e:
            self.db_session.rollback()
            CTkMessagebox(title="Error de BD", message=f"No se pudo guardar: {e}", icon="warning")

    def eliminar_ingrediente(self):
        """Elimina un ingrediente seleccionado aprovechando el CRUD ORM."""
        selecion = self.tree.selection()
        if not selecion:
            CTkMessagebox(title="Error", message="Seleccione un ingrediente para eliminar.", icon="warning")
            return
        item = selecion[0]
        valores = self.tree.item(item, 'values')
        if not valores:
            return
        ingrediente_id = valores[0] 
        nombre = valores[1]
        try:
            eliminado = self.ingrediente_crud.delete_ingrediente_by_id(self.db_session, ingrediente_id)
            if eliminado:
                CTkMessagebox(title="Eliminado", message=f"{nombre.capitalize()} eliminado del stock.", icon="info")
            else:
                CTkMessagebox(title="Error", message=f"No se pudo eliminar {nombre}.", icon="warning")
            self.actualizar_treeview()
        except Exception as e:
            self.db_session.rollback()
            CTkMessagebox(title="Error", message=f"Error al eliminar: {e}", icon="warning")

    # ----------------------------------------------------
    # PESTAÑA 2: PEDIDO
    # ----------------------------------------------------

    def configurar_pestana2(self):
        """Levanta la UI de pedidos que se alimenta de MenuCRUD y ClienteCRUD."""
        frame_superior = ctk.CTkFrame(self.tab2)
        frame_superior.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        frame_intermedio = ctk.CTkFrame(self.tab2)
        frame_intermedio.pack(side="top", fill="x", padx=10, pady=5)
        global tarjetas_frame
        tarjetas_frame = ctk.CTkFrame(frame_superior)
        tarjetas_frame.pack(expand=True, fill="both", padx=10, pady=10)
        self.label_seleccionar_cliente = ctk.CTkLabel(frame_intermedio, text="Asociar Cliente:")
        self.label_seleccionar_cliente.pack(side="left", padx=(10, 5))
        self.combo_clientes = ctk.CTkComboBox(frame_intermedio, values=["Cargando..."])
        self.combo_clientes.pack(side="left", padx=5)
        self.mapa_clientes_combobox = {}
        self.boton_eliminar_menu = ctk.CTkButton(frame_intermedio, text="Eliminar Menú", command=self.eliminar_menu)
        self.boton_eliminar_menu.pack(side="right", padx=10)
        self.label_total = ctk.CTkLabel(frame_intermedio, text="Total: $0.00", anchor="e", font=("Helvetica", 12, "bold"))
        self.label_total.pack(side="right", padx=10)
        frame_inferior = ctk.CTkFrame(self.tab2)
        frame_inferior.pack(side="bottom", fill="both", expand=True, padx=10, pady=10)
        self.treeview_menu = ttk.Treeview(frame_inferior, columns=("Nombre", "Cantidad", "Precio Unitario"), show="headings")
        self.treeview_menu.heading("Nombre", text="Nombre del Menú")
        self.treeview_menu.heading("Cantidad", text="Cantidad")
        self.treeview_menu.heading("Precio Unitario", text="Precio Unitario")
        self.treeview_menu.pack(expand=True, fill="both", padx=10, pady=10)
        self.boton_generar_boleta=ctk.CTkButton(frame_inferior,text="Generar Boleta",command=self.generar_boleta)
        self.boton_generar_boleta.pack(side="bottom",pady=10)

    def actualizar_combobox_clientes(self):
        """Consulta ClienteCRUD vía ORM y usa map/lambda para formatear las etiquetas."""
        clientes = self.cliente_crud.get_all_clientes(self.db_session)
        self.mapa_clientes_combobox.clear()
        if not clientes:
            self.combo_clientes.configure(values=["No hay clientes registrados"])
            self.combo_clientes.set("No hay clientes registrados")
            return
        # `map` + `lambda` genera etiquetas legibles sin bucles explícitos
        nombres_clientes = list(map(lambda c: f"{c.id}: {c.nombre} ({c.email})", clientes))
        for cliente in clientes:
            self.mapa_clientes_combobox[f"{cliente.id}: {cliente.nombre} ({cliente.email})"] = cliente.id
        self.combo_clientes.configure(values=nombres_clientes)
        self.combo_clientes.set(nombres_clientes[0])

    def generar_menus(self):
        """Función 'generar_menus' antigua, ahora se usa 'generar_menus_disponibles'."""
        # Esta función ya no se usa activamente, pero la dejamos por si acaso.
        print("ADVERTENCIA: Se llamó a generar_menus() en lugar de generar_menus_disponibles_y_cambiar_tab()")
        try:
            for child in tarjetas_frame.winfo_children():
                child.destroy()
        except Exception:
            pass
        self.menus = self.menu_crud.get_all_menus(self.db_session)
        max_cols = 4
        for idx, menu_orm in enumerate(self.menus):
            try:
                menu_dto = self._convert_menu_orm_to_dto(menu_orm)
                fila = idx // max_cols
                columna = idx % max_cols
                self.crear_tarjeta(menu_dto, row=fila, column=columna)
            except Exception as e:
                print(f"Error creando tarjeta para {getattr(menu_orm,'nombre',str(menu_orm))}: {e}")

    def _convert_menu_orm_to_dto(self, menu_orm: Menu) -> CrearMenu:
        # ... (código de _convert_menu_orm_to_dto sin cambios) ...
        ingredientes_dto = list(map(lambda assoc: IngredienteDTO(
            nombre=assoc.ingrediente.nombre,
            unidad=assoc.ingrediente.unidad,
            cantidad=assoc.cantidad_requerida
        ), menu_orm.ingredientes_asociados))
        return CrearMenu(
            nombre=menu_orm.nombre,
            ingredientes=ingredientes_dto,
            precio=menu_orm.precio,
            icono_path=menu_orm.icono_path,
            cantidad=0,
            id_orm=menu_orm.id 
        )

    def tarjeta_click(self, event, menu_dto: CrearMenu):
        menu_orm = self.menu_crud.get_menu_by_id(self.db_session, menu_dto.id_orm)
        if not menu_orm:
            CTkMessagebox(title="Error", message="El menú no existe en la base de datos.", icon="warning")
            return
        try:
            # Consumimos el stock inmediatamente para reservar los ingredientes
            self.menu_crud.consumir_stock(self.db_session, menu_orm, 1)
        except ValueError as e:
            self.db_session.rollback()
            CTkMessagebox(title="Stock Insuficiente", message=str(e), icon="warning")
            return
        except Exception as e:
            self.db_session.rollback()
            CTkMessagebox(title="Error", message=f"No se pudo consumir stock: {e}", icon="warning")
            return

        self.pedido.agregar_menu(menu_dto)
        self.actualizar_treeview_pedido()
        total = reduce(lambda subtotal, item: subtotal + (item.precio * item.cantidad), self.pedido.menus, 0.0)
        try:
            self.label_total.configure(text=f"Total: ${total:.2f}")
        except Exception:
            pass

    def generar_boleta(self):
        """Consume stock vía ORM, persiste Pedido/Detalle y genera el PDF con Facade."""

        if not self.pedido.menus:
            CTkMessagebox(title="Boleta", message="El pedido está vacío.", icon="warning")
            return
        cliente_seleccionado_display = self.combo_clientes.get()
        cliente_id_seleccionado = self.mapa_clientes_combobox.get(cliente_seleccionado_display)
        if cliente_id_seleccionado is None:
            CTkMessagebox(title="Error", message="Debe seleccionar un cliente válido para generar la boleta.", icon="warning")
            return
        try:
            self.pedido_crud.create_pedido_from_dto(self.db_session, self.pedido, cliente_id_seleccionado)
                
            facade = BoletaFacade(self.pedido)
            resultado = facade.generar_boleta()
            
            CTkMessagebox(title="Boleta y Stock", message=resultado, icon="info")
            self._boleta_mostrable = True
            self.actualizar_treeview() 
            self.pedido.menus = [] 
            self.actualizar_treeview_pedido()
            self.label_total.configure(text="Total: $0.00")
        except Exception as e:
            import traceback
            traceback.print_exc()                       # imprime traza en la consola
            CTkMessagebox(title="Error en la Compra", message=f"No se pudo completar la compra:\n{e}", icon="warning")
            self.db_session.rollback()
            self.restaurar_stock_pedido_actual()


    # ----------------------------------------------------
    # PESTAÑA 3: CARGA CSV
    # ----------------------------------------------------
    def configurar_pestana3(self):
        """Coloca los widgets que permiten importar CSVs y cargarlos vía ORM."""
        label = ctk.CTkLabel(self.tab3, text="Carga de archivo CSV")
        label.pack(pady=20)
        boton_cargar_csv = ctk.CTkButton(self.tab3, text="Cargar CSV", text_color="white",command=self.cargar_csv)
        boton_cargar_csv.pack(pady=10)
        self.frame_tabla_csv = ctk.CTkFrame(self.tab3)
        self.frame_tabla_csv.pack(fill="both", expand=True, padx=10, pady=10)
        self.df_csv = None   
        self.tabla_csv = None
        self.boton_agregar_stock = ctk.CTkButton(self.frame_tabla_csv, text="Agregar al Stock")
        self.boton_agregar_stock.pack(side="bottom", pady=10)

    def cargar_csv(self):
        """Utiliza pandas para transformar el CSV antes de delegar al CRUD ORM."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo CSV",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        if not file_path:
            return
        self.csv_file_path = file_path 
        self.df_csv = pd.read_csv(file_path)
        self.mostrar_dataframe_en_tabla(self.df_csv)
        self.boton_agregar_stock.configure(command=self.agregar_csv_al_stock)
    
    def agregar_csv_al_stock(self):
        """Ingresa masivamente ingredientes usando las mismas transacciones ORM."""
        if not hasattr(self, 'csv_file_path') or not self.csv_file_path:
            CTkMessagebox(title="Error", message="Primero debes cargar un archivo CSV.", icon="warning")
            return
        try:
            ingredientes_creados = self.ingrediente_crud.load_ingredientes_from_csv(self.db_session, self.csv_file_path)
            CTkMessagebox(title="Stock Actualizado", message=f"{len(ingredientes_creados)} ingredientes procesados desde el CSV.", icon="check")
            self.actualizar_treeview()
        except Exception as e:
            CTkMessagebox(title="Error de CSV", message=f"Error al procesar el CSV: {e}", icon="warning")

    # ----------------------------------------------------
    # PESTAÑAS 4, 5, 6, 7 (Carta, Boleta, Clientes, Gestión Pedidos)
    # ----------------------------------------------------
    
    def _configurar_pestana_crear_menu(self):
        """Renderiza los controles que generan el PDF de la carta usando datos del ORM."""
        contenedor = ctk.CTkFrame(self.tab4)
        contenedor.pack(expand=True, fill="both", padx=10, pady=10)
        boton_menu = ctk.CTkButton(contenedor, text="Generar Carta (PDF)", command=self.generar_y_mostrar_carta_pdf)
        boton_menu.pack(pady=10)
        self.pdf_frame_carta = ctk.CTkFrame(contenedor)
        self.pdf_frame_carta.pack(expand=True, fill="both", padx=10, pady=10)
        self.pdf_viewer_carta = None

    def generar_y_mostrar_carta_pdf(self):
        """Consulta MenuCRUD vía ORM y envía los datos a la fábrica de PDFs."""
        try:
            menus_db = self.menu_crud.get_all_menus(self.db_session)
            pdf_path = "carta.pdf"
            create_menu_pdf(menus_db, pdf_path,
                titulo_negocio="Restaurante",
                subtitulo="Carta 2025",
                moneda="$")
            if self.pdf_viewer_carta is not None:
                self.pdf_viewer_carta.pack_forget()
                self.pdf_viewer_carta.destroy()
            abs_pdf = os.path.abspath(pdf_path)
            self.pdf_viewer_carta = CTkPDFViewer(self.pdf_frame_carta, file=abs_pdf)
            self.pdf_viewer_carta.pack(expand=True, fill="both")
        except Exception as e:
            CTkMessagebox(title="Error", message=f"No se pudo generar/mostrar la carta.\n{e}", icon="warning")

    def _configurar_pestana_ver_boleta(self):
        """Prepara la vista previa de boletas (PDF) generadas desde el ORM."""
        contenedor = ctk.CTkFrame(self.tab5)
        contenedor.pack(expand=True, fill="both", padx=10, pady=10)
        boton_boleta = ctk.CTkButton(contenedor, text="Mostrar Boleta (PDF)", command=self.mostrar_boleta)
        boton_boleta.pack(pady=10)
        self.pdf_frame_boleta = ctk.CTkFrame(contenedor)
        self.pdf_frame_boleta.pack(expand=True, fill="both", padx=10, pady=10)
        self.pdf_viewer_boleta = None

    def mostrar_boleta(self):
        """Abre el PDF generado tras persistir el Pedido/Detalle vía ORM."""
        if not self._boleta_mostrable:
            CTkMessagebox(title="Boleta", message="Primero genere la boleta usando 'Generar Boleta'.", icon="info")
            return
        try:
            pdf_path = os.path.abspath("boleta.pdf")
            if not os.path.exists(pdf_path):
                CTkMessagebox(title="Boleta", message="No se encontró 'boleta.pdf'.", icon="warning")
                self._boleta_mostrable = False
                return
            if self.pdf_viewer_boleta is not None:
                self.pdf_viewer_boleta.pack_forget()
                self.pdf_viewer_boleta.destroy()
            self.pdf_viewer_boleta = CTkPDFViewer(self.pdf_frame_boleta, file=pdf_path)
            self.pdf_viewer_boleta.pack(expand=True, fill="both")
        except Exception as e:
            CTkMessagebox(title="Error Boleta", message=f"No se pudo mostrar la boleta: {e}", icon="warning")
        finally:
            self._boleta_mostrable = False

    def configurar_pestana_clientes(self):
        """Widgetiza el CRUD de clientes conectado a ClienteCRUD (ORM)."""
        frame_formulario = ctk.CTkFrame(self.tab_clientes)
        frame_formulario.pack(side="left", fill="y", padx=10, pady=10)
        frame_treeview = ctk.CTkFrame(self.tab_clientes)
        frame_treeview.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        label_titulo = ctk.CTkLabel(frame_formulario, text="Gestión de Clientes", font=("Helvetica", 16, "bold"))
        label_titulo.pack(pady=10)
        label_nombre_cliente = ctk.CTkLabel(frame_formulario, text="Nombre:")
        label_nombre_cliente.pack(pady=5)
        self.entry_nombre_cliente = ctk.CTkEntry(frame_formulario)
        self.entry_nombre_cliente.pack(pady=5, padx=10)
        label_email_cliente = ctk.CTkLabel(frame_formulario, text="Email:")
        label_email_cliente.pack(pady=5)
        self.entry_email_cliente = ctk.CTkEntry(frame_formulario)
        self.entry_email_cliente.pack(pady=5, padx=10)
        self.boton_crear_cliente = ctk.CTkButton(frame_formulario, text="Crear Cliente", command=self.crear_cliente)
        self.boton_crear_cliente.pack(pady=10)
        self.boton_eliminar_cliente = ctk.CTkButton(frame_formulario, text="Eliminar Cliente", fg_color="#B11919", text_color="white", command=self.eliminar_cliente)
        self.boton_eliminar_cliente.pack(pady=10)
        self.tree_clientes = ttk.Treeview(frame_treeview, columns=("ID", "Nombre", "Email"), show="headings", height=25)
        self.tree_clientes.heading("ID", text="ID")
        self.tree_clientes.heading("Nombre", text="Nombre")
        self.tree_clientes.heading("Email", text="Email")
        self.tree_clientes.column("ID", width=50)
        self.tree_clientes.pack(expand=True, fill="both")
        self.actualizar_treeview_clientes()

    def actualizar_treeview_clientes(self):
        """Refresca el listado de clientes con datos ORM recientes."""
        for item in self.tree_clientes.get_children():
            self.tree_clientes.delete(item)
        try:
            clientes = self.cliente_crud.get_all_clientes(self.db_session)
            for cliente in clientes:
                self.tree_clientes.insert("", "end", values=(cliente.id, cliente.nombre, cliente.email))
        except Exception as e:
            print(f"Error al cargar clientes: {e}")

    def crear_cliente(self):
        """Valida entradas y delega la creación al ClienteCRUD (ORM)."""
        nombre = self.entry_nombre_cliente.get().strip()
        email = self.entry_email_cliente.get().strip()
        try:
            self.cliente_crud.create_cliente(self.db_session, nombre=nombre, email=email)
            CTkMessagebox(title="Éxito", message="Cliente creado correctamente.", icon="check")
            self.entry_nombre_cliente.delete(0, 'end')
            self.entry_email_cliente.delete(0, 'end')
            self.actualizar_treeview_clientes()
            self.actualizar_combobox_clientes() # Actualiza el ComboBox en Pedidos
        except ValueError as e:
            CTkMessagebox(title="Error de Validación", message=str(e), icon="warning")
        except Exception as e:
            self.db_session.rollback()
            if "UNIQUE constraint failed" in str(e) or "Ya existe un cliente con ese email" in str(e):
                CTkMessagebox(title="Error de Duplicado", message="El correo electrónico ya está registrado.", icon="warning")
            else:
                CTkMessagebox(title="Error de BD", message=f"Error inesperado: {e}", icon="warning")

    def eliminar_cliente(self):
        """Invoca el CRUD para borrar clientes respetando las FK (pedidos)."""
        selecion = self.tree_clientes.selection()
        if not selecion:
            CTkMessagebox(title="Error", message="Seleccione un cliente para eliminar.", icon="warning")
            return
        item = selecion[0]
        valores = self.tree_clientes.item(item, 'values')
        if not valores: return
        cliente_id = valores[0]
        nombre = valores[1]
        try:
            self.cliente_crud.delete_cliente_by_id(self.db_session, cliente_id)
            CTkMessagebox(title="Eliminado", message=f"Cliente '{nombre}' eliminado.", icon="info")
            self.actualizar_treeview_clientes()
            self.actualizar_combobox_clientes()
        except Exception as e:
            self.db_session.rollback()
            CTkMessagebox(title="Error", message=f"Error al eliminar: {e}", icon="warning")

    def configurar_pestana_gestion_pedidos(self):
        """Muestra pedidos históricos combinando PedidoCRUD y DetallePedidoCRUD."""
        frame_pedidos = ctk.CTkFrame(self.tab_gestion_pedidos)
        frame_pedidos.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        frame_detalles = ctk.CTkFrame(self.tab_gestion_pedidos)
        frame_detalles.pack(side="right", fill="y", padx=10, pady=10)
        label_pedidos = ctk.CTkLabel(frame_pedidos, text="Pedidos Registrados (Boletas)", font=("Helvetica", 16, "bold"))
        label_pedidos.pack(pady=10)
        self.tree_gestion_pedidos = ttk.Treeview(frame_pedidos, columns=("ID", "Fecha", "Cliente", "Total"), show="headings")
        self.tree_gestion_pedidos.heading("ID", text="ID Boleta")
        self.tree_gestion_pedidos.heading("Fecha", text="Fecha")
        self.tree_gestion_pedidos.heading("Cliente", text="Cliente")
        self.tree_gestion_pedidos.heading("Total", text="Total")
        self.tree_gestion_pedidos.column("ID", width=60)
        self.tree_gestion_pedidos.column("Fecha", width=150)
        self.tree_gestion_pedidos.pack(expand=True, fill="both")
        self.tree_gestion_pedidos.bind('<<TreeviewSelect>>', self.mostrar_detalles_pedido)
        label_detalles = ctk.CTkLabel(frame_detalles, text="Detalle del Pedido", font=("Helvetica", 16, "bold"))
        label_detalles.pack(pady=10)
        self.tree_detalles_pedido = ttk.Treeview(frame_detalles, columns=("Item", "Cantidad", "Precio Unit."), show="headings")
        self.tree_detalles_pedido.heading("Item", text="Item")
        self.tree_detalles_pedido.heading("Cantidad", text="Cantidad")
        self.tree_detalles_pedido.heading("Precio Unit.", text="Precio Unit.")
        self.tree_detalles_pedido.column("Cantidad", width=70)
        self.tree_detalles_pedido.pack(expand=True, fill="both")
        self.actualizar_treeview_gestion_pedidos()

    def actualizar_treeview_gestion_pedidos(self):
        """Hace un JOIN ORM para listar pedidos con su cliente y totales."""
        for item in self.tree_gestion_pedidos.get_children():
            self.tree_gestion_pedidos.delete(item)
        try:
            pedidos_con_cliente = self.pedido_crud.get_pedidos_con_cliente(self.db_session)
            for pedido, nombre_cliente in pedidos_con_cliente:
                fecha_formateada = pedido.fecha.strftime('%Y-%m-%d %H:%M')
                total_formateado = f"${pedido.total_final:,.2f}"
                self.tree_gestion_pedidos.insert("", "end", values=(pedido.id, fecha_formateada, nombre_cliente or "N/A", total_formateado))
        except Exception as e:
            print(f"Error al cargar pedidos: {e}")

    def mostrar_detalles_pedido(self, event=None):
        """Carga los detalles ORM asociados al pedido seleccionado en la UI."""
        for item in self.tree_detalles_pedido.get_children():
            self.tree_detalles_pedido.delete(item)
        selecion = self.tree_gestion_pedidos.selection()
        if not selecion: return
        item = selecion[0]
        valores = self.tree_gestion_pedidos.item(item, 'values')
        if not valores: return
        pedido_id = valores[0]
        try:
            detalles = self.detalle_pedido_crud.get_detalles_by_pedido_id(self.db_session, pedido_id)
            if detalles:
                filas = list(map(lambda detalle: (detalle.nombre_menu, detalle.cantidad, f"${detalle.precio_unitario:,.2f}"), detalles))
                for fila in filas:
                    self.tree_detalles_pedido.insert("", "end", values=fila)
        except Exception as e:
            print(f"Error al cargar detalles: {e}")

    # ----------------------------------------------------
    # PESTAÑA: GESTIÓN DE MENÚS
    # ----------------------------------------------------

    def configurar_pestana_gestion_menus(self):
        """Permite crear, editar y eliminar menús basados en ingredientes existentes."""
        contenedor = ctk.CTkFrame(self.tab_gestion_menus)
        contenedor.pack(expand=True, fill="both", padx=10, pady=10)

        frame_form = ctk.CTkFrame(contenedor)
        frame_form.pack(side="left", fill="y", padx=10, pady=10)

        frame_listado = ctk.CTkFrame(contenedor)
        frame_listado.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Formulario principal para capturar metadata del menú
        self.entry_menu_nombre = ctk.CTkEntry(frame_form, placeholder_text="Nombre del menú")
        self.entry_menu_nombre.pack(pady=5, fill="x")

        self.entry_menu_precio = ctk.CTkEntry(frame_form, placeholder_text="Precio")
        self.entry_menu_precio.pack(pady=5, fill="x")

        self.entry_menu_icono = ctk.CTkEntry(frame_form, placeholder_text="Ruta de ícono (opcional)")
        self.entry_menu_icono.pack(pady=5, fill="x")

        self.combo_menu_ingredientes = ctk.CTkComboBox(frame_form, values=["Cargando..."])
        self.combo_menu_ingredientes.pack(pady=5, fill="x")

        self.entry_cantidad_ingrediente = ctk.CTkEntry(frame_form, placeholder_text="Cantidad requerida")
        self.entry_cantidad_ingrediente.pack(pady=5, fill="x")

        botones_ingrediente = ctk.CTkFrame(frame_form)
        botones_ingrediente.pack(fill="x", pady=5)

        self.boton_agregar_ingrediente_temp = ctk.CTkButton(botones_ingrediente, text="Agregar ingrediente", command=self.agregar_ingrediente_temp)
        self.boton_agregar_ingrediente_temp.pack(side="left", expand=True, padx=5)

        self.boton_remover_ingrediente_temp = ctk.CTkButton(botones_ingrediente, text="Quitar seleccionado", command=self.remover_ingrediente_temp)
        self.boton_remover_ingrediente_temp.pack(side="left", expand=True, padx=5)

        # Tabla temporal donde se muestra la receta en construcción
        self.tree_ingredientes_menu = ttk.Treeview(frame_form, columns=("Ingrediente", "Cantidad"), show="headings", height=6)
        self.tree_ingredientes_menu.heading("Ingrediente", text="Ingrediente")
        self.tree_ingredientes_menu.heading("Cantidad", text="Cantidad")
        self.tree_ingredientes_menu.pack(fill="both", pady=5)
        self.label_total_receta = ctk.CTkLabel(frame_form, text="Total de insumos: 0")
        self.label_total_receta.pack(pady=(0, 10))

        botones_accion = ctk.CTkFrame(frame_form)
        botones_accion.pack(fill="x", pady=10)

        self.boton_guardar_menu = ctk.CTkButton(botones_accion, text="Guardar menú", command=self.crear_o_actualizar_menu)
        self.boton_guardar_menu.pack(side="left", expand=True, padx=5)

        self.boton_cancelar_edicion_menu = ctk.CTkButton(botones_accion, text="Cancelar", command=self.cancelar_edicion_menu, fg_color="#B11919")
        self.boton_cancelar_edicion_menu.pack(side="left", expand=True, padx=5)

        label_listado = ctk.CTkLabel(frame_listado, text="Menús disponibles", font=("Helvetica", 16, "bold"))
        label_listado.pack(pady=5)

        # Listado maestro de menús persistidos en la base
        self.tree_menus = ttk.Treeview(frame_listado, columns=("ID", "Nombre", "Precio"), show="headings")
        self.tree_menus.heading("ID", text="ID")
        self.tree_menus.heading("Nombre", text="Nombre")
        self.tree_menus.heading("Precio", text="Precio")
        self.tree_menus.column("ID", width=50)
        self.tree_menus.pack(expand=True, fill="both", padx=5, pady=5)
        self.tree_menus.bind("<<TreeviewSelect>>", self.cargar_menu_en_formulario)

        frame_botones_menus = ctk.CTkFrame(frame_listado)
        frame_botones_menus.pack(fill="x", pady=5)

        self.boton_eliminar_menu_admin = ctk.CTkButton(frame_botones_menus, text="Eliminar menú", command=self.eliminar_menu_gestion, fg_color="#B11919")
        self.boton_eliminar_menu_admin.pack(side="right", padx=5)

        self.actualizar_combobox_ingredientes_menu()
        self.actualizar_treeview_menus()
        self.actualizar_treeview_ingredientes_temp()

    def actualizar_treeview_menus(self):
        """Refresca el listado de menús usando el ORM."""
        if not hasattr(self, "tree_menus"):
            return
        for item in self.tree_menus.get_children():
            self.tree_menus.delete(item)
        self.menus = self.menu_crud.get_all_menus(self.db_session)
        menus_filtrados = list(filter(lambda menu: menu.ingredientes_asociados, self.menus))
        filas = list(map(lambda m: (m.id, m.nombre, f"${m.precio:,.0f}"), menus_filtrados))
        for fila in filas:
            self.tree_menus.insert("", "end", values=fila)

    def actualizar_combobox_ingredientes_menu(self):
        """Carga los ingredientes existentes en el combo del formulario."""
        try:
            ingredientes = self.ingrediente_crud.get_all_ingredientes(self.db_session)
            if not ingredientes:
                self.combo_menu_ingredientes.configure(values=["Sin ingredientes"])
                self.combo_menu_ingredientes.set("Sin ingredientes")
                return
            valores = [f"{ing.id}: {ing.nombre} ({ing.unidad or ''})" for ing in ingredientes]
            self.combo_menu_ingredientes.configure(values=valores)
            self.combo_menu_ingredientes.set(valores[0])
            self._mapa_ingredientes_combobox = {f"{ing.id}: {ing.nombre} ({ing.unidad or ''})": ing for ing in ingredientes}
        except Exception as e:
            print(f"Error cargando ingredientes: {e}")

    def agregar_ingrediente_temp(self):
        """Agrega un ingrediente a la lista temporal antes de guardar el menú."""
        if not hasattr(self, "combo_menu_ingredientes"):
            return
        seleccionado = self.combo_menu_ingredientes.get()
        if not seleccionado or seleccionado.startswith("Sin ingredientes"):
            CTkMessagebox(title="Ingredientes", message="No hay ingredientes disponibles. Registre primero en stock.", icon="warning")
            return
        ingrediente = self._mapa_ingredientes_combobox.get(seleccionado)
        cantidad = self.entry_cantidad_ingrediente.get().strip()
        try:
            cantidad_val = float(cantidad)
        except Exception:
            CTkMessagebox(title="Cantidad inválida", message="La cantidad requerida debe ser un número.", icon="warning")
            return
        if cantidad_val <= 0:
            CTkMessagebox(title="Cantidad inválida", message="La cantidad requerida debe ser mayor que cero.", icon="warning")
            return
        if ingrediente.cantidad_stock < cantidad_val:
            CTkMessagebox(title="Stock insuficiente", message=f"No hay suficiente stock de {ingrediente.nombre} para esta receta.", icon="warning")
            return
        existente = next((item for item in self.menu_temp_ingredientes if item["ingrediente_id"] == ingrediente.id), None)
        if existente:
            existente["cantidad_requerida"] = cantidad_val
        else:
            self.menu_temp_ingredientes.append(
                {
                    "ingrediente_id": ingrediente.id,
                    "ingrediente_nombre": ingrediente.nombre,
                    "cantidad_requerida": cantidad_val,
                }
            )
        self.entry_cantidad_ingrediente.delete(0, 'end')
        self.actualizar_treeview_ingredientes_temp()

    def remover_ingrediente_temp(self):
        """Quita el ingrediente seleccionado de la receta temporal."""
        selecion = self.tree_ingredientes_menu.selection()
        if not selecion:
            return
        item = selecion[0]
        valores = self.tree_ingredientes_menu.item(item, 'values')
        if not valores:
            return
        nombre = valores[0]
        self.menu_temp_ingredientes = [i for i in self.menu_temp_ingredientes if i["ingrediente_nombre"] != nombre]
        self.actualizar_treeview_ingredientes_temp()

    def actualizar_treeview_ingredientes_temp(self):
        """Refresca el treeview local con los ingredientes de la receta."""
        if not hasattr(self, "tree_ingredientes_menu"):
            return
        for item in self.tree_ingredientes_menu.get_children():
            self.tree_ingredientes_menu.delete(item)
        filas = list(map(lambda ing: (ing["ingrediente_nombre"], ing["cantidad_requerida"]), self.menu_temp_ingredientes))
        for fila in filas:
            self.tree_ingredientes_menu.insert("", "end", values=fila)
        total_insumos = reduce(lambda acc, ing: acc + float(ing["cantidad_requerida"]), self.menu_temp_ingredientes, 0.0)
        if hasattr(self, "label_total_receta"):
            self.label_total_receta.configure(text=f"Total de insumos: {total_insumos}")

    def crear_o_actualizar_menu(self):
        """Crea o actualiza un menú en base a los datos del formulario."""
        nombre = self.entry_menu_nombre.get().strip()
        precio = self.entry_menu_precio.get().strip()
        icono = self.entry_menu_icono.get().strip() or None
        if not nombre:
            CTkMessagebox(title="Validación", message="El nombre del menú es obligatorio.", icon="warning")
            return
        try:
            precio_val = float(precio)
        except Exception:
            CTkMessagebox(title="Validación", message="El precio debe ser numérico.", icon="warning")
            return
        if precio_val <= 0:
            CTkMessagebox(title="Validación", message="El precio debe ser mayor que cero.", icon="warning")
            return
        if not self.menu_temp_ingredientes:
            CTkMessagebox(title="Ingredientes", message="Agregue al menos un ingrediente.", icon="warning")
            return
        try:
            if self.menu_en_edicion:
                self.menu_crud.update_menu(
                    self.db_session,
                    self.menu_en_edicion,
                    nombre=nombre,
                    precio=precio_val,
                    icono_path=icono,
                    ingredientes=self.menu_temp_ingredientes,
                )
                mensaje = "Menú actualizado correctamente."
            else:
                self.menu_crud.create_menu(
                    self.db_session,
                    nombre=nombre,
                    precio=precio_val,
                    icono_path=icono,
                    ingredientes=self.menu_temp_ingredientes,
                )
                mensaje = "Menú creado correctamente."
            CTkMessagebox(title="Gestión de menús", message=mensaje, icon="check")
            self.limpiar_formulario_menu()
            self.actualizar_treeview_menus()
        except Exception as e:
            self.db_session.rollback()
            CTkMessagebox(title="Error", message=f"No se pudo guardar el menú: {e}", icon="warning")

    def cargar_menu_en_formulario(self, event=None):
        """Carga un menú existente para editarlo."""
        selecion = self.tree_menus.selection()
        if not selecion:
            return
        item = selecion[0]
        valores = self.tree_menus.item(item, 'values')
        if not valores:
            return
        menu_id = int(valores[0])
        menu = self.menu_crud.get_menu_by_id(self.db_session, menu_id)
        if not menu:
            return
        self.menu_en_edicion = menu.id
        self.entry_menu_nombre.delete(0, 'end')
        self.entry_menu_nombre.insert(0, menu.nombre)
        self.entry_menu_precio.delete(0, 'end')
        self.entry_menu_precio.insert(0, str(menu.precio))
        self.entry_menu_icono.delete(0, 'end')
        self.entry_menu_icono.insert(0, menu.icono_path or "")
        self.menu_temp_ingredientes = []
        for asociacion in menu.ingredientes_asociados:
            self.menu_temp_ingredientes.append(
                {
                    "ingrediente_id": asociacion.ingrediente_id,
                    "ingrediente_nombre": asociacion.ingrediente.nombre,
                    "cantidad_requerida": asociacion.cantidad_requerida,
                }
            )
        self.actualizar_treeview_ingredientes_temp()
        self.boton_guardar_menu.configure(text="Actualizar menú")

    def limpiar_formulario_menu(self):
        """Restablece el formulario a su estado inicial."""
        self.menu_en_edicion = None
        self.entry_menu_nombre.delete(0, 'end')
        self.entry_menu_precio.delete(0, 'end')
        self.entry_menu_icono.delete(0, 'end')
        self.menu_temp_ingredientes = []
        self.actualizar_treeview_ingredientes_temp()
        self.boton_guardar_menu.configure(text="Guardar menú")

    def cancelar_edicion_menu(self):
        """Cancela la edición en curso."""
        self.limpiar_formulario_menu()

    def eliminar_menu_gestion(self):
        """Elimina el menú seleccionado desde la tabla."""
        selecion = self.tree_menus.selection()
        if not selecion:
            CTkMessagebox(title="Gestión de menús", message="Seleccione un menú para eliminar.", icon="warning")
            return
        item = selecion[0]
        valores = self.tree_menus.item(item, 'values')
        if not valores:
            return
        menu_id = int(valores[0])
        menu = self.menu_crud.get_menu_by_id(self.db_session, menu_id)
        if not menu:
            return
        try:
            self.menu_crud.delete_menu_by_name(self.db_session, menu.nombre)
            CTkMessagebox(title="Gestión de menús", message="Menú eliminado.", icon="info")
            self.limpiar_formulario_menu()
            self.actualizar_treeview_menus()
        except Exception as e:
            self.db_session.rollback()
            CTkMessagebox(title="Error", message=f"No se pudo eliminar el menú: {e}", icon="warning")

    # ----------------------------------------------------
    # PESTAÑA 8: GRÁFICO DE VENTAS
    # ----------------------------------------------------

    def configurar_pestana_grafico_ventas(self):
        """Sección visual que muestra datos agregados del ORM mediante Matplotlib."""
        contenedor = ctk.CTkFrame(self.tab_grafico_ventas)
        contenedor.pack(expand=True, fill="both", padx=10, pady=10)

        header = ctk.CTkFrame(contenedor)
        header.pack(fill="x", pady=(0, 10))

        self.label_grafico_estado = ctk.CTkLabel(header, text="Visualiza métricas del restaurante.")
        self.label_grafico_estado.pack(side="left", padx=10, pady=5)

        opciones = ["Ventas por Cliente", "Ventas por Fecha", "Menús más Vendidos", "Uso de Ingredientes"]
        # Selector de métrica para cubrir todos los gráficos solicitados en la pauta
        self.combo_tipo_grafico = ctk.CTkComboBox(header, values=opciones, command=lambda _: self.actualizar_grafico_ventas(), variable=self.tipo_grafico_var)
        self.combo_tipo_grafico.set(opciones[0])
        self.combo_tipo_grafico.pack(side="left", padx=10, pady=5)

        ctk.CTkLabel(header, text="Periodo:").pack(side="left", padx=(20, 5))
        self.combo_periodo_fecha = ctk.CTkComboBox(
            header,
            values=["Diario", "Semanal", "Mensual"],
            command=lambda _: self.actualizar_grafico_ventas(),
            variable=self.periodo_fecha_var,
        )
        self.combo_periodo_fecha.set("Diario")
        self.combo_periodo_fecha.pack(side="left", padx=5, pady=5)

        self.boton_actualizar_grafico = ctk.CTkButton(header, text="Actualizar gráfico", command=self.actualizar_grafico_ventas)
        self.boton_actualizar_grafico.pack(side="right", padx=10, pady=5)

        self.frame_canvas_ventas = ctk.CTkFrame(contenedor)
        self.frame_canvas_ventas.pack(expand=True, fill="both", padx=5, pady=5)

    def actualizar_grafico_ventas(self):
        """Renderiza gráficos estadísticos seleccionables desde la UI."""
        if self.canvas_ventas:
            try:
                self.canvas_ventas.get_tk_widget().destroy()
            except Exception:
                pass
            self.canvas_ventas = None

        tipo = self.tipo_grafico_var.get()
        if tipo == "Ventas por Fecha":
            self.combo_periodo_fecha.configure(state="normal")
        else:
            self.combo_periodo_fecha.configure(state="disabled")
        try:
            dataset = resolver_dataset(
                tipo,
                self.pedido_crud,
                self.detalle_pedido_crud,
                self.db_session,
                periodo_fecha=self.periodo_fecha_var.get(),
            )
        except Exception as e:
            self.label_grafico_estado.configure(text=f"Error al cargar datos: {e}")
            return

        if not dataset:
            self.label_grafico_estado.configure(text="No hay datos disponibles para graficar.")
            return

        etiquetas, valores, titulo, xlabel, ylabel = dataset
        if not etiquetas:
            self.label_grafico_estado.configure(text="No hay datos disponibles para graficar.")
            return

        self.canvas_ventas = render_bar_chart(self.frame_canvas_ventas, etiquetas, valores, titulo, xlabel, ylabel)
        self.label_grafico_estado.configure(text=f"{tipo}: {len(etiquetas)} registros mostrados")
            
    # ----------------------------------------------------
    # MÉTODOS AUXILIARES (Sin cambios)
    # ----------------------------------------------------
    
    def mostrar_dataframe_en_tabla(self, df):
        """Renderiza un DataFrame de pandas dentro de un Treeview."""
        if self.tabla_csv:
            self.tabla_csv.destroy()
        self.tabla_csv = ttk.Treeview(self.frame_tabla_csv, columns=list(df.columns), show="headings")
        for col in df.columns:
            self.tabla_csv.heading(col, text=col)
            self.tabla_csv.column(col, width=100, anchor="center")
        for _, row in df.iterrows():
            self.tabla_csv.insert("", "end", values=list(row))
        self.tabla_csv.pack(expand=True, fill="both", padx=10, pady=10)

    def actualizar_treeview_pedido(self):
        """Refleja los menús agregados al pedido en progreso."""
        for item in self.treeview_menu.get_children():
            self.treeview_menu.delete(item)
        for menu in self.pedido.menus:
            self.treeview_menu.insert("", "end", values=(menu.nombre, menu.cantidad, f"${menu.precio:.2f}"))

    def crear_tarjeta(self, menu, row=0, column=0):
        """Genera una tarjeta interactiva por menú disponible."""
        tarjeta = ctk.CTkFrame(tarjetas_frame, corner_radius=10, border_width=1, border_color="#4CAF50", width=64, height=140, fg_color="gray")
        tarjeta.grid(row=row, column=column, padx=15, pady=15, sticky="nsew")
        tarjeta.bind("<Button-1>", lambda event, m=menu: self.tarjeta_click(event, m))
        tarjeta.bind("<Enter>", lambda event: tarjeta.configure(border_color="#FF0000"))
        tarjeta.bind("<Leave>", lambda event: tarjeta.configure(border_color="#4CAF50"))
        if getattr(menu, "icono_path", None):
            try:
                icono = self.cargar_icono_menu(menu.icono_path)
                imagen_label = ctk.CTkLabel(tarjeta, image=icono, width=64, height=64, text="", bg_color="transparent")
                imagen_label.image = icono
                imagen_label.pack(anchor="center", pady=5, padx=10)
                imagen_label.bind("<Button-1>", lambda event, m=menu: self.tarjeta_click(event, m))
            except Exception as e:
                print(f"No se pudo cargar la imagen '{menu.icono_path}': {e}")
        texto_label = ctk.CTkLabel(tarjeta, text=f"{menu.nombre}", text_color="black", font=("Helvetica", 12, "bold"), bg_color="transparent")
        texto_label.pack(anchor="center", pady=1)
        texto_label.bind("<Button-1>", lambda event, m=menu: self.tarjeta_click(event, m))

    def eliminar_menu(self):
        #Muestra opciones para eliminar 1, eliminar todo o cancelar.
        selecion = self.treeview_menu.selection()
        if not selecion:
            CTkMessagebox(title="Error", message="Seleccione un elemento del pedido para eliminar.", icon="warning")
            return

        item = selecion[0]
        valores = self.treeview_menu.item(item, 'values')
        if not valores:
            return

        nombre = valores[0]

        # Obtener el menú ORM
        menu_orm = self.menu_crud.get_menu_by_name(self.db_session, nombre)
        if not menu_orm:
            CTkMessagebox(title="Error", message="No se encontró el menú en la base de datos.", icon="warning")
            return

        # Ventana emergente con 3 opciones
        msg = CTkMessagebox(
            title="Eliminar del Pedido",
            message=f" ¿Qué deseas hacer con '{nombre}'?",
            icon="question",
            option_1="Eliminar 1",
            option_2="Eliminar todo",
            option_3="Cancelar"
        )

        respuesta = msg.get()

        # --- OPCIÓN 1: Eliminar solo una unidad ---
        if respuesta == "Eliminar 1":
            eliminado = self.pedido.eliminar_menu(nombre)
            if eliminado:
                try:
                    self.menu_crud.restaurar_stock(self.db_session, menu_orm, 1)
                except Exception as e:
                    self.db_session.rollback()
                    CTkMessagebox(title="Error", message=f"No se pudo devolver el stock: {e}", icon="warning")

        # --- OPCIÓN 2: Eliminar todo el ítem ---
        elif respuesta == "Eliminar todo":
            # Buscar cantidad total del pedido actual
            item_pedido = next((m for m in self.pedido.menus if m.nombre == nombre), None)
            if item_pedido:
                cantidad = item_pedido.cantidad
                self.pedido.menus.remove(item_pedido)
                try:
                    self.menu_crud.restaurar_stock(self.db_session, menu_orm, cantidad)
                except Exception as e:
                    self.db_session.rollback()
                    CTkMessagebox(title="Error", message=f"No se pudo devolver el stock: {e}", icon="warning")

        # --- OPCIÓN 3: Cancelar ---
        else:
            return

        # Actualizar la UI
        self.actualizar_treeview_pedido()
        total = self.pedido.calcular_total()
        try:
            self.label_total.configure(text=f"Total: ${total:.2f}")
        except Exception:
            pass

            
    def restaurar_stock_pedido_actual(self):
        """Devuelve el stock de todos los menús que aún están en el pedido."""
        for item_pedido in self.pedido.menus:
            menu_orm = self.menu_crud.get_menu_by_id(self.db_session, item_pedido.id_orm)
            if menu_orm:
                try:
                    self.menu_crud.restaurar_stock(self.db_session, menu_orm, item_pedido.cantidad)
                except Exception:
                    self.db_session.rollback()

    def on_close(self):
        """Restaura el stock reservado y cierra la aplicación."""
        try:
            self.restaurar_stock_pedido_actual()
        except Exception:
            pass
        finally:
            self.destroy()
            
    def cargar_icono_menu(self, ruta_icono):
        """Abre un recurso de imagen local y lo convierte en CTkImage."""
        if not ruta_icono:
            raise FileNotFoundError("ruta de icono vacía")
        path = ruta_icono
        if not os.path.isabs(path):
            path = os.path.join(os.path.dirname(__file__), ruta_icono)
        imagen = Image.open(path).convert('RGBA')
        icono_menu = ctk.CTkImage(imagen, size=(64, 64))
        return icono_menu

if __name__ == "__main__":
    import customtkinter as ctk
    from tkinter import ttk

    ctk.set_appearance_mode("Dark")  
    ctk.set_default_color_theme("green") 
    ctk.set_widget_scaling(1.0) 
    ctk.set_window_scaling(1.3) 

    app = AplicacionConPestanas()

    try:
        style = ttk.Style(app)   
        style.theme_use("clam")
        style.configure("Treeview", 
                        background="#2b2b2b", 
                        foreground="white", 
                        fieldbackground="#2b2b2b", 
                        bordercolor="#4CAF50")
        style.map('Treeview', background=[('selected', '#4CAF50')])
        style.configure("Treeview.Heading", 
                        background="#333333", 
                        foreground="white", 
                        bordercolor="#4CAF50")
    except Exception:
        pass

    app.mainloop()
