from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from database import dbEngine, Base, get_db
import models
import schemas
import utils.services as services
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
async def save_book(id_user: int,
                    title: str = Query(..., min_length=1),
                    saving_state: str = Query(..., min_length=1),
                    db: Session = Depends(get_db)):
    
    key = await olapi.get_by_title(title)
    link = services.add_link(id_user, key, saving_state, db)
    return link