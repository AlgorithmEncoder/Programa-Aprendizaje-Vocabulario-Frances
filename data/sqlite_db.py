"""
Capa de acceso a SQLite para AprenderFrances.

Esta clase centraliza todas las operaciones con las bases de vocabulario.

Responsabilidades:

- creación y apertura de bases;
- migración de estructuras antiguas;
- consulta de palabras;
- inserción y eliminación;
- actualización;
- estadísticas;
- registro de respuestas;
- gestión del progreso;
- gestión de transacciones.

La interfaz gráfica no debería ejecutar SQL directamente.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from pathlib import Path
from typing import Any

from config.app_config import DB_FOLDER


class SQLiteDB:
    """
    Gestiona una base de datos SQLite de vocabulario.
    """

    TABLE_NAME = "words"

    ALLOWED_UPDATE_FIELDS = {
        "translation",
        "estado",
        "aciertos_aprendizaje",
        "intentos_aprendizaje",
        "sesiones_superadas",
        "correct",
        "incorrect",
        "streak",
        "interval",
        "created_at",
        "last_seen",
    }

    DATABASE_SUFFIXES = {
        ".sqlite",
        ".db",
    }

    DEFAULT_WORD_VALUES = {
        "estado": "nuevo",
        "aciertos_aprendizaje": 0,
        "intentos_aprendizaje": 0,
        "sesiones_superadas": 0,
        "correct": 0,
        "incorrect": 0,
        "streak": 0,
        "interval": 0,
    }

    _INVALID_DATABASE_NAME = re.compile(
        r"""[\\/:*?"<>|]"""
    )

    def __init__(
        self,
        db_name: str | Path | None = None,
        db_path: str | Path | None = None,
    ) -> None:
        """
        Abre o crea una base de datos.

        Parameters
        ----------
        db_name:
            Nombre de la base. Por defecto se busca dentro de ``DB_FOLDER``.

        db_path:
            Ruta completa. Tiene prioridad sobre ``db_name``.
        """
        self.db_path = self._resolve_db_path(
            db_name=db_name,
            db_path=db_path,
        )

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.conn = sqlite3.connect(
            str(self.db_path),
        )

        self.conn.row_factory = sqlite3.Row

        self.conn.execute(
            "PRAGMA foreign_keys = ON"
        )

        self.create_tables()

    # ------------------------------------------------------------------
    # Rutas y nombres
    # ------------------------------------------------------------------

    @classmethod
    def _validate_database_name(
        cls,
        name: str,
    ) -> str:
        """
        Valida un nombre de base de datos.
        """
        if not isinstance(name, str):
            raise TypeError(
                "El nombre de la base debe ser texto."
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "El nombre de la base no puede estar vacío."
            )

        if cls._INVALID_DATABASE_NAME.search(name):
            raise ValueError(
                (
                    "El nombre de la base contiene caracteres "
                    "no permitidos."
                )
            )

        if name in {".", ".."}:
            raise ValueError(
                "El nombre de la base no es válido."
            )

        return name

    @classmethod
    def _filename_from_name(
        cls,
        name: str | Path,
    ) -> str:
        """
        Convierte un nombre de base en nombre de archivo.
        """
        path = Path(name)

        filename = path.name

        if path.suffix.lower() not in cls.DATABASE_SUFFIXES:
            filename = f"{filename}.sqlite"

        return filename

    @classmethod
    def _resolve_db_path(
        cls,
        db_name: str | Path | None,
        db_path: str | Path | None,
    ) -> Path:
        """
        Determina la ruta real de la base de datos.
        """
        if db_path is not None:
            return (
                Path(db_path)
                .expanduser()
                .resolve()
            )

        if db_name is None:
            raise ValueError(
                "Debe proporcionarse db_name o db_path."
            )

        path = Path(db_name)

        # Una ruta explícita con directorio.
        if path.parent != Path("."):
            return (
                path
                .expanduser()
                .resolve()
            )

        filename = cls._filename_from_name(
            db_name,
        )

        return (
            DB_FOLDER / filename
        ).resolve()

    # ------------------------------------------------------------------
    # Gestión global de bases
    # ------------------------------------------------------------------

    @classmethod
    def list_databases(cls) -> list[str]:
        """
        Devuelve los nombres de las bases disponibles.
        """
        DB_FOLDER.mkdir(
            parents=True,
            exist_ok=True,
        )

        names: set[str] = set()

        for suffix in cls.DATABASE_SUFFIXES:
            for path in DB_FOLDER.glob(
                f"*{suffix}"
            ):
                if path.is_file():
                    names.add(
                        path.stem
                    )

        return sorted(
            names,
            key=str.casefold,
        )

    @classmethod
    def exists(
        cls,
        db_name: str | Path,
    ) -> bool:
        """
        Comprueba si existe una base.
        """
        path = cls._resolve_db_path(
            db_name=db_name,
            db_path=None,
        )

        return path.is_file()

    @classmethod
    def create_database(
        cls,
        db_name: str,
    ) -> Path:
        """
        Crea una nueva base de datos.
        """
        db_name = cls._validate_database_name(
            db_name,
        )

        path = cls._resolve_db_path(
            db_name=db_name,
            db_path=None,
        )

        if path.exists():
            raise FileExistsError(
                f"La base ya existe: {path.name}"
            )

        with cls(
            db_path=path,
        ):
            pass

        return path

    # ------------------------------------------------------------------
    # Conexión
    # ------------------------------------------------------------------

    def close(self) -> None:
        """
        Cierra la conexión.
        """
        if self.conn is not None:
            self.conn.close()

    def commit(self) -> None:
        """
        Confirma la transacción actual.
        """
        self.conn.commit()

    def rollback(self) -> None:
        """
        Revierte la transacción actual.
        """
        self.conn.rollback()

    def __enter__(self) -> "SQLiteDB":
        """
        Permite utilizar SQLiteDB como context manager.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        """
        Confirma la transacción si no hubo errores.
        """
        try:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
        finally:
            self.close()

    # ------------------------------------------------------------------
    # Inicialización y migraciones
    # ------------------------------------------------------------------

    def create_tables(self) -> None:
        """
        Crea la tabla principal y migra bases antiguas cuando es necesario.
        """
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS words (
                word TEXT PRIMARY KEY,
                translation TEXT NOT NULL,

                estado TEXT NOT NULL DEFAULT 'nuevo',

                aciertos_aprendizaje INTEGER NOT NULL DEFAULT 0,
                intentos_aprendizaje INTEGER NOT NULL DEFAULT 0,
                sesiones_superadas INTEGER NOT NULL DEFAULT 0,

                correct INTEGER NOT NULL DEFAULT 0,
                incorrect INTEGER NOT NULL DEFAULT 0,

                streak INTEGER NOT NULL DEFAULT 0,
                interval INTEGER NOT NULL DEFAULT 0,

                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                last_seen TEXT
            )
            """
        )

        self._migrate_words_table()

        self.conn.commit()

    def _migrate_words_table(self) -> None:
        """
        Añade columnas que puedan faltar en bases antiguas.
        """
        existing_columns = {
            row["name"]
            for row in self.conn.execute(
                f"PRAGMA table_info({self.TABLE_NAME})"
            ).fetchall()
        }

        migrations = {
            "estado": (
                "TEXT NOT NULL DEFAULT 'nuevo'"
            ),
            "aciertos_aprendizaje": (
                "INTEGER NOT NULL DEFAULT 0"
            ),
            "intentos_aprendizaje": (
                "INTEGER NOT NULL DEFAULT 0"
            ),
            "sesiones_superadas": (
                "INTEGER NOT NULL DEFAULT 0"
            ),
            "correct": (
                "INTEGER NOT NULL DEFAULT 0"
            ),
            "incorrect": (
                "INTEGER NOT NULL DEFAULT 0"
            ),
            "streak": (
                "INTEGER NOT NULL DEFAULT 0"
            ),
            "interval": (
                "INTEGER NOT NULL DEFAULT 0"
            ),
            "created_at": (
                "TEXT"
            ),
            "last_seen": (
                "TEXT"
            ),
        }

        for column, definition in migrations.items():

            if column in existing_columns:
                continue

            self.conn.execute(
                (
                    f"ALTER TABLE {self.TABLE_NAME} "
                    f"ADD COLUMN {column} {definition}"
                )
            )

        # Las bases antiguas no tenían created_at.
        # Aprovechamos last_seen cuando existe y utilizamos la fecha actual
        # como último recurso.
        self.conn.execute(
            """
            UPDATE words
            SET created_at = COALESCE(
                created_at,
                last_seen,
                CURRENT_TIMESTAMP
            )
            WHERE created_at IS NULL
            """
        )

    # ------------------------------------------------------------------
    # Normalización
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_word(
        word: str,
    ) -> str:
        """
        Normaliza una palabra.
        """
        if not isinstance(word, str):
            raise TypeError(
                "La palabra debe ser texto."
            )

        normalized = word.strip()

        if not normalized:
            raise ValueError(
                "La palabra no puede estar vacía."
            )

        return normalized

    @staticmethod
    def _normalize_translation(
        translation: str,
    ) -> str:
        """
        Normaliza una traducción.
        """
        if not isinstance(translation, str):
            raise TypeError(
                "La traducción debe ser texto."
            )

        normalized = translation.strip()

        if not normalized:
            raise ValueError(
                "La traducción no puede estar vacía."
            )

        return normalized

    @staticmethod
    def _today() -> str:
        """
        Fecha actual en formato ISO.
        """
        return date.today().isoformat()

    @staticmethod
    def _now() -> str:
        """
        Fecha y hora actual en formato ISO.
        """
        return datetime.now().isoformat(
            timespec="seconds"
        )

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def get_word(
        self,
        word: str,
    ) -> dict[str, Any] | None:
        """
        Devuelve una palabra completa.
        """
        word = self._normalize_word(word)

        cursor = self.conn.execute(
            """
            SELECT *
            FROM words
            WHERE word = ?
            LIMIT 1
            """,
            (word,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    def get_all_words(
        self,
    ) -> list[dict[str, Any]]:
        """
        Devuelve todas las palabras.
        """
        cursor = self.conn.execute(
            """
            SELECT *
            FROM words
            ORDER BY word COLLATE NOCASE ASC
            """
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    def get_words_by_state(
        self,
        estado: str,
    ) -> list[dict[str, Any]]:
        """
        Devuelve palabras de un estado concreto.
        """
        estado = str(estado).strip()

        if not estado:
            raise ValueError(
                "El estado no puede estar vacío."
            )

        cursor = self.conn.execute(
            """
            SELECT *
            FROM words
            WHERE estado = ?
            ORDER BY word COLLATE NOCASE ASC
            """,
            (estado,),
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    def count_words(self) -> int:
        """
        Devuelve el número total de palabras.
        """
        row = self.conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM words
            """
        ).fetchone()

        return int(
            row["total"]
        )

    # ------------------------------------------------------------------
    # Inserción
    # ------------------------------------------------------------------

    def add_word(
        self,
        word: str,
        translation: str,
        *,
        commit: bool = True,
    ) -> bool:
        """
        Añade una nueva palabra.

        No sustituye una palabra existente. Esto evita perder el progreso
        de aprendizaje accidentalmente.
        """
        word = self._normalize_word(word)
        translation = self._normalize_translation(
            translation
        )

        cursor = self.conn.execute(
            """
            INSERT INTO words (
                word,
                translation,
                estado,
                aciertos_aprendizaje,
                intentos_aprendizaje,
                sesiones_superadas,
                correct,
                incorrect,
                streak,
                interval,
                created_at,
                last_seen
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(word) DO NOTHING
            """,
            (
                word,
                translation,
                self.DEFAULT_WORD_VALUES["estado"],
                self.DEFAULT_WORD_VALUES[
                    "aciertos_aprendizaje"
                ],
                self.DEFAULT_WORD_VALUES[
                    "intentos_aprendizaje"
                ],
                self.DEFAULT_WORD_VALUES[
                    "sesiones_superadas"
                ],
                self.DEFAULT_WORD_VALUES["correct"],
                self.DEFAULT_WORD_VALUES["incorrect"],
                self.DEFAULT_WORD_VALUES["streak"],
                self.DEFAULT_WORD_VALUES["interval"],
                self._now(),
                None,
            ),
        )

        if commit:
            self.conn.commit()

        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Actualización
    # ------------------------------------------------------------------

    def update_word(
        self,
        word: str,
        *,
        commit: bool = True,
        **kwargs: Any,
    ) -> bool:
        """
        Actualiza uno o varios campos de una palabra.

        Solo pueden actualizarse campos presentes en
        ``ALLOWED_UPDATE_FIELDS``.
        """
        word = self._normalize_word(word)

        if not kwargs:
            return False

        invalid_fields = (
            set(kwargs)
            - self.ALLOWED_UPDATE_FIELDS
        )

        if invalid_fields:
            invalid = ", ".join(
                sorted(invalid_fields)
            )

            raise ValueError(
                (
                    "Campos no permitidos para actualizar: "
                    f"{invalid}"
                )
            )

        assignments = ", ".join(
            f"{field} = ?"
            for field in kwargs
        )

        parameters = (
            tuple(kwargs.values())
            + (word,)
        )

        cursor = self.conn.execute(
            f"""
            UPDATE words
            SET {assignments}
            WHERE word = ?
            """,
            parameters,
        )

        if commit:
            self.conn.commit()

        return cursor.rowcount > 0

    def update_words(
        self,
        words_data: Mapping[str, Mapping[str, Any]],
    ) -> int:
        """
        Actualiza múltiples palabras dentro de una única transacción.

        Returns
        -------
        int
            Número de registros actualizados.
        """
        updated = 0

        try:
            for word, info in words_data.items():

                if not isinstance(info, Mapping):
                    continue

                values = {
                    key: value
                    for key, value in info.items()
                    if key in self.ALLOWED_UPDATE_FIELDS
                }

                if not values:
                    continue

                if self.update_word(
                    word,
                    commit=False,
                    **values,
                ):
                    updated += 1

            self.conn.commit()

        except Exception:
            self.conn.rollback()
            raise

        return updated

    # ------------------------------------------------------------------
    # Eliminación
    # ------------------------------------------------------------------

    def delete_word(
        self,
        word: str,
    ) -> bool:
        """
        Elimina una palabra.
        """
        word = self._normalize_word(word)

        cursor = self.conn.execute(
            """
            DELETE FROM words
            WHERE word = ?
            """,
            (word,),
        )

        self.conn.commit()

        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Aprendizaje
    # ------------------------------------------------------------------

    def register_learning_attempt(
        self,
        word: str,
        correct: bool,
        *,
        commit: bool = True,
    ) -> bool:
        """
        Registra un intento realizado durante el modo de aprendizaje.

        Estos contadores son específicos de la sesión/proceso de aprendizaje
        y no sustituyen a las estadísticas históricas del quiz.
        """
        word = self._normalize_word(word)

        current = self.get_word(word)

        if current is None:
            return False

        attempts = (
            int(
                current["intentos_aprendizaje"]
            )
            + 1
        )

        correct_attempts = int(
            current["aciertos_aprendizaje"]
        )

        if correct:
            correct_attempts += 1

        cursor = self.conn.execute(
            """
            UPDATE words
            SET
                intentos_aprendizaje = ?,
                aciertos_aprendizaje = ?,
                last_seen = ?
            WHERE word = ?
            """,
            (
                attempts,
                correct_attempts,
                self._today(),
                word,
            ),
        )

        if commit:
            self.conn.commit()

        return cursor.rowcount > 0

    def register_learning_session(
        self,
        word: str,
        passed: bool,
        *,
        commit: bool = True,
    ) -> bool:
        """
        Registra una sesión de aprendizaje superada.
        """
        word = self._normalize_word(word)

        if not passed:
            return self.word_exists(
                word
            )

        current = self.get_word(word)

        if current is None:
            return False

        sessions = (
            int(
                current["sesiones_superadas"]
            )
            + 1
        )

        return self.update_word(
            word,
            sesiones_superadas=sessions,
            commit=commit,
        )

    # ------------------------------------------------------------------
    # Quiz
    # ------------------------------------------------------------------

    def register_quiz_answer(
        self,
        word: str,
        correct: bool,
        *,
        commit: bool = True,
    ) -> bool:
        """
        Registra el resultado de una respuesta del quiz.

        Actualiza:

        - aciertos;
        - errores;
        - racha;
        - intervalo de repaso;
        - fecha de última aparición.
        """
        word = self._normalize_word(word)

        current = self.get_word(word)

        if current is None:
            return False

        correct_count = int(
            current["correct"]
        )

        incorrect_count = int(
            current["incorrect"]
        )

        streak = int(
            current["streak"]
        )

        interval = max(
            1,
            int(
                current["interval"] or 1
            ),
        )

        if correct:
            correct_count += 1
            streak += 1

            # Mantiene la idea del algoritmo original:
            # incrementar progresivamente el intervalo.
            interval = max(
                1,
                int(interval * 1.8),
            )

        else:
            incorrect_count += 1
            streak = 0
            interval = 1

        cursor = self.conn.execute(
            """
            UPDATE words
            SET
                correct = ?,
                incorrect = ?,
                streak = ?,
                interval = ?,
                last_seen = ?
            WHERE word = ?
            """,
            (
                correct_count,
                incorrect_count,
                streak,
                interval,
                self._today(),
                word,
            ),
        )

        if commit:
            self.conn.commit()

        return cursor.rowcount > 0

    def register_answer(
        self,
        word: str,
        correct: bool,
        *,
        commit: bool = True,
    ) -> bool:
        """
        Alias de compatibilidad para registrar una respuesta de quiz.
        """
        return self.register_quiz_answer(
            word,
            correct,
            commit=commit,
        )

    # ------------------------------------------------------------------
    # Existencia
    # ------------------------------------------------------------------

    def word_exists(
        self,
        word: str,
    ) -> bool:
        """
        Comprueba si una palabra existe dentro de la base.
        """
        word = self._normalize_word(word)

        row = self.conn.execute(
            """
            SELECT 1
            FROM words
            WHERE word = ?
            LIMIT 1
            """,
            (word,),
        ).fetchone()

        return row is not None

    # ------------------------------------------------------------------
    # Estadísticas
    # ------------------------------------------------------------------

    def get_statistics(
        self,
    ) -> dict[str, Any]:
        """
        Obtiene estadísticas globales de la base.
        """
        row = self.conn.execute(
            """
            SELECT
                COUNT(*) AS total,

                SUM(
                    CASE
                        WHEN estado = 'nuevo'
                        THEN 1
                        ELSE 0
                    END
                ) AS nuevas,

                SUM(
                    CASE
                        WHEN estado = 'aprendiendo'
                        THEN 1
                        ELSE 0
                    END
                ) AS aprendiendo,

                SUM(
                    CASE
                        WHEN estado = 'aprendido'
                        THEN 1
                        ELSE 0
                    END
                ) AS aprendidas,

                COALESCE(
                    SUM(correct),
                    0
                ) AS correctas,

                COALESCE(
                    SUM(incorrect),
                    0
                ) AS incorrectas

            FROM words
            """
        ).fetchone()

        total = int(
            row["total"] or 0
        )

        correctas = int(
            row["correctas"] or 0
        )

        incorrectas = int(
            row["incorrectas"] or 0
        )

        attempts = (
            correctas + incorrectas
        )

        accuracy = (
            (correctas / attempts) * 100
            if attempts > 0
            else 0.0
        )

        return {
            "total": total,
            "nuevas": int(
                row["nuevas"] or 0
            ),
            "aprendiendo": int(
                row["aprendiendo"] or 0
            ),
            "aprendidas": int(
                row["aprendidas"] or 0
            ),
            "correctas": correctas,
            "incorrectas": incorrectas,
            "porcentaje_acierto": accuracy,
        }