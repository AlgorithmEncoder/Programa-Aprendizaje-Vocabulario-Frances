"""
Lógica del sistema de aprendizaje.

Este módulo contiene las reglas que determinan:

- qué palabras entran en una sesión;
- cómo se calcula el rendimiento;
- cuándo una sesión se considera superada;
- cómo evoluciona el estado de una palabra.

No depende de Tkinter ni de SQLite.
"""

from __future__ import annotations

import random
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any


DEFAULT_SESSION_SIZE = 10

DEFAULT_NEW_WORD_PERCENTAGE = 0.60
DEFAULT_REVIEW_PERCENTAGE = 0.40
DEFAULT_MINIMUM_ACCURACY = 0.50
DEFAULT_SESSIONS_TO_LEARN = 2


@dataclass(slots=True, frozen=True)
class SessionEvaluation:
    """
    Resultado de evaluar una palabra al terminar una sesión.
    """

    accuracy: float
    passed: bool
    new_state: str
    sessions_completed: int


def _get_int(
    value: Any,
    default: int = 0,
) -> int:
    """
    Convierte un valor a entero no negativo.
    """
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default

    return max(0, number)


def _get_float(
    value: Any,
    default: float,
) -> float:
    """
    Convierte un valor a número decimal.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _get_percentage(
    config: Mapping[str, Any],
    key: str,
    default: float,
) -> float:
    """
    Obtiene un porcentaje de configuración.
    """
    value = _get_float(
        config.get(key, default),
        default,
    )

    return min(
        max(value, 0.0),
        1.0,
    )


def get_session_size(
    config: Mapping[str, Any],
) -> int:
    """
    Obtiene el tamaño de sesión configurado.
    """
    value = _get_int(
        config.get(
            "tamano_sesion_aprendizaje",
            DEFAULT_SESSION_SIZE,
        ),
        DEFAULT_SESSION_SIZE,
    )

    return max(
        1,
        value,
    )


def select_learning_words(
    words: Iterable[Mapping[str, Any]],
    config: Mapping[str, Any],
    *,
    total: int | None = None,
    rng: random.Random | None = None,
) -> list[Mapping[str, Any]]:
    """
    Selecciona las palabras para una sesión de aprendizaje.

    La selección intenta mantener la proporción configurada entre
    palabras nuevas y palabras de repaso y utiliza otras palabras
    disponibles para completar la sesión cuando sea necesario.
    """
    candidates = list(words)

    if not candidates:
        return []

    if rng is None:
        rng = random.Random()

    if total is None:
        total = get_session_size(config)
    else:
        total = max(
            1,
            int(total),
        )

    total = min(
        total,
        len(candidates),
    )

    new_percentage = _get_percentage(
        config,
        "porcentaje_nuevas",
        DEFAULT_NEW_WORD_PERCENTAGE,
    )

    review_percentage = _get_percentage(
        config,
        "porcentaje_repaso",
        DEFAULT_REVIEW_PERCENTAGE,
    )

    percentage_total = (
        new_percentage + review_percentage
    )

    if percentage_total > 1:
        new_percentage /= percentage_total
        review_percentage /= percentage_total

    new_count = int(
        total * new_percentage
    )

    review_count = int(
        total * review_percentage
    )

    selected: list[Mapping[str, Any]] = []

    new_words = [
        word
        for word in candidates
        if word.get(
            "estado",
            "nuevo",
        ) == "nuevo"
    ]

    review_words = [
        word
        for word in candidates
        if word.get(
            "estado",
            "nuevo",
        ) == "aprendiendo"
    ]

    if new_words and new_count:
        selected.extend(
            rng.sample(
                new_words,
                min(
                    new_count,
                    len(new_words),
                ),
            )
        )

    available_review = [
        word
        for word in review_words
        if word not in selected
    ]

    if available_review and review_count:
        selected.extend(
            rng.sample(
                available_review,
                min(
                    review_count,
                    len(available_review),
                ),
            )
        )

    remaining = [
        word
        for word in candidates
        if word not in selected
    ]

    slots_left = (
        total - len(selected)
    )

    if remaining and slots_left > 0:
        selected.extend(
            rng.sample(
                remaining,
                min(
                    slots_left,
                    len(remaining),
                ),
            )
        )

    rng.shuffle(selected)

    return selected[:total]


def calculate_accuracy(
    word_data: Mapping[str, Any],
) -> float:
    """
    Calcula la precisión durante la sesión actual.
    """
    correct = _get_int(
        word_data.get(
            "aciertos_aprendizaje",
            0,
        )
    )

    attempts = _get_int(
        word_data.get(
            "intentos_aprendizaje",
            0,
        )
    )

    if attempts == 0:
        return 0.0

    return correct / attempts


def evaluate_word_session(
    word_data: Mapping[str, Any],
    config: Mapping[str, Any],
) -> SessionEvaluation:
    """
    Evalúa el rendimiento de una palabra en una sesión.
    """
    accuracy = calculate_accuracy(
        word_data
    )

    minimum_accuracy = _get_percentage(
        config,
        "porcentaje_acierto_minimo",
        DEFAULT_MINIMUM_ACCURACY,
    )

    sessions_to_learn = max(
        1,
        _get_int(
            config.get(
                "sesiones_para_aprender",
                DEFAULT_SESSIONS_TO_LEARN,
            ),
            DEFAULT_SESSIONS_TO_LEARN,
        ),
    )

    current_state = str(
        word_data.get(
            "estado",
            "nuevo",
        )
    )

    previous_sessions = _get_int(
        word_data.get(
            "sesiones_superadas",
            0,
        )
    )

    passed = (
        accuracy >= minimum_accuracy
    )

    sessions_completed = previous_sessions

    if passed:
        sessions_completed += 1

    new_state = current_state

    if passed:
        if current_state == "nuevo":
            new_state = "aprendiendo"

        elif (
            current_state == "aprendiendo"
            and sessions_completed >= sessions_to_learn
        ):
            new_state = "aprendido"

    return SessionEvaluation(
        accuracy=accuracy,
        passed=passed,
        new_state=new_state,
        sessions_completed=sessions_completed,
    )