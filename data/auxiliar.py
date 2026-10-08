"""
Funciones auxiliares para trabajar con las bases de datos de vocabulario.

Este módulo actúa como una capa de compatibilidad entre la aplicación
y SQLite cuando necesitamos representar una base de datos completa como
un diccionario de Python.

La lógica SQL permanece centralizada en ``SQLiteDB``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from data.sqlite_db import SQLiteDB


def load_database_sqlite(
    db_name: str | Path,
) -> dict[str, Any]:
    """
    Carga una base de datos SQLite en una estructura de Python.

    El resultado mantiene el formato general utilizado por la aplicación:

    {
        "name": "frances",
        "words": {
            "bonjour": {
                ...
            },
            "chat": {
                ...
            }
        }
    }

    Parameters
    ----------
    db_name:
        Nombre o ruta de la base de datos.

    Returns
    -------
    dict
        Datos completos de la base de vocabulario.
    """
    with SQLiteDB(db_name=db_name) as db:
        rows = db.get_all_words()

        words: dict[str, dict[str, Any]] = {}

        for row in rows:
            word = row["word"]
            words[word] = row

        return {
            "name": db.db_path.stem,
            "words": words,
        }


def update_word_sqlite(
    db_name: str | Path,
    words_data: dict[str, dict[str, Any]],
) -> None:
    """
    Actualiza una colección de palabras en una base SQLite.

    Solo se utilizan los campos que ``SQLiteDB`` permite modificar.
    Los campos propios de la representación en memoria, como ``word``,
    se ignoran.

    Parameters
    ----------
    db_name:
        Nombre o ruta de la base de datos.

    words_data:
        Diccionario con las palabras y sus datos.
    """
    if not isinstance(words_data, dict):
        raise TypeError(
            "words_data debe ser un diccionario."
        )

    with SQLiteDB(db_name=db_name) as db:
        allowed_fields = SQLiteDB.ALLOWED_UPDATE_FIELDS

        for word, info in words_data.items():
            if not isinstance(info, dict):
                continue

            updates = {
                key: value
                for key, value in info.items()
                if key in allowed_fields
            }

            if not updates:
                continue

            db.update_word(
                word,
                **updates,
            )


def save_database_sqlite(
    db_name: str | Path,
    words_data: dict[str, dict[str, Any]],
) -> None:
    """
    Guarda los cambios de una base SQLite.

    Actualmente es un alias semántico de ``update_word_sqlite``.
    Se mantiene separado para que la intención del código que lo utiliza
    sea más clara.
    """
    update_word_sqlite(
        db_name,
        words_data,
    )