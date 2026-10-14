import argparse
from contextlib import closing
from pathlib import Path
import sqlite3

from app.database import inicializar_base_datos, obtener_ruta_base_datos


def ejecutar_script(ruta_script: Path, ruta_base_datos: Path | None = None) -> None:
    contenido = ruta_script.read_text(encoding="utf-8")
    ruta = ruta_base_datos or obtener_ruta_base_datos()
    inicializar_base_datos(ruta)
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        conexion.execute("PRAGMA foreign_keys = ON")
        conexion.executescript(contenido)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ejecuta un archivo SQL contra la base SQLite del catálogo."
    )
    parser.add_argument("archivo", type=Path, help="Archivo SQL que se ejecutará")
    argumentos = parser.parse_args()

    try:
        ejecutar_script(argumentos.archivo)
    except (OSError, RuntimeError, sqlite3.Error) as error:
        parser.error(f"No se pudo ejecutar el archivo SQL: {error}")

    print(f"Script ejecutado: {argumentos.archivo}")


if __name__ == "__main__":
    main()
