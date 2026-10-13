import httpx


class ErrorApex(Exception):
    def __init__(self, mensaje: str, status_code: int = 502):
        super().__init__(mensaje)
        self.status_code = status_code


class CatalogoProductos:
    def __init__(self, url: str, cliente_http: httpx.Client):
        self.url = url
        self.cliente_http = cliente_http

    def listar(self) -> list[dict]:
        try:
            respuesta = self.cliente_http.get(self.url)
        except httpx.TimeoutException as error:
            raise ErrorApex(
                "Se agotó el tiempo de espera al consultar APEX", 504
            ) from error
        except httpx.ConnectError as error:
            raise ErrorApex(
                f"No fue posible conectarse con APEX: {error}"
            ) from error
        except httpx.HTTPError as error:
            raise ErrorApex("No fue posible comunicarse con APEX") from error

        if not respuesta.is_success:
            raise ErrorApex(
                f"APEX respondió con el estado HTTP {respuesta.status_code}"
            )

        try:
            contenido = respuesta.json()
        except ValueError as error:
            raise ErrorApex("APEX no devolvió un JSON válido") from error

        if not isinstance(contenido, dict) or not isinstance(
            contenido.get("items"), list
        ):
            raise ErrorApex("APEX debe devolver una lista de productos en 'items'")

        productos = contenido["items"]
        if any(not isinstance(producto, dict) for producto in productos):
            raise ErrorApex("APEX devolvió un producto con formato inválido")

        return [
            {str(clave).lower(): valor for clave, valor in producto.items()}
            for producto in productos
        ]
