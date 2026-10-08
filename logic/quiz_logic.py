from datetime import date
import random

def get_adaptive_words(words):

    today = date.today()
    candidates = []

    for word, info in words.items():

        correct = info["correct"]
        incorrect = info["incorrect"]
        total = correct + incorrect

        ratio_error = incorrect / total if total > 0 else 0

        last_seen = date.fromisoformat(info["last_seen"])
        days_since = (today - last_seen).days

        interval = max(1, info["interval"])
        due_factor = days_since / interval

        score = (
            (due_factor * 2)
            + (ratio_error * 1.5)
            + (1 / (total + 1))
        )

        candidates.append((word, info, score))

    if not candidates:
        return []

    candidates.sort(key=lambda x: x[2], reverse=True)

    # Top 40% para variabilidad
    top_slice = candidates[:max(5, int(len(candidates) * 0.4))]

    random.shuffle(top_slice)

    return [(w, info) for w, info, _ in top_slice]

def get_review_words(words, review_count):
    candidates = []

    for word, info in words:
        correct = info["correct"]
        incorrect = info["incorrect"]
        total = correct + incorrect

        if total > 0:
            ratio_error = incorrect / total
            candidates.append(
                (word, info, ratio_error)
            )

    if not candidates:
        return []

    # Ordenar por mayor ratio de error
    candidates.sort(key=lambda x: x[2], reverse=True)

    n = review_count.get()

    top_words = candidates[:n]

    return [(w, info) for w, info, _ in top_words]