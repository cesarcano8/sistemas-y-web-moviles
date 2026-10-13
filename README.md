# Catálogo de productos con FastAPI y Docker

Aplicación web de solo lectura para consultar los productos publicados por Oracle APEX. FastAPI consume el endpoint público y presenta el inventario en una tabla adaptable.

## Componentes

- FastAPI y Pydantic: API y validación de la respuesta.
- Oracle APEX/ORDS: endpoint HTTP público de productos, sin autenticación.
- Bootstrap: interfaz web adaptable a móvil y escritorio.
- Docker Compose: ejecuta la aplicación.
- pytest y httpx: pruebas HTTP de la API.

## Requisitos

- Python 3.11 o superior, o Docker.

## Ejecutar localmente

1. Crear un entorno virtual e instalar dependencias:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Iniciar la aplicación:

   ```bash
   uvicorn app.main:app --reload
   ```

3. Abrir `http://localhost:8000` para ver el catálogo o `/docs` para la documentación interactiva.

## Ejecutar con Docker

```bash
docker compose up --build
```

Abre `http://localhost:8000` para ver el catálogo y `http://localhost:8000/docs` para la documentación interactiva. Bootstrap se carga desde jsDelivr y requiere acceso a internet desde el navegador. El servidor también necesita acceso al endpoint de APEX.

## Configurar APEX

La URL del endpoint de prueba ya está configurada como predeterminada. Para cambiarla, copia `.env.example` a `.env` y modifica `APEX_PRODUCTOS_URL`. No se requiere token ni credenciales de base de datos. Consulta [`docs/apex.md`](docs/apex.md) para el contrato de respuesta.

## Probar

```bash
python -m pytest
```

Las pruebas simulan la respuesta HTTP de APEX; no necesitan una base de datos ni acceso a internet.

## Ruta de la API

| Método | Ruta | Acción |
| --- | --- | --- |
| GET | `/productos` | Listar los productos recibidos de APEX |

La guía [`docs/apex.md`](docs/apex.md) describe la integración con el endpoint de Oracle APEX/ORDS.
