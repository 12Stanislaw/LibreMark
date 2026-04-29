from cachetools import TTLCache

# Створюємо кеш:
# maxsize=100 — зберігаємо максимум 100 книг
# ttl=3600 — дані видаляються через 1 годину (3600 секунд)
book_details_cache = TTLCache(maxsize=100, ttl=3600)