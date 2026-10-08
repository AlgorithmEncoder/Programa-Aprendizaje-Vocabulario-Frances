"""
Lógica para el cálculo de estadísticas del vocabulario.

Este módulo no depende de Tkinter ni de SQLite directamente. Recibe una
colección de registros de palabras y devuelve estadísticas listas para que
la interfaz las presente.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class WordStatistics:
    """
    Estadísticas de una palabra concreta.
    """

    word: str
    correct: int
    incorrect: int
    total_attempts: int
    accuracy: float
    interval: int


@dataclass(slots=True, frozen=True)
class GlobalStatistics:
    """
    Estadísticas generales de una base de vocabulario.
    """

    total_words: int
    total_correct: int
    total_incorrect: int
    total_attempts: int
    accuracy: float


LEVEL_RANGES = (
    ("Nivel 1", 1),
    ("Nivel 2", 3),
    ("Nivel 3", 6),
    ("Nivel 4", 12),
    ("Nivel 5", float("inf")),
)


def _to_non_negative_int(
    value: Any,
) -> int:
    """
    Convierte un valor a entero no negativo.
    """
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _normalize_words(
    words: Iterable[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """
    Convierte los registros a una lista filtrando entradas inválidas.
    """
    normalized: list[Mapping[str, Any]] = []

    for info in words:
        if isinstance(info, Mapping):
            normalized.append(info)

    return normalized


def calculate_global_statistics(
    words: Iterable[Mapping[str, Any]],
) -> GlobalStatistics:
    """
    Calcula las estadísticas globales de una colección de palabras.
    """
    normalized = _normalize_words(words)

    total_correct = sum(
        _to_non_negative_int(word.get("correct", 0))
        for word in normalized
    )

    total_incorrect = sum(
        _to_non_negative_int(word.get("incorrect", 0))
        for word in normalized
    )

    total_attempts = total_correct + total_incorrect

    accuracy = (
        (total_correct / total_attempts) * 100
        if total_attempts > 0
        else 0.0
    )

    return GlobalStatistics(
        total_words=len(normalized),
        total_correct=total_correct,
        total_incorrect=total_incorrect,
        total_attempts=total_attempts,
        accuracy=accuracy,
    )


def calculate_word_statistics(
    words: Iterable[Mapping[str, Any]],
) -> list[WordStatistics]:
    """
    Calcula las estadísticas individuales de todas las palabras.
    """
    result: list[WordStatistics] = []

    for info in _normalize_words(words):
        word = str(info.get("word", "")).strip()

        if not word:
            continue

        correct = _to_non_negative_int(
            info.get("correct", 0)
        )

        incorrect = _to_non_negative_int(
            info.get("incorrect", 0)
        )

        total_attempts = correct + incorrect

        accuracy = (
            (correct / total_attempts) * 100
            if total_attempts > 0
            else 0.0
        )

        interval = _to_non_negative_int(
            info.get("interval", 0)
        )

        result.append(
            WordStatistics(
                word=word,
                correct=correct,
                incorrect=incorrect,
                total_attempts=total_attempts,
                accuracy=accuracy,
                interval=interval,
            )
        )

    return result


def get_most_failed_words(
    words: Iterable[Mapping[str, Any]],
    limit: int = 5,
) -> list[WordStatistics]:
    """
    Obtiene las palabras con mayor número de errores.

    Como desempate se utiliza la precisión más baja.
    """
    if limit < 1:
        return []

    statistics = calculate_word_statistics(words)

    failed = [
        item
        for item in statistics
        if item.incorrect > 0
    ]

    failed.sort(
        key=lambda item: (
            item.incorrect,
            -item.accuracy,
        ),
        reverse=True,
    )

    return failed[:limit]


def get_best_mastered_words(
    words: Iterable[Mapping[str, Any]],
    limit: int = 5,
) -> list[WordStatistics]:
    """
    Obtiene las palabras con mejores resultados.

    Se prioriza:

    1. precisión;
    2. número de aciertos;
    3. menor número de errores.
    """
    if limit < 1:
        return []

    statistics = calculate_word_statistics(words)

    mastered = [
        item
        for item in statistics
        if item.correct > 0
    ]

    mastered.sort(
        key=lambda item: (
            item.accuracy,
            item.correct,
            -item.incorrect,
        ),
        reverse=True,
    )

    return mastered[:limit]


def count_words_by_level(
    words: Iterable[Mapping[str, Any]],
) -> dict[str, int]:
    """
    Cuenta cuántas palabras hay en cada nivel de aprendizaje.

    Los niveles se determinan mediante el intervalo de repaso.
    """
    counts = {
        "Nivel 1": 0,
        "Nivel 2": 0,
        "Nivel 3": 0,
        "Nivel 4": 0,
        "Nivel 5": 0,
    }

    for info in _normalize_words(words):
        interval = _to_non_negative_int(
            info.get("interval", 0)
        )

        if interval <= 1:
            level = "Nivel 1"
        elif interval <= 3:
            level = "Nivel 2"
        elif interval <= 6:
            level = "Nivel 3"
        elif interval <= 12:
            level = "Nivel 4"
        else:
            level = "Nivel 5"

        counts[level] += 1

    return counts