import httpx
from app import schemas
import os
from dotenv import load_dotenv

load_dotenv()
URL = os.getenv("OL_URL")
http_client = httpx.AsyncClient(timeout=10.0)

#---Look for ISBN by title---
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
            raise schemas.LibreMarkException(message = "Open Library API is temporarily overloadeds", status_code = 503)
        
        if response.status_code != 200:
            raise schemas.LibreMarkException(message=f"External API error: {response.status_code}", status_code=502)

        data = response.json()
        docs = data.get("docs", [])

        if not docs:
            raise schemas.LibreMarkException(message="Book not found", status_code=404)

        # 3. Витягуємо ISBN
        # docs[0] — це найбільш релевантна книга
        isbn_list = docs[0].get("isbn", [])

        if not isbn_list:
            raise schemas.LibreMarkException(message="No ISBN associated with this title", status_code=404)


        # Повертаємо перший знайдений ISBN
        return isbn_list[0]
    
    except (httpx.ConnectError, httpx.ConnectTimeout):
        raise schemas.LibreMarkException(message="Could not connect to Open Library", status_code=503)
    except httpx.TimeoutException:
        raise schemas.LibreMarkException(message="Open Library response timed out", status_code=504)
    except Exception as e:
        raise schemas.LibreMarkException(message=f"Internal API error: {str(e)}", status_code=500)

#---Get info about book by ISBN---
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
            raise schemas.LibreMarkException(
                message=f"Open Library API returned error {response.status_code}", 
                status_code=502
            )

        data = response.json()
        book_key = f"ISBN:{isbn}"

        if book_key not in data:
            # Якщо даних про книгу немає в Books API, повертаємо базову інфу
            return {"isbn": isbn, "title": "Дані відсутні", "authors": ["N/A"], "synopsis": "Опис відсутній"}

        book_data = data[book_key]

        if book_key not in data:
            raise schemas.LibreMarkException(
                message=f"Detailed information for ISBN {isbn} not found", 
                status_code=404
            )
        
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
    except httpx.TimeoutException:
        raise schemas.LibreMarkException(message="Connection timed out while fetching book details", status_code=504)
    except httpx.RequestError:
        raise schemas.LibreMarkException(message="Network error occurred while contacting Open Library", status_code=503)
    except schemas.LibreMarkException:
        raise
    except Exception as e:
        raise schemas.LibreMarkException(message=f"Unexpected error: {str(e)}", status_code=500)