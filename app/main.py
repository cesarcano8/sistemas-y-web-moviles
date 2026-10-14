from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles

from app.database import (
    actualizar_producto,
    crear_producto,
    eliminar_producto,
    inicializar_base_datos,
    listar_catalogos,
    listar_productos,
    obtener_producto,
    obtener_ruta_base_datos,
)
from app.schemas import Producto, ProductoEntrada


def crear_app(database_path: str | Path | None = None) -> FastAPI:
    ruta_base_datos = (
        Path(database_path) if database_path is not None else obtener_ruta_base_datos()
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        inicializar_base_datos(ruta_base_datos)
        app.state.database_path = ruta_base_datos
        yield

    app = FastAPI(title="Catálogo de productos", version="1.0.0", lifespan=lifespan)
    app.mount(
        "/static",
        StaticFiles(directory=Path(__file__).parent / "static"),
        name="static",
    )
    registrar_rutas(app)
    return app


def inicio():
    return Response(
        content=(Path(__file__).parent / "static" / "index.html").read_text(),
        media_type="text/html",
        headers={"Cache-Control": "no-cache, must-revalidate"},
    )


def obtener_productos(request: Request) -> list[Producto]:
    return listar_productos(request.app.state.database_path)


def obtener_detalle_producto(id_producto: int, request: Request) -> Producto:
    producto = obtener_producto(request.app.state.database_path, id_producto)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


def obtener_catalogos(request: Request) -> dict[str, list[dict]]:
    return listar_catalogos(request.app.state.database_path)


def agregar_producto(producto: ProductoEntrada, request: Request) -> Producto:
    try:
        return crear_producto(
            request.app.state.database_path,
            producto.model_dump(),
        )
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Nombre de producto duplicado o categoría/proveedor inexistente",
        ) from error


def editar_producto(
    id_producto: int,
    producto: ProductoEntrada,
    request: Request,
) -> Producto:
    try:
        actualizado = actualizar_producto(
            request.app.state.database_path,
            id_producto,
            producto.model_dump(),
        )
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Nombre de producto duplicado o categoría/proveedor inexistente",
        ) from error
    if actualizado is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return actualizado


def borrar_producto(id_producto: int, request: Request) -> Response:
    try:
        eliminado = eliminar_producto(request.app.state.database_path, id_producto)
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar: el producto tiene movimientos asociados",
        ) from error
    if not eliminado:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def registrar_rutas(app: FastAPI):
    app.add_api_route("/", inicio, methods=["GET"], response_class=Response)
    app.add_api_route(
        "/productos",
        obtener_productos,
        methods=["GET"],
        response_model=list[Producto],
    )
    app.add_api_route(
        "/productos/{id_producto}",
        obtener_detalle_producto,
        methods=["GET"],
        response_model=Producto,
    )
    app.add_api_route(
        "/catalogos",
        obtener_catalogos,
        methods=["GET"],
    )
    app.add_api_route(
        "/productos",
        agregar_producto,
        methods=["POST"],
        response_model=Producto,
        status_code=status.HTTP_201_CREATED,
    )
    app.add_api_route(
        "/productos/{id_producto}",
        editar_producto,
        methods=["PUT"],
        response_model=Producto,
    )
    app.add_api_route(
        "/productos/{id_producto}",
        borrar_producto,
        methods=["DELETE"],
        status_code=status.HTTP_204_NO_CONTENT,
    )


app = crear_app()
