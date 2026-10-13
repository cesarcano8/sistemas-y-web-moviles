import httpx
from fastapi.testclient import TestClient

from app.apex import CatalogoProductos
from app.main import APEX_PRODUCTOS_URL, crear_app


PRODUCTO = {
    "id_producto": 1,
    "codigo": "QUES-001",
    "nombre": "Queso campesino",
    "descripcion": "Queso campesino de prueba",
    "id_categoria": 1,
    "id_proveedor": 1,
    "precio_compra": 12000,
    "precio_venta": 15000,
    "stock": 27,
    "stock_minimo": 5,
    "estado": "A",
}


def crear_app_pruebas(cliente_http: httpx.Client) -> TestClient:
    catalogo = CatalogoProductos(APEX_PRODUCTOS_URL, cliente_http)
    return TestClient(crear_app(catalogo=catalogo))


def test_inicio_y_archivos_estaticos():
    def responder(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        return httpx.Response(200, json={"items": []})

    with httpx.Client(
        transport=httpx.MockTransport(responder)
    ) as cliente_http:
        with crear_app_pruebas(cliente_http) as cliente:
            respuesta = cliente.get("/")
            javascript = cliente.get("/static/app.js")

    assert respuesta.status_code == 200
    assert "Catálogo de productos" in respuesta.text
    assert "lista-productos" in respuesta.text
    assert respuesta.headers["content-type"].startswith("text/html")
    assert javascript.status_code == 200
    assert 'solicitar("/productos")' in javascript.text


def test_listar_productos_consulta_apex_sin_autenticacion():
    productos = [PRODUCTO, {**PRODUCTO, "id_producto": 2, "codigo": "QUES-002"}]

    def responder(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == APEX_PRODUCTOS_URL
        assert "Authorization" not in request.headers
        return httpx.Response(
            200,
            json={
                "items": productos,
                "hasMore": False,
                "limit": 25,
                "offset": 0,
                "count": len(productos),
            },
        )

    with httpx.Client(transport=httpx.MockTransport(responder)) as cliente_http:
        with crear_app_pruebas(cliente_http) as cliente:
            respuesta = cliente.get("/productos")

    assert respuesta.status_code == 200
    assert respuesta.json() == productos


def test_respuesta_apex_sin_items_devuelve_error_gateway():
    def responder(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL(APEX_PRODUCTOS_URL)
        return httpx.Response(200, json={"hasMore": False})

    with httpx.Client(
        transport=httpx.MockTransport(responder)
    ) as cliente_http:
        with crear_app_pruebas(cliente_http) as cliente_http_api:
            respuesta = cliente_http_api.get("/productos")

    assert respuesta.status_code == 502
    assert respuesta.json() == {
        "detail": "APEX debe devolver una lista de productos en 'items'"
    }


def test_error_http_de_apex_se_expone_como_error_gateway():
    def responder(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == httpx.URL(APEX_PRODUCTOS_URL)
        return httpx.Response(503)

    with httpx.Client(
        transport=httpx.MockTransport(responder)
    ) as cliente_http:
        with crear_app_pruebas(cliente_http) as cliente_http_api:
            respuesta = cliente_http_api.get("/productos")

    assert respuesta.status_code == 502
    assert respuesta.json() == {"detail": "APEX respondió con el estado HTTP 503"}


def test_error_de_conexion_apex_expone_el_motivo():
    def responder(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(
            "[Errno -3] Temporary failure in name resolution",
            request=request,
        )

    with httpx.Client(transport=httpx.MockTransport(responder)) as cliente_http:
        with crear_app_pruebas(cliente_http) as cliente_http_api:
            respuesta = cliente_http_api.get("/productos")

    assert respuesta.status_code == 502
    assert respuesta.json() == {
        "detail": (
            "No fue posible conectarse con APEX: "
            "[Errno -3] Temporary failure in name resolution"
        )
    }


def test_tiempo_de_espera_de_apex_devuelve_gateway_timeout():
    def responder(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    with httpx.Client(transport=httpx.MockTransport(responder)) as cliente_http:
        with crear_app_pruebas(cliente_http) as cliente_http_api:
            respuesta = cliente_http_api.get("/productos")

    assert respuesta.status_code == 504
    assert respuesta.json() == {
        "detail": "Se agotó el tiempo de espera al consultar APEX"
    }
