from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles

from app.database import (
    inicializar_base_datos,
    listar_productos,
    obtener_ruta_base_datos,
)
from app.schemas import Producto


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


def registrar_rutas(app: FastAPI):
    app.add_api_route("/", inicio, methods=["GET"], response_class=Response)
    app.add_api_route(
        "/productos",
        obtener_productos,
        methods=["GET"],
        response_model=list[Producto],
    )


app = crear_app()
