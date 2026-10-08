"""
Carga y validación de la configuración de AprenderFrances.

La configuración se almacena en ``config.json``.

Este módulo es responsable de localizar, cargar y validar la configuración
para que el resto de la aplicación pueda trabajar con valores fiables.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


CONFIG_FILENAME = "config.json"


DEFAULT_CONFIG: dict[str, Any] = {
    "tamano_sesion_aprendizaje": 10,
    "porcentaje_nuevas": 0.6,
    "porcentaje_repaso": 0.4,
    "porcentaje_acierto_minimo": 0.5,
    "sesiones_para_aprender": 2,
    "opciones_multiple": 4,
}


class ConfigError(Exception):
    """
    Excepción utilizada para errores de configuración.
    """


def get_config_path(
    custom_path: str | Path | None = None,
) -> Path:
    """
    Obtiene la ruta del archivo de configuración.
    """
    if custom_path is not None:
        path = Path(
            custom_path
        ).expanduser().resolve()

        if not path.is_file():
            raise FileNotFoundError(
                f"No se encontró la configuración: {path}"
            )

        return path

    candidates: list[Path] = []

    # ---------------------------------------------------------------
    # Aplicación empaquetada
    # ---------------------------------------------------------------

    if getattr(sys, "frozen", False):
        executable_dir = (
            Path(sys.executable)
            .resolve()
            .parent
        )

        candidates.append(
            executable_dir / CONFIG_FILENAME
        )

    # ---------------------------------------------------------------
    # Desarrollo
    # ---------------------------------------------------------------

    project_root = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    candidates.append(
        project_root / CONFIG_FILENAME
    )

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    paths = "\n".join(
        f"  - {path}"
        for path in candidates
    )

    raise FileNotFoundError(
        (
            "No se encontró el archivo config.json.\n\n"
            f"Rutas comprobadas:\n{paths}"
        )
    )


def _validate_number(
    config: dict[str, Any],
    key: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> None:
    """
    Valida que una propiedad sea numérica y respete sus límites.
    """
    value = config[key]

    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise ConfigError(
            (
                f"La propiedad '{key}' debe ser "
                "numérica."
            )
        )

    if minimum is not None and value < minimum:
        raise ConfigError(
            (
                f"La propiedad '{key}' no puede ser "
                f"menor que {minimum}."
            )
        )

    if maximum is not None and value > maximum:
        raise ConfigError(
            (
                f"La propiedad '{key}' no puede ser "
                f"mayor que {maximum}."
            )
        )


def validate_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """
    Valida y normaliza la configuración.

    Returns
    -------
    dict
        Configuración completa y validada.

    Raises
    ------
    ConfigError
        Cuando existe una configuración inválida.
    """
    if not isinstance(config, dict):
        raise ConfigError(
            "La configuración debe ser un objeto JSON."
        )

    merged = {
        **DEFAULT_CONFIG,
        **config,
    }

    # ---------------------------------------------------------------
    # Sesión
    # ---------------------------------------------------------------

    _validate_number(
        merged,
        "tamano_sesion_aprendizaje",
        minimum=1,
    )

    _validate_number(
        merged,
        "porcentaje_nuevas",
        minimum=0,
        maximum=1,
    )

    _validate_number(
        merged,
        "porcentaje_repaso",
        minimum=0,
        maximum=1,
    )

    percentages_total = (
        merged["porcentaje_nuevas"]
        + merged["porcentaje_repaso"]
    )

    if percentages_total <= 0:
        raise ConfigError(
            (
                "La suma de porcentaje_nuevas y "
                "porcentaje_repaso debe ser mayor que 0."
            )
        )

    if percentages_total > 1:
        raise ConfigError(
            (
                "La suma de porcentaje_nuevas y "
                "porcentaje_repaso no puede superar 1."
            )
        )

    _validate_number(
        merged,
        "porcentaje_acierto_minimo",
        minimum=0,
        maximum=1,
    )

    _validate_number(
        merged,
        "sesiones_para_aprender",
        minimum=1,
    )

    _validate_number(
        merged,
        "opciones_multiple",
        minimum=2,
    )

    # Los valores enteros deben ser realmente enteros.
    integer_fields = (
        "tamano_sesion_aprendizaje",
        "sesiones_para_aprender",
        "opciones_multiple",
    )

    for field in integer_fields:
        value = merged[field]

        if not isinstance(value, int):
            if isinstance(value, float) and value.is_integer():
                merged[field] = int(value)
            else:
                raise ConfigError(
                    (
                        f"La propiedad '{field}' "
                        "debe ser un número entero."
                    )
                )

    return merged


def cargar_config(
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Carga y valida la configuración de la aplicación.
    """
    path = get_config_path(
        config_path
    )

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError as error:
        raise ConfigError(
            (
                "El archivo config.json contiene "
                f"JSON inválido: {error}"
            )
        ) from error

    return validate_config(data)


def load_config(
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Alias en inglés de ``cargar_config``.
    """
    return cargar_config(
        config_path
    )