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
    assert "/static/app.js?v=5" in respuesta.text
    assert 'id="dialogo-producto"' in respuesta.text
    assert 'id="abrir-formulario"' in respuesta.text
    assert javascript.status_code == 200
    assert 'solicitar("/productos")' in javascript.text
    assert "producto.categoria" in javascript.text
    assert "producto.stock_actual" in javascript.text
    assert 'method: esEdicion ? "PUT" : "POST"' in javascript.text
    assert "dialogoProducto.showModal()" in javascript.text


def test_base_nueva_crea_seis_tablas_y_catalogos_vacios(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        respuesta = cliente.get("/productos")
        catalogos = cliente.get("/catalogos")

    assert respuesta.status_code == 200
    assert respuesta.json() == []
    assert catalogos.json() == {"categorias": [], "proveedores": []}
    with closing(sqlite3.connect(ruta_base_datos)) as conexion:
        tablas = {
            fila[0]
            for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {"roles", "usuarios", "categorias", "proveedores", "productos", "movimientos"} <= tablas


def test_script_de_datos_sql_alimenta_catalogo_y_catalogos(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ruta_datos = obtener_ruta_esquema().parent / "productos.sql"
    ejecutar_script(ruta_datos, ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        respuesta = cliente.get("/productos")
        catalogos = cliente.get("/catalogos")

    assert respuesta.status_code == 200
    productos = respuesta.json()
    assert len(productos) == 8
    assert len(catalogos.json()["categorias"]) == 4
    assert len(catalogos.json()["proveedores"]) == 3
    queso = next(producto for producto in productos if producto["nombre"] == "Queso campesino")
    assert queso == {
        "id_producto": 4,
        "nombre": "Queso campesino",
        "id_categoria": 2,
        "categoria": "Quesos",
        "id_proveedor": 2,
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


def test_crud_crear_ver_editar_y_eliminar_producto(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)
    producto = {
        "nombre": "Producto CRUD",
        "id_categoria": 1,
        "id_proveedor": 1,
        "unidad": "UND",
        "precio_venta": 1000,
        "stock_actual": 8,
        "stock_minimo": 2,
        "activo": True,
    }

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        creado = cliente.post("/productos", json=producto)
        id_producto = creado.json()["id_producto"]
        detalle = cliente.get(f"/productos/{id_producto}")
        actualizado = cliente.put(
            f"/productos/{id_producto}",
            json={**producto, "nombre": "Producto actualizado", "stock_actual": 5},
        )
        eliminacion = cliente.delete(f"/productos/{id_producto}")
        detalle_borrado = cliente.get(f"/productos/{id_producto}")

    assert creado.status_code == 201
    assert creado.json()["categoria"] == "Embutidos"
    assert creado.json()["proveedor"] == "Cárnicos del Valle"
    assert detalle.status_code == 200
    assert actualizado.status_code == 200
    assert actualizado.json()["nombre"] == "Producto actualizado"
    assert actualizado.json()["stock_actual"] == 5
    assert eliminacion.status_code == 204
    assert detalle_borrado.status_code == 404


def test_no_se_puede_eliminar_producto_con_movimientos(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        respuesta = cliente.delete("/productos/1")
        producto = cliente.get("/productos/1")

    assert respuesta.status_code == 409
    assert "movimientos asociados" in respuesta.json()["detail"]
    assert producto.status_code == 200


def test_validaciones_de_producto_y_referencias(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)
    producto = {
        "nombre": "Producto inválido",
        "id_categoria": 99,
        "id_proveedor": 99,
        "unidad": "UND",
        "precio_venta": 0,
        "stock_actual": 0,
        "stock_minimo": 0,
        "activo": True,
    }

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        invalido = cliente.post("/productos", json=producto)
        referencia_invalida = cliente.post(
            "/productos",
            json={**producto, "nombre": "Producto sin referencia", "precio_venta": 1},
        )
        inexistente = cliente.put("/productos/9999", json={
            **producto,
            "id_categoria": 1,
            "id_proveedor": 1,
            "precio_venta": 1,
        })

    assert invalido.status_code == 422
    assert referencia_invalida.status_code == 409
    assert inexistente.status_code == 404
