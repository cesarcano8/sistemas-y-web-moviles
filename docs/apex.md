# Consultar productos desde Oracle APEX

La aplicación obtiene el catálogo desde este endpoint público:

```text
https://oracleapex.com/ords/proyecto_salsamentaria/productos/lista/
```

No se usa autenticación ni conexión directa a Oracle Database. FastAPI consulta el endpoint y expone los productos a la interfaz mediante `GET /productos`.

## Configuración

La URL anterior es la predeterminada. Si el endpoint cambia, se puede configurar con `APEX_PRODUCTOS_URL` en el entorno o en el archivo `.env`:

```dotenv
APEX_PRODUCTOS_URL=https://oracleapex.com/ords/proyecto_salsamentaria/productos/lista/
```

## Respuesta esperada

APEX devuelve un objeto con los productos en `items` y metadatos de paginación:

```json
{
  "items": [
    {
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
      "estado": "A"
    }
  ],
  "hasMore": false
}
```

La API de la aplicación devuelve el arreglo `items` como respuesta de `GET /productos`. El cliente HTTP del servidor tiene un tiempo límite de 10 segundos; los errores de APEX se devuelven con un estado HTTP de gateway y un mensaje explícito. Actualmente se procesa la página que devuelve el endpoint, que informa `hasMore: false` en la respuesta de prueba.
