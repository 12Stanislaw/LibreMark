from pydantic import BaseModel, EmailStr, Field, field_validator

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
    @field_validator('password')
    @classmethod
    def password_validation(cls, v: str) -> str:
        # Перевірка довжини
        if len(v) < 8:
            raise ValueError('Password must have at least 8 characters')
        
        # Перевірка на цифру
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        
        return v

class UserResponse(BaseModel):
    id_user: int
    login: str
    email: str


class BookResponse(BaseModel):
    title : str
    author : str
    first_publish_year: int
    language : str
    details : str
