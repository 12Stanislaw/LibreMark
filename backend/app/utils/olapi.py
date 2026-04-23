from fastapi import HTTPException
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
URL = os.getenv("OL_URL")
http_client = httpx.AsyncClient(timeout=10.0)

#Отримуємо key книги за назвою
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
async def get_book_by_key(key : str):
    ...