from utils.helpers import get_level


def test_get_level_1():
    assert get_level(1) == "🔴 Nivel 1"


def test_get_level_2():
    assert get_level(3) == "🟠 Nivel 2"


def test_get_level_3():
    assert get_level(6) == "🟡 Nivel 3"


def test_get_level_4():
    assert get_level(12) == "🟢 Nivel 4"


def test_get_level_5():
    assert get_level(13) == "🔵 Nivel 5"