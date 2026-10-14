from pydantic import BaseModel


class Producto(BaseModel):
    id_producto: int
    nombre: str
    categoria: str
    proveedor: str
    unidad: str
    precio_venta: float
    stock_actual: float
    stock_minimo: float
    activo: bool
