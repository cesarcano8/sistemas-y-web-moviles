from contextlib import closing
import os
from pathlib import Path
import sqlite3


def obtener_ruta_base_datos() -> Path:
    return Path(os.getenv("DATABASE_PATH", "data/productos.db"))


def obtener_ruta_esquema() -> Path:
    return Path(__file__).parent.parent / "sql" / "esquema.sql"


def inicializar_base_datos(ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        conexion.execute("PRAGMA foreign_keys = ON")
        conexion.row_factory = sqlite3.Row
        columnas = {
            fila["name"]
            for fila in conexion.execute("PRAGMA table_info(productos)")
        }
        columnas_modelo = {"unidad", "stock_actual", "activo"}
        if columnas and not columnas_modelo.issubset(columnas):
            cantidad = conexion.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
            if cantidad:
                raise RuntimeError(
                    "La base de datos contiene productos del esquema anterior. "
                    "Haz una copia de data/productos.db y migra esos registros "
                    "antes de iniciar la aplicación."
                )
            conexion.execute("DROP TABLE productos")

        script_esquema = obtener_ruta_esquema().read_text(encoding="utf-8")
        conexion.executescript(script_esquema)


def listar_productos(ruta: Path) -> list[dict]:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        filas = conexion.execute(
            """
            SELECT p.id_producto, p.nombre,
                   c.nombre AS categoria, pr.nombre AS proveedor,
                   p.unidad, p.precio_venta, p.stock_actual, p.stock_minimo,
                   p.activo
            FROM productos AS p
            JOIN categorias AS c ON c.id_categoria = p.id_categoria
            JOIN proveedores AS pr ON pr.id_proveedor = p.id_proveedor
            WHERE p.activo = 1
            ORDER BY p.nombre
            """
        ).fetchall()
    return [dict(fila) for fila in filas]
