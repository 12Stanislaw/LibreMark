from fastapi import HTTPException, status
from argon2 import PasswordHasher

# Create hasher
ph = PasswordHasher()

#---Hash password---
def hash_pass(password: str) -> str:
    """Хешує пароль за допомогою Argon2id"""
    return ph.hash(password)
#---Verify hashed password---
def verify_pass(plain_password : str, hashed_password : str) -> bool:
    
    return ph.verify(hashed_password, plain_password)