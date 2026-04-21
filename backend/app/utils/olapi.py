from fastapi import HTTPException
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
URL = os.getenv("OL_URL")
http_client = httpx.AsyncClient(timeout=10.0)

#Отримуємо JSON книги за назвою
async def get_by_title(title: str):
    params = {"title" : title, "limit" : 1}
    try:
        response = await http_client.get(URL, params=params)
    
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Open Library API error")
        
        data = response.json()
        docs = data.get("docs", [])
        
        if not docs:
            raise HTTPException(status_code=404, detail="Book not found")

        first_book = docs[0]
        key = first_book.get("key")
        return key
    except httpx.RequestError as exc:
        # Обробка помилок мережі (наприклад, немає інтернету)
        raise HTTPException(status_code=503, detail=f"Could not connect to Open Library: {exc}")