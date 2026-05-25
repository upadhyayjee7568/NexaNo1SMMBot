CATEGORY_MARKUP = {
    "instagram_followers": 20,
    "instagram_likes": 25,
    "youtube_views": 30,
    "telegram_members": 20,
}
DEFAULT_MARKUP = 25


def apply_markup(base_rate: float, category: str | None = None) -> float:
    markup = CATEGORY_MARKUP.get(category or "", DEFAULT_MARKUP)
    return round(base_rate * (1 + markup / 100), 4)
