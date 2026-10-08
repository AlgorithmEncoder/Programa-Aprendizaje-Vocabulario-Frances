from __future__ import annotations

import json
from pathlib import Path

from logic.json_sqlite_converter import (
    get_database_path,
    json_to_sqlite,
)


def create_json(
    path: Path,
    words: dict,
) -> None:
    data = {
        "words": words,
    }

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_json_to_sqlite(tmp_path: Path) -> None:
    json_path = tmp_path / "frances.json"
    output = tmp_path / "databases"

    create_json(
        json_path,
        {
            "bonjour": {
                "translation": "hola",
            },
            "chat": {
                "translation": "gato",
            },
        },
    )

    result = json_to_sqlite(
        json_path,
        output,
    )

    assert result.success is True
    assert result.words == 2
    assert result.output == get_database_path(
        json_path,
        output,
    )
    assert result.output.exists()


def test_invalid_json_returns_failure(
    tmp_path: Path,
) -> None:
    json_path = tmp_path / "invalid.json"

    json_path.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    result = json_to_sqlite(
        json_path,
        tmp_path / "output",
    )

    assert result.success is False
    assert result.error


def test_json_without_words_returns_failure(
    tmp_path: Path,
) -> None:
    json_path = tmp_path / "invalid.json"

    json_path.write_text(
        json.dumps(
            {
                "something": {}
            }
        ),
        encoding="utf-8",
    )

    result = json_to_sqlite(
        json_path,
        tmp_path / "output",
    )

    assert result.success is False
    assert result.error


def test_existing_database_is_not_overwritten_by_default(
    tmp_path: Path,
) -> None:
    json_path = tmp_path / "frances.json"
    output = tmp_path / "output"

    create_json(
        json_path,
        {
            "bonjour": {
                "translation": "hola",
            },
        },
    )

    first = json_to_sqlite(
        json_path,
        output,
    )

    assert first.success

    second = json_to_sqlite(
        json_path,
        output,
    )

    assert second.success is False
    assert "existe" in (
        second.error or ""
    ).lower()


def test_progress_callback(
    tmp_path: Path,
) -> None:
    json_path = tmp_path / "frances.json"
    output = tmp_path / "output"

    create_json(
        json_path,
        {
            "bonjour": {
                "translation": "hola",
            },
            "chat": {
                "translation": "gato",
            },
            "chien": {
                "translation": "perro",
            },
        },
    )

    progress: list[tuple[int, int]] = []

    result = json_to_sqlite(
        json_path,
        output,
        progress_callback=(
            lambda current, total:
            progress.append(
                (current, total)
            )
        ),
    )

    assert result.success is True
    assert progress[-1] == (3, 3)