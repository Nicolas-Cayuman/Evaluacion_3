"""graficos.py

Funciones utilitarias para obtener datos agregados desde el ORM y
renderizarlos en gráficos usando Matplotlib. Mantiene desacoplada la
lógica estadística de la interfaz principal.
"""
from typing import List, Tuple, Callable, Optional
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def render_bar_chart(parent, etiquetas: List[str], valores: List[float], titulo: str, xlabel: str, ylabel: str) -> FigureCanvasTkAgg:
    """
    Crea un gráfico de barras genérico y lo monta dentro de `parent`.
    Devuelve el canvas para que la UI pueda controlarlo.
    """
    figure = Figure(figsize=(6, 4), dpi=100)
    ax = figure.add_subplot(111)
    ax.bar(etiquetas, valores, color="#4CAF50")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(titulo)
    ax.tick_params(axis="x", rotation=45, labelsize=9)
    figure.tight_layout()

    canvas = FigureCanvasTkAgg(figure, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(expand=True, fill="both")
    return canvas


def obtener_datos_ventas_por_cliente(pedido_crud, db_session) -> Tuple[List[str], List[float], str, str, str]:
    """Devuelve etiquetas y valores para el gráfico de ventas por cliente."""
    datos = pedido_crud.get_totales_por_cliente(db_session)
    etiquetas = [fila[0] if fila[0] else "Sin Cliente" for fila in datos]
    valores = [float(fila[1] or 0.0) for fila in datos]
    return etiquetas, valores, "Ventas por cliente", "Cliente", "Total vendido ($)"


def obtener_datos_ventas_por_fecha(pedido_crud, db_session, periodo: str = "day") -> Tuple[List[str], List[float], str, str, str]:
    """Agrupa las ventas por fecha usando el periodo deseado (día, semana, mes)."""
    datos = pedido_crud.get_totales_por_fecha(db_session, periodo=periodo)
    etiquetas = [fila[0] for fila in datos]
    valores = [float(fila[1] or 0.0) for fila in datos]
    return etiquetas, valores, "Ventas por fecha", "Fecha", "Total vendido ($)"


def obtener_datos_menus_mas_vendidos(detalle_crud, db_session) -> Tuple[List[str], List[float], str, str, str]:
    """Entrega la cantidad vendida por cada menú para graficar top sellers."""
    datos = detalle_crud.get_totales_por_menu(db_session)
    etiquetas = [fila[0] for fila in datos]
    valores = [float(fila[1] or 0.0) for fila in datos]
    return etiquetas, valores, "Menús más vendidos", "Menú", "Cantidad vendida"


def obtener_datos_consumo_ingredientes(detalle_crud, db_session) -> Tuple[List[str], List[float], str, str, str]:
    """Calcula el uso acumulado de ingredientes según pedidos registrados."""
    datos = detalle_crud.get_consumo_ingredientes(db_session)
    etiquetas = [fila[0] for fila in datos]
    valores = [float(fila[1] or 0.0) for fila in datos]
    return etiquetas, valores, "Consumo de ingredientes", "Ingrediente", "Cantidad utilizada"


def resolver_dataset(tipo: str, pedido_crud, detalle_crud, db_session, periodo_fecha: str = "Diario") -> Optional[Tuple[List[str], List[float], str, str, str]]:
    """
    Retorna la tupla (etiquetas, valores, título, xlabel, ylabel) para el tipo de gráfico solicitado.
    Si el tipo no existe se devuelve None.
    """
    mapa_periodos = {
        "Diario": "day",
        "Semanal": "week",
        "Mensual": "month",
    }
    periodo_sql = mapa_periodos.get(periodo_fecha, "day")

    mapping: dict[str, Callable[[], Tuple[List[str], List[float], str, str, str]]] = {
        "Ventas por Cliente": lambda: obtener_datos_ventas_por_cliente(pedido_crud, db_session),
        "Ventas por Fecha": lambda: obtener_datos_ventas_por_fecha(pedido_crud, db_session, periodo=periodo_sql),
        "Menús más Vendidos": lambda: obtener_datos_menus_mas_vendidos(detalle_crud, db_session),
        "Uso de Ingredientes": lambda: obtener_datos_consumo_ingredientes(detalle_crud, db_session),
    }
    resolver = mapping.get(tipo)
    return resolver() if resolver else None
