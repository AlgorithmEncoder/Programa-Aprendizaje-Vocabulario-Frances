from datetime import date

import pytest

from data.sqlite_db import SQLiteDB
from logic.quiz_logic import get_adaptive_words, get_review_words


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """
    Crea una base de datos SQLite aislada para cada test.

    Usamos pytest's tmp_path para no tocar las bases de datos reales
    del proyecto.
    """
    # DB_FOLDER utiliza objetos pathlib.Path, así que mantenemos
    # tmp_path como Path y no lo convertimos a str.
    monkeypatch.setattr("data.sqlite_db.DB_FOLDER", tmp_path)

    db_name = "integration_test"

    SQLiteDB.create_database(db_name)
    db = SQLiteDB(db_name)

    yield db

    db.close()


def test_flujo_completo_de_creacion_y_recuperacion(test_db):
    """
    Comprueba el flujo básico:

    crear palabra → actualizar datos → cerrar DB
    → volver a abrir → comprobar que los datos persisten.
    """
    test_db.add_word("bonjour", "hola")

    test_db.update_word(
        "bonjour",
        correct=3,
        incorrect=1,
        streak=2,
        interval=4,
        last_seen=str(date.today()),
    )

    test_db.close()

    db = SQLiteDB("integration_test")

    word = db.get_word("bonjour")

    assert word["translation"] == "hola"
    assert word["correct"] == 3
    assert word["incorrect"] == 1
    assert word["streak"] == 2
    assert word["interval"] == 4
    assert word["last_seen"] == str(date.today())

    db.close()


def test_flujo_de_quiz_con_base_de_datos(test_db):
    """
    Comprueba la interacción entre SQLiteDB y quiz_logic.

    Se crean palabras con distintos niveles de conocimiento,
    se seleccionan para un quiz adaptativo y después se simula
    una respuesta correcta que queda guardada en SQLite.
    """
    test_db.add_word("bonjour", "hola")
    test_db.add_word("maison", "casa")
    test_db.add_word("chat", "gato")

    test_db.update_word(
        "bonjour",
        correct=8,
        incorrect=1,
        streak=3,
        interval=8,
        last_seen=str(date.today()),
    )

    test_db.update_word(
        "maison",
        correct=2,
        incorrect=4,
        streak=0,
        interval=1,
        last_seen=str(date.today()),
    )

    test_db.update_word(
        "chat",
        correct=0,
        incorrect=0,
        streak=0,
        interval=1,
        last_seen=str(date.today()),
    )

    words = {
        info["word"]: info
        for info in test_db.get_all_words()
    }

    questions = get_adaptive_words(words)

    assert questions
    assert all(len(question) == 2 for question in questions)

    selected_word, selected_info = questions[0]

    previous_correct = selected_info["correct"]

    # Simulamos una respuesta correcta,
    # igual que haría el sistema de quiz.
    selected_info["correct"] += 1
    selected_info["streak"] += 1
    selected_info["interval"] = max(
        1,
        int(selected_info["interval"] * 1.8)
    )
    selected_info["last_seen"] = str(date.today())

    selected_info.pop("word", None)

    test_db.update_word(
        selected_word,
        **selected_info,
    )

    saved_info = test_db.get_word(selected_word)

    assert saved_info["correct"] == previous_correct + 1
    assert saved_info["streak"] >= 1
    assert saved_info["interval"] >= 1
    assert saved_info["last_seen"] == str(date.today())


def test_flujo_de_repaso_con_base_de_datos(test_db):
    """
    Comprueba que las palabras guardadas en SQLite pueden pasar
    al sistema de selección de palabras problemáticas.
    """
    test_db.add_word("bonjour", "hola")
    test_db.add_word("maison", "casa")
    test_db.add_word("chat", "gato")

    test_db.update_word(
        "bonjour",
        correct=10,
        incorrect=1,
        streak=5,
        interval=10,
        last_seen=str(date.today()),
    )

    test_db.update_word(
        "maison",
        correct=2,
        incorrect=5,
        streak=0,
        interval=1,
        last_seen=str(date.today()),
    )

    test_db.update_word(
        "chat",
        correct=1,
        incorrect=3,
        streak=0,
        interval=1,
        last_seen=str(date.today()),
    )

    words = {
        info["word"]: info
        for info in test_db.get_all_words()
    }

    review_words = get_review_words(
        list(words.items()),
        2,
    )

    assert len(review_words) == 2

    selected_words = [word for word, _ in review_words]

    # Maison tiene una proporción de errores mayor,
    # por lo que debe estar entre las palabras prioritarias.
    assert "maison" in selected_words


def test_los_cambios_del_quiz_persisten_al_reabrir(test_db):
    """
    Comprueba específicamente que una modificación realizada durante
    un quiz no se queda solamente en memoria.
    """
    test_db.add_word("merci", "gracias")

    test_db.update_word(
        "merci",
        correct=0,
        incorrect=0,
        streak=0,
        interval=1,
        last_seen=None,
    )

    # Simulamos un primer intento incorrecto.
    info = test_db.get_word("merci")

    info["incorrect"] += 1
    info["streak"] = 0
    info["interval"] = 1
    info["last_seen"] = str(date.today())

    info.pop("word", None)
    test_db.update_word("merci", **info)

    # Cerramos y volvemos a abrir la base.
    test_db.close()

    db = SQLiteDB("integration_test")

    saved_info = db.get_word("merci")

    assert saved_info["correct"] == 0
    assert saved_info["incorrect"] == 1
    assert saved_info["streak"] == 0
    assert saved_info["interval"] == 1
    assert saved_info["last_seen"] == str(date.today())

    db.close()