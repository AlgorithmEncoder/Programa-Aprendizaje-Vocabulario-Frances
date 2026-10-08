from __future__ import annotations

import random

from logic.learning import (
    calculate_accuracy,
    evaluate_word_session,
    get_session_size,
    select_learning_words,
)


def make_word(
    word: str,
    state: str = "nuevo",
) -> dict:
    return {
        "word": word,
        "translation": f"translation-{word}",
        "estado": state,
        "aciertos_aprendizaje": 0,
        "intentos_aprendizaje": 0,
        "sesiones_superadas": 0,
    }


def test_calculate_accuracy() -> None:
    word = {
        "aciertos_aprendizaje": 3,
        "intentos_aprendizaje": 4,
    }

    assert calculate_accuracy(
        word
    ) == 0.75


def test_accuracy_with_no_attempts() -> None:
    word = {
        "aciertos_aprendizaje": 0,
        "intentos_aprendizaje": 0,
    }

    assert calculate_accuracy(
        word
    ) == 0.0


def test_new_word_becomes_learning() -> None:
    word = {
        "estado": "nuevo",
        "aciertos_aprendizaje": 2,
        "intentos_aprendizaje": 2,
        "sesiones_superadas": 0,
    }

    config = {
        "porcentaje_acierto_minimo": 0.5,
        "sesiones_para_aprender": 2,
    }

    result = evaluate_word_session(
        word,
        config,
    )

    assert result.passed is True
    assert result.new_state == "aprendiendo"
    assert result.sessions_completed == 1


def test_learning_word_becomes_learned_after_required_sessions() -> None:
    word = {
        "estado": "aprendiendo",
        "aciertos_aprendizaje": 4,
        "intentos_aprendizaje": 4,
        "sesiones_superadas": 1,
    }

    config = {
        "porcentaje_acierto_minimo": 0.5,
        "sesiones_para_aprender": 2,
    }

    result = evaluate_word_session(
        word,
        config,
    )

    assert result.passed is True
    assert result.new_state == "aprendido"
    assert result.sessions_completed == 2


def test_failed_session_does_not_increment_completed_sessions() -> None:
    word = {
        "estado": "aprendiendo",
        "aciertos_aprendizaje": 1,
        "intentos_aprendizaje": 4,
        "sesiones_superadas": 1,
    }

    config = {
        "porcentaje_acierto_minimo": 0.5,
        "sesiones_para_aprender": 2,
    }

    result = evaluate_word_session(
        word,
        config,
    )

    assert result.passed is False
    assert result.new_state == "aprendiendo"
    assert result.sessions_completed == 1


def test_session_size_comes_from_config() -> None:
    config = {
        "tamano_sesion_aprendizaje": 15,
    }

    assert get_session_size(
        config
    ) == 15


def test_learning_selection_respects_session_size() -> None:
    words = [
        make_word(f"word{i}")
        for i in range(20)
    ]

    config = {
        "tamano_sesion_aprendizaje": 10,
        "porcentaje_nuevas": 0.6,
        "porcentaje_repaso": 0.4,
    }

    selected = select_learning_words(
        words,
        config,
        rng=random.Random(42),
    )

    assert len(selected) == 10


def test_learning_selection_includes_new_words() -> None:
    words = [
        *(
            make_word(
                f"new{i}",
                "nuevo",
            )
            for i in range(10)
        ),
        *(
            make_word(
                f"learning{i}",
                "aprendiendo",
            )
            for i in range(10)
        ),
    ]

    config = {
        "tamano_sesion_aprendizaje": 10,
        "porcentaje_nuevas": 0.6,
        "porcentaje_repaso": 0.4,
    }

    selected = select_learning_words(
        words,
        config,
        rng=random.Random(42),
    )

    states = [
        word["estado"]
        for word in selected
    ]

    assert "nuevo" in states
    assert "aprendiendo" in states