from contextlib import asynccontextmanager
import asyncio
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Depends, Query, HTTPException,Request
from sqlalchemy.orm import Session
from app.database import dbEngine, Base, get_db
from fastapi.security import OAuth2PasswordRequestForm
from app import models
from app import schemas
from app import jwt
import app.utils.services as services
import app.utils.security as security
import app.utils.olapi as olapi

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Дії при запуску (якщо потрібно)
    yield
    # Дії при вимкненні: закриваємо з'єднання
    await olapi.http_client.aclose()

app = FastAPI(lifespan=lifespan)
Base.metadata.create_all(bind=dbEngine)

#---Exception handler----
@app.exception_handler(schemas.LibreMarkException)
async def libremark_exception_handler(request: Request, exc: schemas.LibreMarkException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.message,
            "user": "Stanislaw-Admin" # Можна додати системну інфу для себе
        }
    )

#---Root---
@app.get("/")
async def root():
    return{"msg" : "ok"}

#---Add new user---
@app.post("/users/",
          response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate,
                db: Session = Depends(get_db)):
    services.check_unique_user(user, db)
    new_user = services.register_user(user, db)

    return new_user
#---Add new book---
@app.post("/users/books/")
async def save_book(current_user :models.User = Depends(jwt.get_current_user),
                    title: str = Query(..., min_length=1),
                    saving_state: str = Query(..., min_length=1),
                    db: Session = Depends(get_db)):
    
    key = await olapi.get_by_title(title)
    link = services.add_link(current_user.id_user, key, saving_state, db)
    return link

#---Login---
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

#---Видаляємо книгу з БД ---
@app.delete("/users/books")
async def delete_book(id_link: int,
                    current_user :models.User = Depends(jwt.get_current_user),
                    db: Session = Depends(get_db)):
    
    if id_link <= 0:
        raise HTTPException(status_code= 400,
                            detail= "ID must be grater than 0")
    book_db = db.query(models.UserIsbn).filter(models.UserIsbn.id_link == id_link, models.UserIsbn.id_user == current_user.id_user).first()

    db.delete(book_db)
    db.commit()
    
    remaining_books = db.query(models.UserIsbn).filter(
        models.UserIsbn.id_user == current_user.id_user
    ).order_by(models.UserIsbn.id_link).all()

    for index, book in enumerate(remaining_books, start=1):
        book.id_link = index
    
    db.commit()

    return {"msg" : "Deleted",
            "User" : current_user.login,
            }


@app.get("/user/books", response_model=list[schemas.BookResponse])
async def show_all_books(
    current_user: models.User = Depends(jwt.get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Отримуємо список ISBN із бази даних
    user_book_records = services.get_all_isbns(current_user.id_user, db)
    
    if not user_book_records:
        return []

    # 2. Формуємо список завдань для одночасного виконання
    # Проходимося по кожному запису і готуємо запит до API
    tasks = [olapi.get_book_by_isbn(record.isbn) for record in user_book_records]
    
    # 3. Чекаємо виконання всіх запитів одночасно (Concurrency)
    # Це працює набагато швидше, ніж цикл for з await
    books_data = await asyncio.gather(*tasks)

    return books_data