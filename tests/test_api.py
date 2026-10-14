from contextlib import closing
import sqlite3

from fastapi.testclient import TestClient
import pytest

from app.database import inicializar_base_datos, obtener_ruta_esquema
from app.ejecutar_sql import ejecutar_script
from app.main import crear_app


def test_inicio_y_archivos_estaticos(tmp_path):
    with TestClient(crear_app(tmp_path / "productos.db")) as cliente:
        respuesta = cliente.get("/")
        javascript = cliente.get("/static/app.js")

    assert respuesta.status_code == 200
    assert "Catálogo de productos" in respuesta.text
    assert "lista-productos" in respuesta.text
    assert respuesta.headers["content-type"].startswith("text/html")
    assert respuesta.headers["cache-control"] == "no-cache, must-revalidate"
    assert "/static/app.js?v=2" in respuesta.text
    assert javascript.status_code == 200
    assert 'solicitar("/productos")' in javascript.text
    assert "producto.categoria" in javascript.text
    assert "producto.stock_actual" in javascript.text


def test_base_nueva_crea_seis_tablas_y_devuelve_lista_vacia(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        respuesta = cliente.get("/productos")

    assert respuesta.status_code == 200
    assert respuesta.json() == []
    with closing(sqlite3.connect(ruta_base_datos)) as conexion:
        tablas = {
            fila[0]
            for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {"roles", "usuarios", "categorias", "proveedores", "productos", "movimientos"} <= tablas


def test_script_de_datos_sql_alimenta_la_api_desde_sqlite(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ruta_datos = obtener_ruta_esquema().parent / "productos.sql"
    ejecutar_script(ruta_datos, ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        respuesta = cliente.get("/productos")

    assert respuesta.status_code == 200
    productos = respuesta.json()
    assert len(productos) == 8
    queso = next(producto for producto in productos if producto["nombre"] == "Queso campesino")
    assert queso == {
        "id_producto": 4,
        "nombre": "Queso campesino",
        "categoria": "Quesos",
        "proveedor": "Lácteos La Pradera",
        "unidad": "KG",
        "precio_venta": 24000,
        "stock_actual": 15.75,
        "stock_minimo": 6,
        "activo": True,
    }


def test_claves_foraneas_rechazan_categoria_inexistente(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ruta_script = tmp_path / "producto_invalido.sql"
    ruta_script.write_text(
        """
        INSERT INTO productos (
            nombre, id_categoria, id_proveedor, unidad, precio_venta
        ) VALUES ('Producto inválido', 99, 99, 'UND', 1000);
        """,
        encoding="utf-8",
    )

    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        ejecutar_script(ruta_script, ruta_base_datos)


def test_migra_tabla_antigua_vacia(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    with sqlite3.connect(ruta_base_datos) as conexion:
        conexion.execute(
            """
            CREATE TABLE productos (
                id_producto INTEGER PRIMARY KEY,
                codigo TEXT NOT NULL,
                nombre TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                id_categoria INTEGER NOT NULL,
                id_proveedor INTEGER NOT NULL,
                precio_compra REAL NOT NULL,
                precio_venta REAL NOT NULL,
                stock INTEGER NOT NULL,
                stock_minimo INTEGER NOT NULL,
                estado TEXT NOT NULL
            )
            """
        )

    inicializar_base_datos(ruta_base_datos)
    with closing(sqlite3.connect(ruta_base_datos)) as conexion:
        columnas = {
            fila[1] for fila in conexion.execute("PRAGMA table_info(productos)")
        }

    assert {"unidad", "stock_actual", "activo"} <= columnas


def test_migracion_no_descarta_productos_de_la_tabla_antigua(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    with sqlite3.connect(ruta_base_datos) as conexion:
        conexion.execute(
            "CREATE TABLE productos (id_producto INTEGER PRIMARY KEY, unidad TEXT)"
        )
        conexion.execute("INSERT INTO productos (id_producto, unidad) VALUES (1, 'KG')")

    with pytest.raises(RuntimeError, match="contiene productos del esquema anterior"):
        inicializar_base_datos(ruta_base_datos)
