import os
import sqlite3
from pathlib import Path
from datetime import date
from config.app_config import DB_FOLDER  # tu carpeta de bases

class SQLiteDB:
    """Clase para manejar una base de datos SQLite específica."""

    def __init__(self, name: str):
        self.name = name
        self.db_path = os.path.join(DB_FOLDER, f"{name}.sqlite")
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_table()

    # =========================
    # CONEXIÓN Y TABLA
    # =========================
    def _connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
            self.conn = None
            self.cursor = None

    def _create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS words (
                word TEXT PRIMARY KEY,
                translation TEXT,
                estado TEXT DEFAULT 'nuevo',
                aciertos_aprendizaje INTEGER DEFAULT 0,
                intentos_aprendizaje INTEGER DEFAULT 0,
                sesiones_superadas INTEGER DEFAULT 0,
                correct INTEGER DEFAULT 0,
                incorrect INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                interval INTEGER DEFAULT 1,
                last_seen TEXT
            )
        """)
        self.conn.commit()

    # =========================
    # OPERACIONES DE PALABRAS
    # =========================
    def add_word(self, word: str, translation: str):
        """Agrega o reemplaza una palabra."""
        self.cursor.execute("""
            INSERT OR REPLACE INTO words
            (word, translation, last_seen)
            VALUES (?, ?, ?)
        """, (word, translation, str(date.today())))
        self.conn.commit()

    def update_word(self, word: str, **kwargs):
        """Actualiza campos de una palabra existente."""
        if not kwargs:
            return
        fields = ", ".join(f"{k}=?" for k in kwargs.keys())
        values = list(kwargs.values())
        values.append(word)
        self.cursor.execute(f"UPDATE words SET {fields} WHERE word = ?", values)
        self.conn.commit()

    def delete_word(self, word: str):
        self.cursor.execute("DELETE FROM words WHERE word = ?", (word,))
        self.conn.commit()

    def get_word(self, word: str):
        self.cursor.execute("SELECT * FROM words WHERE word = ?", (word,))
        row = self.cursor.fetchone()
        if row:
            keys = [description[0] for description in self.cursor.description]
            return dict(zip(keys, row))
        return None

    def word_exists(self, word: str) -> bool:
        self.cursor.execute("SELECT 1 FROM words WHERE word = ?", (word,))
        return self.cursor.fetchone() is not None

    def get_all_words(self):
        """Devuelve todas las palabras con su traducción."""
        self.cursor.execute("SELECT word, translation FROM words ORDER BY word")
        return {row[0]: row[1] for row in self.cursor.fetchall()}

    # =========================
    # OPERACIONES DE BASES
    # =========================
    @staticmethod
    def list_databases():
        Path(DB_FOLDER).mkdir(exist_ok=True)
        return [f.stem for f in Path(DB_FOLDER).glob("*.sqlite")]

    @staticmethod
    def create_database(name: str):
        path = os.path.join(DB_FOLDER, f"{name}.sqlite")
        if os.path.exists(path):
            raise FileExistsError(f"La base '{name}' ya existe.")
        SQLiteDB(name)  # Se crea la base y la tabla automáticamente

    @staticmethod
    def exists(name: str) -> bool:
        path = os.path.join(DB_FOLDER, f"{name}.sqlite")
        return os.path.exists(path)