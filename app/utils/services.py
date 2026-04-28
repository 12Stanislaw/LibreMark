from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import dbEngine, Base, get_db
import app.models as models
import app.schemas as schemas
import app.utils.security as security


#---Checking if login and email are unique---
def check_unique_user(user : schemas.UserCreate,
                   db: Session):
    
    #Check unique login
    existing_user = db.query(models.User).filter(or_(models.User.login == user.login, models.User.email == user.email)).first()

    if existing_user:
        if existing_user.login == user.login:
            raise schemas.LibreMarkException(message = "This login is already registered", status_code = 409)
        raise schemas.LibreMarkException(message = "This email is already registered", status_code = 409)

#---Adding user to database---
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

#---Adding link to database---
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

#---Authenticate user---
def authenticate_user(form_data, 
                      db:Session):
    
    user_db = db.query(models.User).filter(models.User.login == form_data.username).first()

    if not user_db:
        return False
    return user_db

def get_all_isbns(id_user: int, db: Session):
    # Повертає список об'єктів UserIsbn для конкретного юзера
    return db.query(models.UserIsbn).filter(models.UserIsbn.id_user == id_user).all()