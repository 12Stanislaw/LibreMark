import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models, jwt

# Використовуємо одну базу для всього
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    # Підміняємо залежність get_db на нашу тестову сесію
    def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db):
    user = models.User(login="testuser", password="hashedpassword", email = "test@test.com")
    db.add(user)
    db.commit()
    db.refresh(user) # Обов'язково оновити, щоб отримати ID
    return user

@pytest.fixture
def auth_token(test_user):
    # Якщо в моделі login, то sub має бути test_user.login
    return jwt.create_access_token({"sub": test_user.login})