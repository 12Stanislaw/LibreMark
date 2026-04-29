from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Enum as SQLEnum
from app.database import Base
from app import schemas as schemas

class User(Base):
    __tablename__ = "users"

    id_user: Mapped[int] = mapped_column(primary_key=True, autoincrement = True)
    login: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self):
        return f"<User(login='{self.login}')>"
    
class UserIsbn(Base):
    __tablename__ = "user_isbn"

    id_link : Mapped[int] = mapped_column(primary_key=True, autoincrement = True)
    id_user: Mapped[int] = mapped_column(ForeignKey(User.id_user))
    isbn: Mapped[str] = mapped_column(String, nullable=False)
    saving_state : Mapped[schemas.SavingState] = mapped_column(SQLEnum(schemas.SavingState), nullable=False)

    def __repr__(self):
        return f"<UserIsbn(user_id={self.user_id}, isbn='{self.isbn}')>"