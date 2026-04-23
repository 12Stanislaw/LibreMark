from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import dbEngine, Base, get_db
import models
import schemas
import utils.security as security


#---Перевіряємо унікальність логіну та емейлу користувача---
def check_unique_user(user : schemas.UserCreate,
                   db: Session):
    
    #Перевіряємо унікальний логін
    existing_user = db.query(models.User).filter(or_(models.User.login == user.login, models.User.email == user.email)).first()

    if existing_user:
        if existing_user.login == user.login:
            raise HTTPException(status_code=400, detail="This login is already registered")
        raise HTTPException(status_code=400, detail="This email is already registered")

#---Додаємо користувача в БД---
def register_user(user: schemas.UserCreate,
        db: Session):
    
    user_db = models.User(
        login = user.login,
        email = user.email,
        password = security.hash_pass(user.password)
    )
    db.add(user_db)
    db.commit()
    db.refresh(user_db)
    return user_db

#---Додаємо книгу користувачу---
def add_link(id_user: int,
             key: str,
             saving_state: str,
             db: Session):
    
    link = models.UserIsbn(
        id_user = id_user,
        isbn = key,
        saving_state = saving_state
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    return {"status": "success", "user": id_user, "book_added": key}

#---Автентифікуємо користувача---
def authenticate_user(form_data, 
                      db:Session):
    
    user_db = db.query(models.User).filter(models.User.login == form_data.username).first()

    if not user_db or not security.verify_pass(form_data.password, user_db.password):
        return False
    return user_db