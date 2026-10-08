from data.sqlite_db import SQLiteDB

def load_database_sqlite(db_name: str) -> dict:
    """
    Carga todas las palabras de la base SQLite en un diccionario
    similar al que usabas antes.
    """
    db = SQLiteDB(db_name)
    words = db.get_all_words()  # devuelve {palabra: traducción}

    # Convertir a formato completo con campos de seguimiento
    full_words = {}
    for word, translation in words.items():
        info = db.get_word(word)
        full_words[word] = info

    return {
        "name": db_name,
        "words": full_words
    }


def update_word_sqlite(db_name: str, words_data: dict):
    """
    Actualiza todas las palabras en la base SQLite a partir del dict.
    """
    db = SQLiteDB(db_name)
    for word, info in words_data.items():
        # Evitamos el campo 'mot' o 'traduction' que se usan internamente
        info_copy = {k: v for k, v in info.items() if k not in ["mot", "traduction"]}
        db.update_word(word, **info_copy)
    db.close()


def save_database_sqlite(db_name: str, words_data: dict):
    """
    Función para persistir cambios (alias de update_word_sqlite)
    """
    update_word_sqlite(db_name, words_data)