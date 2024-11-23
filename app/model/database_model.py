from typing import Annotated

from sqlmodel import Field, SQLModel
from pydantic import EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber, PhoneNumberValidator

class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True)
    password: str
    nama: str
    telepon: Annotated[PhoneNumber, PhoneNumberValidator(default_region="ID", number_format="NATIONAL")] = Field(unique=True)
    photo_profile: str

class Motor_Image(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    filename: str
    model: str

class Motor(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    motor_image_id: int = Field(foreign_key="motor_image.id")
    mileage: int
    location: str
    tax: bool
    mail: bool
    min_price: int
    max_price: int
