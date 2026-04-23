from fastapi import HTTPException
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
URL = os.getenv("OL_URL")
http_client = httpx.AsyncClient(timeout=10.0)

#Отримуємо isbn книги за назвою
async def get_by_title(title: str):
    # 1. Формуємо URL та параметри
    # Використовуємо q= замість title= для ширшого пошуку, якщо назва неточна
    url = "https://openlibrary.org/search.json"
    params = {
        "q": title, 
        "limit": 1,
        "fields": "isbn,title,author_name" # Просимо тільки те, що треба
    }
    
    # 2. Обов'язкові заголовки (User-Agent)
    # Open Library часто кидає 503, якщо бачить "голий" httpx клієнт
    headers = {
        "User-Agent": "MyLibraryApp/1.0 (contact: your-email@example.com)"
    }

    try:
        response = await http_client.get(url, params=params, headers=headers)

        # Якщо отримали 503 або іншу помилку від сервера
        if response.status_code == 503:
            raise HTTPException(status_code=503, detail="Open Library перевантажена. Спробуйте через хвилину.")
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Open Library API помилка: {response.status_code}")

        data = response.json()
        docs = data.get("docs", [])

        if not docs:
            raise HTTPException(status_code=404, detail="Книгу не знайдено")

        # 3. Витягуємо ISBN
        # docs[0] — це найбільш релевантна книга
        isbn_list = docs[0].get("isbn", [])

        if not isbn_list:
            raise HTTPException(status_code=404, detail="Книгу знайдено, але в неї немає ISBN в базі")

        # Повертаємо перший знайдений ISBN
        return isbn_list[0]
    
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Не вдалося з'єднатися з сервером Open Library")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Сервер Open Library не відповів вчасно")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутрішня помилка: {str(e)}")

async def get_book_by_isbn(isbn: str):
    # Використовуємо Books API для отримання детальної інформації
    url = "https://openlibrary.org/api/books"
    params = {
        "bibkeys": f"ISBN:{isbn}",
        "format": "json",
        "jscmd": "data"
    }

    try:
        response = await http_client.get(url, params=params)
        
        if response.status_code != 200:
            return {"isbn": isbn, "title": "Помилка API", "authors": ["Невідомо"]}

        data = response.json()
        book_key = f"ISBN:{isbn}"

        if book_key not in data:
            # Якщо даних про книгу немає в Books API, повертаємо базову інфу
            return {"isbn": isbn, "title": "Дані відсутні", "authors": ["N/A"], "synopsis": "Опис відсутній"}

        book_data = data[book_key]

        return {
            "isbn": isbn,
            "title": book_data.get("title", "Без назви"),
            "authors": [a.get("name") for a in book_data.get("authors", [])],
            "publish_date": str(book_data.get("publish_date", "N/A")),
            "languages": [l.get("name") for l in book_data.get("languages", [])],
            "synopsis": book_data.get("notes") or "Опис недоступний",
            "cover": book_data.get("cover", {}).get("large"),
            "pages": book_data.get("number_of_pages")
        }
    except Exception:
        # У разі мережевої помилки повертаємо заглушку для конкретної книги
        return {"isbn": isbn, "title": "Помилка завантаження", "authors": []}   