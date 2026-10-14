from typing import Literal

from pydantic import BaseModel, Field


class Producto(BaseModel):
    id_producto: int
    nombre: str
    id_categoria: int
    categoria: str
    id_proveedor: int
    proveedor: str
    unidad: Literal["KG", "UND"]
    precio_venta: float
    stock_actual: float
    stock_minimo: float
    activo: bool


class ProductoEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    id_categoria: int = Field(gt=0)
    id_proveedor: int = Field(gt=0)
    unidad: Literal["KG", "UND"]
    precio_venta: float = Field(gt=0)
    stock_actual: float = Field(ge=0)
    stock_minimo: float = Field(ge=0)
    activo: bool = True
