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
        filas = conexion.execute(_consulta_productos() + " ORDER BY p.nombre").fetchall()
    return [dict(fila) for fila in filas]


def obtener_producto(ruta: Path, id_producto: int) -> dict | None:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        fila = conexion.execute(
            _consulta_productos() + " WHERE p.id_producto = ?",
            (id_producto,),
        ).fetchone()
    return dict(fila) if fila else None


def listar_catalogos(ruta: Path) -> dict[str, list[dict]]:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        categorias = conexion.execute(
            "SELECT id_categoria, nombre FROM categorias ORDER BY nombre"
        ).fetchall()
        proveedores = conexion.execute(
            "SELECT id_proveedor, nombre FROM proveedores ORDER BY nombre"
        ).fetchall()
    return {
        "categorias": [dict(fila) for fila in categorias],
        "proveedores": [dict(fila) for fila in proveedores],
    }


def crear_producto(ruta: Path, producto: dict) -> dict:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        conexion.execute("PRAGMA foreign_keys = ON")
        cursor = conexion.execute(
            """
            INSERT INTO productos (
                nombre, id_categoria, id_proveedor, unidad, precio_venta,
                stock_actual, stock_minimo, activo
            ) VALUES (
                :nombre, :id_categoria, :id_proveedor, :unidad, :precio_venta,
                :stock_actual, :stock_minimo, :activo
            )
            """,
            {**producto, "activo": int(producto["activo"])},
        )
        id_producto = cursor.lastrowid
    result = obtener_producto(ruta, id_producto)
    if result is None:
        raise RuntimeError("No se pudo volver a leer el producto recién creado")
    return result


def actualizar_producto(ruta: Path, id_producto: int, producto: dict) -> dict | None:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        conexion.execute("PRAGMA foreign_keys = ON")
        cursor = conexion.execute(
            """
            UPDATE productos
            SET nombre = :nombre,
                id_categoria = :id_categoria,
                id_proveedor = :id_proveedor,
                unidad = :unidad,
                precio_venta = :precio_venta,
                stock_actual = :stock_actual,
                stock_minimo = :stock_minimo,
                activo = :activo
            WHERE id_producto = :id_producto
            """,
            {
                **producto,
                "activo": int(producto["activo"]),
                "id_producto": id_producto,
            },
        )
        if cursor.rowcount == 0:
            return None
    return obtener_producto(ruta, id_producto)


def eliminar_producto(ruta: Path, id_producto: int) -> bool:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        conexion.execute("PRAGMA foreign_keys = ON")
        cursor = conexion.execute(
            "DELETE FROM productos WHERE id_producto = ?", (id_producto,)
        )
        return cursor.rowcount > 0


def _consulta_productos() -> str:
    return """
        SELECT p.id_producto, p.nombre,
               p.id_categoria, c.nombre AS categoria,
               p.id_proveedor, pr.nombre AS proveedor,
               p.unidad, p.precio_venta, p.stock_actual, p.stock_minimo,
               p.activo
        FROM productos AS p
        JOIN categorias AS c ON c.id_categoria = p.id_categoria
        JOIN proveedores AS pr ON pr.id_proveedor = p.id_proveedor
    """
