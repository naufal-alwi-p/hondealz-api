from typing import Annotated

from sqlmodel import Field, SQLModel, Relationship
from pydantic import EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber, PhoneNumberValidator

class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True)
    password: str
    username: str = Field(unique=True, max_length=30)
    name: str
    telephone: Annotated[PhoneNumber, PhoneNumberValidator(default_region="ID", number_format="NATIONAL")] = Field(unique=True, max_length=16)
    photo_profile: str | None = Field(default=None, max_length=40, unique=True)

    motors: list["Motor"] = Relationship(back_populates="user", cascade_delete=True)

class Motor(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    motor_image_id: int | None = Field(default=None, foreign_key="motor_image.id", ondelete="SET NULL")
    model: str
    year: int
    mileage: int
    location: str
    tax: bool
    min_price: int
    max_price: int

    user: User = Relationship(back_populates="motors")
    motor_image: "Motor_Image" = Relationship(back_populates="motor")

class Motor_Image(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    filename: str = Field(max_length=40, unique=True)
    model_prediction: str

    motor: Motor = Relationship(back_populates="motor_image")
