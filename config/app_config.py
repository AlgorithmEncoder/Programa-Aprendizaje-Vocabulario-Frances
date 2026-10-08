"""
Configuración global de la aplicación.

Este módulo centraliza las rutas que utiliza la aplicación para almacenar
sus datos de ejecución.

La ubicación depende de cómo se esté ejecutando el programa:

- En desarrollo: se utiliza la carpeta raíz del proyecto.
- En una aplicación empaquetada: se utiliza una carpeta específica dentro
  de Documentos del usuario.

Esto permite mantener separado el código de la aplicación de los datos
generados durante su uso.
"""

from __future__ import annotations

import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Información de la aplicación
# ---------------------------------------------------------------------------

APP_NAME = "AprenderFrances"


# ---------------------------------------------------------------------------
# Directorio base
# ---------------------------------------------------------------------------

def get_base_dir() -> Path:
    """
    Devuelve el directorio base donde se almacenarán los datos de la
    aplicación.

    Durante el desarrollo se utiliza la raíz del proyecto.

    Cuando la aplicación se ejecuta como un programa empaquetado
    (por ejemplo, mediante PyInstaller), los datos se almacenan en:

        ~/Documents/AprenderFrances

    Returns
    -------
    Path
        Directorio base de la aplicación.
    """
    if getattr(sys, "frozen", False):
        return Path.home() / "Documents" / APP_NAME

    # app_config.py está dentro de:
    # proyecto/config/app_config.py
    #
    # Por tanto:
    # parent     -> config/
    # parent[1]  -> raíz del proyecto
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()


# ---------------------------------------------------------------------------
# Directorios de datos
# ---------------------------------------------------------------------------

DB_FOLDER = BASE_DIR / "databases"
RESULT_FOLDER = BASE_DIR / "results"


# ---------------------------------------------------------------------------
# Inicialización del sistema de archivos
# ---------------------------------------------------------------------------

def ensure_app_directories() -> None:
    """
    Crea los directorios necesarios para la ejecución de la aplicación.

    La función es segura de ejecutar varias veces gracias a
    ``exist_ok=True``.
    """
    DB_FOLDER.mkdir(parents=True, exist_ok=True)
    RESULT_FOLDER.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Inicialización
# ---------------------------------------------------------------------------

ensure_app_directories()