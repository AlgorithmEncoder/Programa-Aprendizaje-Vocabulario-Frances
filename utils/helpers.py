"""
Funciones auxiliares generales de la aplicación.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Niveles de aprendizaje
# ---------------------------------------------------------------------------

LEVEL_1_MAX_INTERVAL = 1
LEVEL_2_MAX_INTERVAL = 3
LEVEL_3_MAX_INTERVAL = 6
LEVEL_4_MAX_INTERVAL = 12


def get_level(interval: int | float) -> str:
    """
    Obtiene el nivel de aprendizaje asociado a un intervalo.

    Parameters
    ----------
    interval:
        Número de días del intervalo actual de repaso.

    Returns
    -------
    str
        Nombre y representación visual del nivel.

    Raises
    ------
    TypeError
        Si ``interval`` no es numérico.

    ValueError
        Si ``interval`` es negativo.

    Examples
    --------
    >>> get_level(1)
    '🔴 Nivel 1'

    >>> get_level(7)
    '🟢 Nivel 4'

    >>> get_level(20)
    '🔵 Nivel 5'
    """
    if not isinstance(interval, (int, float)):
        raise TypeError(
            "interval debe ser un número."
        )

    if interval < 0:
        raise ValueError(
            "interval no puede ser negativo."
        )

    if interval <= LEVEL_1_MAX_INTERVAL:
        return "🔴 Nivel 1"

    if interval <= LEVEL_2_MAX_INTERVAL:
        return "🟠 Nivel 2"

    if interval <= LEVEL_3_MAX_INTERVAL:
        return "🟡 Nivel 3"

    if interval <= LEVEL_4_MAX_INTERVAL:
        return "🟢 Nivel 4"

    return "🔵 Nivel 5"