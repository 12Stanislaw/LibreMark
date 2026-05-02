import pytest

# Тест: доступ до секретного шляху без токена
def test_get_books_without_token(client):
    response = client.get("/user/books")
    assert response.status_code == 401 # Має повернути 401 Unauthorized

# Тест: успішний доступ з валідним токеном
def test_get_books_with_valid_token(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/user/books", headers=headers)
    
    # Якщо все ок, має бути 200 або 404 (якщо список порожній), але не 401
    assert response.status_code in [200, 404]