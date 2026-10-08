from __future__ import annotations

import random

from logic.quiz_logic import (
    get_adaptive_words,
    get_review_words,
)


def test_adaptive_words_handles_unseen_words() -> None:
    words = {
        "bonjour": {
            "correct": 0,
            "incorrect": 0,
            "interval": 0,
            "last_seen": None,
        }
    }

    result = get_adaptive_words(
        words,
        rng=random.Random(42),
    )

    assert len(result) == 1
    assert result[0][0] == "bonjour"


def test_adaptive_words_prioritize_errors() -> None:
    words = {
        "facile": {
            "correct": 10,
            "incorrect": 0,
            "interval": 10,
            "last_seen": "2026-10-01",
        },
        "difficile": {
            "correct": 2,
            "incorrect": 8,
            "interval": 1,
            "last_seen": "2026-10-07",
        },
    }

    result = get_adaptive_words(
        words,
        today=__import__("datetime").date(2026, 10, 8),
        rng=random.Random(42),
    )

    names = [
        word
        for word, _info in result
    ]

    assert "difficile" in names


def test_review_words_order_by_error_ratio() -> None:
    words = {
        "a": {
            "correct": 9,
            "incorrect": 1,
        },
        "b": {
            "correct": 1,
            "incorrect": 9,
        },
        "c": {
            "correct": 5,
            "incorrect": 5,
        },
    }

    result = get_review_words(
        words,
        2,
    )

    assert [
        word
        for word, _info in result
    ] == ["b", "c"]


def test_review_words_ignore_unanswered_words() -> None:
    words = {
        "new": {
            "correct": 0,
            "incorrect": 0,
        },
        "review": {
            "correct": 1,
            "incorrect": 1,
        },
    }

    result = get_review_words(
        words,
        10,
    )

    assert len(result) == 1
    assert result[0][0] == "review"