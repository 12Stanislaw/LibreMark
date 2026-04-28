import os
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database import get_db # Імпортуй свою функцію отримання сесії
from app import models

# Завантажуємо змінні
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY") 
ALGORITHM = os.getenv("ALGORITHM") 

# Перевірка, чи зчиталися змінні (для дебагу)
if not SECRET_KEY or not ALGORITHM:
    raise RuntimeError("SECRET_KEY або ALGORITHM не знайдені в .env файлі")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

def create_access_token(data: dict, expires_delta: timedelta = None):    
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Стандарт: 15 хвилин, якщо нічого не передали
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    
    # Створюємо токен
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не вдалося перевірити облікові дані",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login: str = payload.get("sub")
        if login is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Шукаємо користувача в базі за ім'ям (або id)
    user = db.query(models.User).filter(models.User.login == login).first()
    
    # Якщо токен валідний, але юзера в базі вже немає (наприклад, видалили)
    if user is None:
        raise credentials_exception
        
    return user # ТЕПЕР ПОВЕРТАЄМО ЦІЛИЙ ОБ'ЄКТ