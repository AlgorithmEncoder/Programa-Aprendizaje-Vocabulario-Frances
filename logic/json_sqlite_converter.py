"""
Motor de conversión de vocabulario JSON a SQLite.

Este módulo contiene exclusivamente la lógica de conversión.
No depende de Tkinter ni de ninguna otra interfaz gráfica.

Esto permite utilizar el conversor desde:

- la aplicación gráfica;
- tests automáticos;
- scripts;
- futuras interfaces;
- procesos automatizados.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config.app_config import DB_FOLDER
from data.sqlite_db import SQLiteDB


# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------

ProgressCallback = Callable[[int, int], None]


# ---------------------------------------------------------------------------
# Resultado de una conversión
# ---------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class ConversionResult:
    """
    Resultado de una conversión JSON → SQLite.
    """

    source: Path
    output: Path
    success: bool
    words: int = 0
    error: str | None = None


# ---------------------------------------------------------------------------
# Lectura y validación JSON
# ---------------------------------------------------------------------------

def load_json(
    json_path: str | Path,
) -> dict[str, Any]:
    """
    Carga un archivo JSON.

    Parameters
    ----------
    json_path:
        Ruta del archivo JSON.

    Returns
    -------
    dict
        Datos contenidos en el archivo.

    Raises
    ------
    FileNotFoundError
        Si el archivo no existe.

    ValueError
        Si el JSON no es válido o su estructura es incorrecta.
    """
    path = Path(json_path)

    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"La ruta no corresponde a un archivo: {path}"
        )

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"El archivo JSON no es válido: {error}"
        ) from error

    if not isinstance(data, dict):
        raise ValueError(
            "El contenido principal del JSON debe ser un objeto."
        )

    return data


def validate_words(
    data: dict[str, Any],
) -> list[tuple[str, dict[str, Any]]]:
    """
    Valida y normaliza las palabras contenidas en un JSON.

    Returns
    -------
    list
        Lista de pares ``(palabra, información)``.

    Raises
    ------
    ValueError
        Cuando la estructura no es válida.
    """
    words = data.get("words")

    if words is None:
        raise ValueError(
            "El archivo JSON no contiene la propiedad 'words'."
        )

    if not isinstance(words, dict):
        raise ValueError(
            "La propiedad 'words' debe ser un objeto."
        )

    validated: list[tuple[str, dict[str, Any]]] = []

    for word, info in words.items():
        if not isinstance(word, str):
            raise ValueError(
                "Las palabras deben utilizar texto como clave."
            )

        normalized_word = word.strip()

        if not normalized_word:
            raise ValueError(
                "Se ha encontrado una palabra vacía."
            )

        if not isinstance(info, dict):
            raise ValueError(
                f"Los datos de '{normalized_word}' deben ser un objeto."
            )

        translation = info.get("translation")

        if not isinstance(translation, str):
            raise ValueError(
                (
                    f"La traducción de '{normalized_word}' "
                    "debe ser texto."
                )
            )

        if not translation.strip():
            raise ValueError(
                (
                    f"La palabra '{normalized_word}' "
                    "no tiene una traducción válida."
                )
            )

        validated.append(
            (
                normalized_word,
                info,
            )
        )

    return validated


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

def get_database_path(
    json_path: str | Path,
    output_folder: str | Path = DB_FOLDER,
) -> Path:
    """
    Obtiene la ruta de la base SQLite correspondiente al JSON.

    Example
    -------
    ``vocabulario.json`` → ``vocabulario.sqlite``
    """
    source = Path(json_path)
    output = Path(output_folder)

    return (
        output
        / f"{source.stem}.sqlite"
    ).resolve()


# ---------------------------------------------------------------------------
# Conversión
# ---------------------------------------------------------------------------

def json_to_sqlite(
    json_path: str | Path,
    output_folder: str | Path = DB_FOLDER,
    *,
    overwrite: bool = False,
    progress_callback: ProgressCallback | None = None,
) -> ConversionResult:
    """
    Convierte un archivo JSON a SQLite.

    Parameters
    ----------
    json_path:
        Archivo JSON de origen.

    output_folder:
        Carpeta donde se creará la base.

    overwrite:
        Permite sustituir una base existente.

    progress_callback:
        Función opcional llamada después de cada palabra.

        Recibe:

        ``processed, total``

    Returns
    -------
    ConversionResult
        Información completa sobre el resultado.
    """
    source = Path(json_path).resolve()

    output = get_database_path(
        source,
        output_folder,
    )

    backup: Path | None = None

    try:
        # ---------------------------------------------------------------
        # Cargar y validar
        # ---------------------------------------------------------------

        data = load_json(source)
        words = validate_words(data)

        # ---------------------------------------------------------------
        # Preparar destino
        # ---------------------------------------------------------------

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if output.exists():

            if not overwrite:
                return ConversionResult(
                    source=source,
                    output=output,
                    success=False,
                    error=(
                        "La base de datos ya existe y "
                        "no se ha autorizado sobrescribirla."
                    ),
                )

            # Crear copia de seguridad.
            backup = output.with_suffix(
                output.suffix + ".bak"
            )

            if backup.exists():
                backup.unlink()

            shutil.copy2(
                output,
                backup,
            )

            output.unlink()

        # ---------------------------------------------------------------
        # Crear base
        # ---------------------------------------------------------------

        total = len(words)
        processed = 0

        with SQLiteDB(
            db_path=output,
        ) as db:

            for word, info in words:

                added = db.add_word(
                    word,
                    info["translation"],
                    commit=False,
                )

                # La base recién creada no debería tener la palabra,
                # pero esta comprobación hace la operación más robusta.
                if added:
                    fields = (
                        "estado",
                        "aciertos_aprendizaje",
                        "intentos_aprendizaje",
                        "sesiones_superadas",
                        "correct",
                        "incorrect",
                        "streak",
                        "interval",
                        "last_seen",
                    )

                    updates = {
                        field: info[field]
                        for field in fields
                        if field in info
                    }

                    if updates:
                        db.update_word(
                            word,
                            commit=False,
                            **updates,
                        )

                processed += 1

                if progress_callback is not None:
                    progress_callback(
                        processed,
                        total,
                    )

            db.commit()

        # ---------------------------------------------------------------
        # Conversión correcta
        # ---------------------------------------------------------------

        if backup is not None and backup.exists():
            backup.unlink()

        return ConversionResult(
            source=source,
            output=output,
            success=True,
            words=total,
        )

    except Exception as error:
        # ---------------------------------------------------------------
        # Recuperación
        # ---------------------------------------------------------------

        try:
            if output.exists():
                output.unlink()
        except OSError:
            pass

        if backup is not None and backup.exists():
            try:
                shutil.move(
                    backup,
                    output,
                )
            except OSError:
                pass

        return ConversionResult(
            source=source,
            output=output,
            success=False,
            error=str(error),
        )