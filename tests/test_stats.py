from logic.stats import (
    calculate_global_statistics,
    calculate_word_statistics,
    count_words_by_level,
    get_best_mastered_words,
    get_most_failed_words,
)


def sample_words() -> list[dict]:
    return [
        {
            "word": "bonjour",
            "correct": 9,
            "incorrect": 1,
            "interval": 10,
        },
        {
            "word": "chat",
            "correct": 2,
            "incorrect": 8,
            "interval": 1,
        },
        {
            "word": "chien",
            "correct": 5,
            "incorrect": 5,
            "interval": 4,
        },
    ]


def test_global_statistics() -> None:
    stats = calculate_global_statistics(
        sample_words()
    )

    assert stats.total_words == 3
    assert stats.total_correct == 16
    assert stats.total_incorrect == 14
    assert stats.total_attempts == 30

    assert stats.accuracy == (
        16 / 30 * 100
    )


def test_word_statistics() -> None:
    stats = calculate_word_statistics(
        sample_words()
    )

    assert len(stats) == 3

    bonjour = stats[0]

    assert bonjour.word == "bonjour"
    assert bonjour.correct == 9
    assert bonjour.incorrect == 1
    assert bonjour.accuracy == 90.0


def test_most_failed_words() -> None:
    result = get_most_failed_words(
        sample_words()
    )

    assert result[0].word == "chat"


def test_best_mastered_words() -> None:
    result = get_best_mastered_words(
        sample_words()
    )

    assert result[0].word == "bonjour"


def test_count_words_by_level() -> None:
    result = count_words_by_level(
        sample_words()
    )

    assert result == {
        "Nivel 1": 1,
        "Nivel 2": 0,
        "Nivel 3": 1,
        "Nivel 4": 1,
        "Nivel 5": 0,
    }