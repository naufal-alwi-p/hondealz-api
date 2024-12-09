from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from pydantic import EmailStr

class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True)
    password: str
    username: str = Field(unique=True, max_length=30)
    name: str
    photo_profile: str | None = Field(default=None, max_length=40, unique=True)

    motors: list["Motor"] = Relationship(back_populates="user", cascade_delete=True)
    motor_images: list["Motor_Image"] = Relationship(back_populates="user", cascade_delete=True)
    forgot_password: list["Forgot_Password"] = Relationship(back_populates="user", cascade_delete=True)

class Forgot_Password(SQLModel, table=True):
    uuid: str = Field(primary_key=True, max_length=36)
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    expire: datetime

    user: User = Relationship(back_populates="forgot_password")

class Motor(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    motor_image_id: int | None = Field(default=None, foreign_key="motor_image.id", ondelete="SET NULL")
    model: str
    year: int
    mileage: int
    province: str
    engine_size: int
    predicted_price: int
    min_price: int
    max_price: int

    user: User = Relationship(back_populates="motors")
    motor_image: "Motor_Image" = Relationship(back_populates="motor")

class Motor_Image(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    filename: str = Field(max_length=40, unique=True)
    model_prediction: str

    user: User = Relationship(back_populates="motor_images")
    motor: Motor = Relationship(back_populates="motor_image")
