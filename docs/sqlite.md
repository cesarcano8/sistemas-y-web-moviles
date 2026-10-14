# Esquema y datos SQLite

La aplicación usa SQLite como fuente local y no consulta Oracle APEX/ORDS al mostrar el catálogo. El archivo persistente está en `data/productos.db`.

El script original estaba escrito para Oracle. No se puede ejecutar directamente en SQLite: Oracle `NUMBER`, `VARCHAR2`, columnas `IDENTITY`, `SYSDATE` y los `ALTER TABLE ... ADD CONSTRAINT` no son compatibles tal cual. El esquema convertido está en `sql/esquema.sql`; la aplicación lo ejecuta al arrancar.

El esquema contiene seis tablas: `roles`, `usuarios`, `categorias`, `proveedores`, `productos` y `movimientos`. Las claves foráneas y restricciones `CHECK` se definen junto a sus tablas y SQLite las valida.

## Cargar datos

`sql/productos.sql` contiene datos de ejemplo compatibles con SQLite. Para cargar tus propios datos, edita sus `INSERT`, respetando las relaciones: roles antes de usuarios, categorías y proveedores antes de productos, y productos/usuarios antes de movimientos. El archivo actual incluye productos demostrativos; reemplázalos por los registros reales antes de ejecutar si no quieres conservarlos.

Los valores `HASH_ADMIN` y `HASH_VENDEDOR` son marcadores, no contraseñas cifradas. Esta aplicación aún no implementa inicio de sesión.

Ejecuta el archivo **una sola vez**. Desde PowerShell, en la raíz del proyecto y con Docker Desktop activo:

```powershell
docker compose up -d
docker compose exec api python -m app.ejecutar_sql /app/sql/productos.sql
```

La carpeta `sql/` se monta como solo lectura dentro del contenedor y el ejecutor aplica el archivo a `/data/productos.db`. La carpeta local `data/` conserva la base aunque el contenedor se detenga o se reconstruya. Recarga `http://localhost:8000` para ver el catálogo.

Al volver a ejecutar el script de ejemplo, las claves primarias y restricciones únicas producirán un error de duplicado. Para editar registros existentes, usa `UPDATE`; para agregar, usa IDs nuevos. Los IDs de los ejemplos están fijados para que las relaciones de movimientos coincidan.

## Diferencias con el modelo anterior de la API

El catálogo actual usa las columnas que realmente define el modelo de inventario: nombre, categoría, proveedor, unidad, precio de venta, existencias, mínimo y activo. Ya no espera `codigo`, `descripcion` ni `precio_compra`, campos que no existen en la tabla Oracle del archivo original.

## Operaciones de productos

La página principal permite crear, listar, editar y eliminar productos. La API expone además `GET /productos/{id}`, `POST /productos`, `PUT /productos/{id}` y `DELETE /productos/{id}`. Los campos categoría y proveedor se eligen de los catálogos existentes; precio debe ser mayor que cero y stock no puede ser negativo.

Un producto asociado a movimientos no se puede eliminar, para conservar el historial. En ese caso la API devuelve `409 Conflict`; se puede editar para marcarlo inactivo.

La aplicación aún no tiene autenticación. Limita su uso a un entorno local o de confianza.
