from fastapi import HTTPException, status
from argon2 import PasswordHasher

# Створюємо об'єкт хешера
ph = PasswordHasher()

def hash_pass(password: str) -> str:
    """Хешує пароль за допомогою Argon2id"""
    return ph.hash(password)

def verify_pass(plain_password : str, hashed_password : str) -> bool:
    
    return ph.verify(hashed_password, plain_password)