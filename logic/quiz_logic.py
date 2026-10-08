"""
Lógica de selección adaptativa de palabras para los quizzes.

Este módulo contiene las reglas utilizadas para decidir qué palabras
deberían aparecer en una sesión de aprendizaje o repaso.

La lógica no depende de Tkinter ni de ningún elemento de la interfaz
gráfica. Recibe datos y devuelve resultados, lo que facilita su reutilización
y la creación de tests automáticos.
"""

from __future__ import annotations

import random
from collections.abc import Iterable, Mapping
from datetime import date
from typing import Any, TypeAlias


# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------

WordInfo: TypeAlias = Mapping[str, Any]
WordEntry: TypeAlias = tuple[str, WordInfo]


# ---------------------------------------------------------------------------
# Constantes del algoritmo
# ---------------------------------------------------------------------------

ADAPTIVE_TOP_PERCENTAGE = 0.40
MIN_ADAPTIVE_CANDIDATES = 5

DUE_WEIGHT = 2.0
ERROR_WEIGHT = 1.5
NOVELTY_WEIGHT = 1.0


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

def _get_value(
    info: WordInfo,
    key: str,
    default: Any,
) -> Any:
    """
    Obtiene un valor del registro de una palabra.

    Centralizar esta operación permite tratar de forma segura registros
    procedentes de distintas fuentes, por ejemplo JSON o SQLite.
    """
    return info.get(key, default)


def _to_non_negative_int(
    value: Any,
    default: int = 0,
) -> int:
    """
    Convierte un valor a entero no negativo.

    Si la conversión no es posible, devuelve ``default``.
    """
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default

    return max(0, number)


def _parse_last_seen(value: Any) -> date | None:
    """
    Convierte una fecha almacenada a ``date``.

    ``None`` representa que la palabra todavía no ha sido vista.
    """
    if value in (None, ""):
        return None

    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _get_days_since_seen(
    last_seen: Any,
    today: date,
) -> int | None:
    """
    Calcula cuántos días han pasado desde la última aparición.

    Devuelve ``None`` cuando la palabra nunca se ha visto o la fecha
    almacenada no es válida.
    """
    parsed_date = _parse_last_seen(last_seen)

    if parsed_date is None:
        return None

    days = (today - parsed_date).days

    # Una fecha futura no debe producir valores negativos.
    return max(0, days)


def _calculate_error_ratio(info: WordInfo) -> float:
    """
    Calcula la proporción de respuestas incorrectas.

    Returns
    -------
    float
        Valor entre 0.0 y 1.0.
    """
    correct = _to_non_negative_int(
        _get_value(info, "correct", 0)
    )
    incorrect = _to_non_negative_int(
        _get_value(info, "incorrect", 0)
    )

    total = correct + incorrect

    if total == 0:
        return 0.0

    return incorrect / total


def _calculate_adaptive_score(
    info: WordInfo,
    today: date,
) -> float:
    """
    Calcula la prioridad adaptativa de una palabra.

    El sistema combina tres factores:

    1. Tiempo desde el último repaso.
    2. Proporción de errores.
    3. Falta de historial de respuestas.

    Una puntuación más alta significa que la palabra debería tener
    mayor prioridad.
    """
    correct = _to_non_negative_int(
        _get_value(info, "correct", 0)
    )
    incorrect = _to_non_negative_int(
        _get_value(info, "incorrect", 0)
    )

    total = correct + incorrect

    error_ratio = _calculate_error_ratio(info)

    days_since = _get_days_since_seen(
        _get_value(info, "last_seen", None),
        today,
    )

    interval = _to_non_negative_int(
        _get_value(info, "interval", 1),
        default=1,
    )

    interval = max(1, interval)

    # Una palabra que nunca se ha visto necesita entrar en circulación.
    # La tratamos como si estuviera pendiente desde el inicio.
    if days_since is None:
        due_factor = 1.0
    else:
        due_factor = days_since / interval

    novelty_factor = 1 / (total + 1)

    return (
        (due_factor * DUE_WEIGHT)
        + (error_ratio * ERROR_WEIGHT)
        + (novelty_factor * NOVELTY_WEIGHT)
    )


def _normalize_word_entries(
    words: Mapping[str, WordInfo]
    | Iterable[WordEntry],
) -> list[WordEntry]:
    """
    Convierte las posibles representaciones de palabras a una lista común.

    La aplicación normalmente utilizará un diccionario:

        {
            "bonjour": {...},
            "chat": {...}
        }

    pero también se admite una secuencia de pares ``(word, info)`` para
    facilitar la reutilización con resultados procedentes de otras fuentes.
    """
    if isinstance(words, Mapping):
        entries = list(words.items())
    else:
        entries = list(words)

    normalized: list[WordEntry] = []

    for entry in entries:
        if not isinstance(entry, tuple) or len(entry) != 2:
            continue

        word, info = entry

        if not isinstance(word, str):
            continue

        word = word.strip()

        if not word:
            continue

        if not isinstance(info, Mapping):
            continue

        normalized.append((word, info))

    return normalized


def _get_review_count(
    review_count: int | Any,
) -> int:
    """
    Obtiene el número de palabras que deben seleccionarse.

    Se acepta temporalmente un objeto que tenga ``get()`` para mantener
    compatibilidad con la interfaz gráfica existente.

    La interfaz idealmente debería proporcionar directamente un ``int``.
    """
    if hasattr(review_count, "get") and callable(review_count.get):
        review_count = review_count.get()

    try:
        count = int(review_count)
    except (TypeError, ValueError):
        raise ValueError(
            "review_count debe ser un número entero."
        ) from None

    if count < 1:
        raise ValueError(
            "review_count debe ser mayor o igual que 1."
        )

    return count


# ---------------------------------------------------------------------------
# Selección adaptativa
# ---------------------------------------------------------------------------

def get_adaptive_words(
    words: Mapping[str, WordInfo]
    | Iterable[WordEntry],
    *,
    today: date | None = None,
    rng: random.Random | None = None,
) -> list[WordEntry]:
    """
    Selecciona palabras de forma adaptativa.

    Las palabras reciben una puntuación basada en:

    - tiempo desde el último repaso;
    - proporción de errores;
    - cantidad de respuestas realizadas.

    Se conserva el 40 % superior de candidatos, con un mínimo de cinco
    cuando existen suficientes palabras, y posteriormente se mezclan para
    introducir variabilidad entre sesiones.

    Parameters
    ----------
    words:
        Palabras disponibles.

    today:
        Fecha utilizada como referencia. Por defecto, la fecha actual.

        Permitir indicar la fecha facilita las pruebas automáticas.

    rng:
        Generador aleatorio opcional. Por defecto se utiliza el módulo
        ``random``.

    Returns
    -------
    list
        Lista de pares ``(word, info)``.

    Notes
    -----
    La función no modifica los datos originales.
    """
    entries = _normalize_word_entries(words)

    if not entries:
        return []

    if today is None:
        today = date.today()

    # Calculamos una puntuación para cada palabra.
    candidates: list[tuple[str, WordInfo, float]] = []

    for word, info in entries:
        score = _calculate_adaptive_score(
            info,
            today,
        )

        candidates.append(
            (word, info, score)
        )

    # Las palabras con mayor prioridad se colocan primero.
    candidates.sort(
        key=lambda item: item[2],
        reverse=True,
    )

    candidate_count = max(
        MIN_ADAPTIVE_CANDIDATES,
        int(len(candidates) * ADAPTIVE_TOP_PERCENTAGE),
    )

    candidate_count = min(
        candidate_count,
        len(candidates),
    )

    selected = candidates[:candidate_count]

    # Mezclar las candidatas seleccionadas evita que el orden de prioridad
    # determine siempre el orden en que aparecen en el quiz.
    if rng is None:
        random.shuffle(selected)
    else:
        rng.shuffle(selected)

    return [
        (word, info)
        for word, info, _score in selected
    ]


# ---------------------------------------------------------------------------
# Selección para repaso
# ---------------------------------------------------------------------------

def get_review_words(
    words: Mapping[str, WordInfo]
    | Iterable[WordEntry],
    review_count: int | Any,
) -> list[WordEntry]:
    """
    Selecciona las palabras que presentan mayor necesidad de repaso.

    La prioridad se determina principalmente mediante la proporción
    de respuestas incorrectas.

    Parameters
    ----------
    words:
        Palabras disponibles.

    review_count:
        Número máximo de palabras que se desean obtener.

        Se recomienda proporcionar un ``int``. También se admite
        temporalmente un objeto Tkinter con ``get()`` para mantener
        compatibilidad con la interfaz existente.

    Returns
    -------
    list
        Lista de pares ``(word, info)``.

    Notes
    -----
    Las palabras sin ninguna respuesta previa no se consideran palabras
    de repaso, ya que todavía no existe información suficiente sobre
    su rendimiento.
    """
    entries = _normalize_word_entries(words)
    count = _get_review_count(review_count)

    candidates: list[
        tuple[str, WordInfo, float, int]
    ] = []

    for word, info in entries:
        correct = _to_non_negative_int(
            _get_value(info, "correct", 0)
        )
        incorrect = _to_non_negative_int(
            _get_value(info, "incorrect", 0)
        )

        total = correct + incorrect

        if total == 0:
            continue

        error_ratio = incorrect / total

        # En caso de empate, priorizamos las palabras con más errores
        # absolutos.
        candidates.append(
            (
                word,
                info,
                error_ratio,
                incorrect,
            )
        )

    if not candidates:
        return []

    # Primero importa el porcentaje de error y, como desempate,
    # el número de errores absolutos.
    candidates.sort(
        key=lambda item: (item[2], item[3]),
        reverse=True,
    )

    selected = candidates[:count]

    return [
        (word, info)
        for word, info, _error_ratio, _incorrect in selected
    ]