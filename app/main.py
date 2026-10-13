from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, Response
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from app.apex import CatalogoProductos, ErrorApex
from app.schemas import Producto

APEX_PRODUCTOS_URL = (
    "https://oracleapex.com/ords/proyecto_salsamentaria/productos/lista/"
)


def crear_app(catalogo: CatalogoProductos | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        cliente_http = None
        if catalogo is not None:
            app.state.catalogo = catalogo
        else:
            url = os.getenv("APEX_PRODUCTOS_URL", APEX_PRODUCTOS_URL)
            cliente_http = httpx.Client(timeout=10)
            app.state.catalogo = CatalogoProductos(url, cliente_http)

        try:
            yield
        finally:
            if cliente_http is not None:
                cliente_http.close()

    app = FastAPI(title="Catálogo de productos", version="1.0.0", lifespan=lifespan)

    @app.exception_handler(ErrorApex)
    async def manejar_error_apex(_request: Request, error: ErrorApex):
        del _request
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": str(error)},
        )

    app.mount(
        "/static",
        StaticFiles(directory=Path(__file__).parent / "static"),
        name="static",
    )
    registrar_rutas(app)
    return app


def obtener_catalogo(request: Request) -> CatalogoProductos:
    return request.app.state.catalogo


Catalogo = Annotated[CatalogoProductos, Depends(obtener_catalogo)]


def inicio():
    return Response(
        content=(Path(__file__).parent / "static" / "index.html").read_text(),
        media_type="text/html",
    )


def obtener_productos(catalogo: Catalogo):
    try:
        return [Producto.model_validate(producto) for producto in catalogo.listar()]
    except ValidationError as error:
        raise ErrorApex("APEX devolvió un producto con campos inválidos") from error


def registrar_rutas(app: FastAPI):
    app.add_api_route("/", inicio, methods=["GET"], response_class=Response)
    app.add_api_route(
        "/productos",
        obtener_productos,
        methods=["GET"],
        response_model=list[Producto],
    )


app = crear_app()
