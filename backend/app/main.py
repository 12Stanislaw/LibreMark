from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import dbEngine, Base, get_db
from fastapi.security import OAuth2PasswordRequestForm
import models
import schemas
import jwt
import utils.services as services
import utils.security as security
import utils.olapi as olapi

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Дії при запуску (якщо потрібно)
    yield
    # Дії при вимкненні: закриваємо з'єднання
    await olapi.http_client.aclose()

app = FastAPI(lifespan=lifespan)
Base.metadata.create_all(bind=dbEngine)

@app.get("/")
async def root():
    return{"msg" : "ok"}

@app.post("/users/",
          response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate,
                db: Session = Depends(get_db)):
    services.check_unique_user(user, db)
    new_user = services.register_user(user, db)

    return new_user

@app.post("/users/books/")
async def save_book(current_user :models.User = Depends(jwt.get_current_user),
                    title: str = Query(..., min_length=1),
                    saving_state: str = Query(..., min_length=1),
                    db: Session = Depends(get_db)):
    
    key = await olapi.get_by_title(title)
    link = services.add_link(current_user.id_user, key, saving_state, db)
    return link

@app.post("/users/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)):

    user_db = services.authenticate_user(form_data, db)
    #Перевірка користувача та пароля
    if not user_db or not security.verify_pass(form_data.password, user_db.password):
        
        raise HTTPException(
            status_code=401,
            detail="Невірне ім'я або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
     # 4. Створюємо токен (передаємо ім'я в 'sub')
    access_token = jwt.create_access_token(data={"sub": user_db.login})

    # 5. Повертаємо токен
    return {
        "access_token": access_token, 
        "token_type": "bearer"}

@app.delete("/users/books")
async def delete_book(current_user :models.User = Depends(jwt.get_current_user),
                    title: str = Query(..., min_length=1),
                    db: Session = Depends(get_db)):
    
    key = await olapi.get_by_title(title)

    book_db = db.query(models.UserIsbn).filter(models.UserIsbn.isbn == key, models.UserIsbn.id_user == current_user.id_user).first()

    db.delete(book_db)
    db.commit()

    return {"msg" : "Deleted",
            "User" : current_user.login,
            "Book_key" : key}

