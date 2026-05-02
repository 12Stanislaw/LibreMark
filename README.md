# LibreMark
## Overview
Backend application for managing read books.  
Users can search books via OpenLibrary API and save them to their personal collection.

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Docker
- JWT Authentication

## Features

- User registration & login (JWT)
- Search books via OpenLibrary API
- Save books to database
- View personal book list
- Sort books by status (read, dropped, etc.)

## Getting Started

### 1. Clone repo

```bash
git clone https://github.com/12Stanislaw/LibreMark.git
cd LibreMark
```

### 2. Run with Docker(Recommented)
```bash
docker-compose up --build
```
App will be available at:
```bash
http://localhost:8000
```

#### Without Docker(optional)
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API Documentation
Swagger available at:
```bash
http://localhost:8000/docs
```
### Environment variables
Create .env file
```
DB_USER=...
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432
DB_NAME=libremark

OL_URL=https://openlibrary.org/search.json

SECRET_KEY=...
ALGORITHM=HS256
```

## Demo Flow

1. Register user
2. Login
3. Search book
4. Save to collection
5. Update status (read/dropped)
   
## Future Improvements
- Refresh tokens for better auth security
- Redis caching for OpenLibrary responses
- Rate limiting to protect API
