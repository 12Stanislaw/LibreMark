from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    login: str = Field(
        ..., 
        min_length=3, 
        max_length=30, 
        pattern=r"^\S+$", # Регулярний вираз: заборона пробілів
        description="Унікальний нікнейм користувача"
    )
    
    # Автоматична перевірка формату email
    email: EmailStr
    password : str

class UserResponse(BaseModel):
    id_user: int
    login: str
    email: str

