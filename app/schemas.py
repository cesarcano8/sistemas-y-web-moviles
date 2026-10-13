from pydantic import BaseModel


class Producto(BaseModel):
    id_producto: int
    codigo: str
    nombre: str
    descripcion: str
    id_categoria: int
    id_proveedor: int
    precio_compra: float
    precio_venta: float
    stock: int
    stock_minimo: int
    estado: str
