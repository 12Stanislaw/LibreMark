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
                    saving_state: schemas.SavingState = Query(...),
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
        
        raise schemas.LibreMarkException(
            message="Invalid login or password", 
            status_code=401
        )
    
     # 4. Створюємо токен (передаємо ім'я в 'sub')
    access_token = jwt.create_access_token(data={"sub": user_db.login})

    # 5. Повертаємо токен
    return {
        "access_token": access_token, 
        "token_type": "bearer"}

#---Delete book from database ---
@app.delete("/users/books")
async def delete_book(id_link: int,
                    current_user :models.User = Depends(jwt.get_current_user),
                    db: Session = Depends(get_db)):
    
    if id_link <= 0:
        raise schemas.LibreMarkException(message="ID must be greater than 0", status_code=400)
    book_db = db.query(models.UserIsbn).filter(models.UserIsbn.id_link == id_link, models.UserIsbn.id_user == current_user.id_user).first()

    if not book_db:
        raise schemas.LibreMarkException(message="Not found link with this ID", status_code=404)
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

#---Show all saved books---
@app.get("/user/books", response_model=list[schemas.BookResponse])
async def show_all_books(skip: int = Query(0, ge=0),     
                        limit: int = Query(10, ge=1, le=50),
                        current_user: models.User = Depends(jwt.get_current_user),
                        db: Session = Depends(get_db)):
    
    user_book_records = services.get_all_isbns(current_user.id_user, db, skip = skip, limit = limit)
    
    if not user_book_records:
        return []

    # 2. Формуємо список завдань для одночасного виконання
    # Проходимося по кожному запису і готуємо запит до API
    tasks = [olapi.get_book_by_isbn(record.isbn) for record in user_book_records]
    
    # 3. Чекаємо виконання всіх запитів одночасно (Concurrency)
    # Це працює набагато швидше, ніж цикл for з await
    books_data = await asyncio.gather(*tasks)

    return books_data

#---Get all books by specific saving state
@app.get("/books/")
async def get_books_by_state(skip: int = Query(0, ge=0),
                             limit: int = Query(10, ge=1, le=50),
                             current_user :models.User = Depends(jwt.get_current_user),
                             saving_state: schemas.SavingState = Query(...),
                             db: Session = Depends(get_db)):
    isbns = services.get_isbns_by_state(current_user.id_user, saving_state, db, skip = skip, limit = limit)

    if not isbns:
        return []
    
    tasks = [olapi.get_book_by_isbn(record.isbn) for record in isbns]

    books_data = await asyncio.gather(*tasks)

    return books_data


