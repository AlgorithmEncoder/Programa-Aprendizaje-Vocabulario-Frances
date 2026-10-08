def get_level(interval):
    if interval <= 1:
        return "🔴 Nivel 1"
    elif interval <= 3:
        return "🟠 Nivel 2"
    elif interval <= 6:
        return "🟡 Nivel 3"
    elif interval <= 12:
        return "🟢 Nivel 4"
    else:
        return "🔵 Nivel 5"