from pydantic import BaseModel, HttpUrl, EmailStr
from typing import Literal

class UserDataWithoutPhoto(BaseModel):
    email: EmailStr
    username: str
    name: str

class UserData(UserDataWithoutPhoto):
    photo_profile: HttpUrl | None

class AccessTokenPayload(BaseModel):
    id: int
    expr: int

class PricePredictInput(BaseModel):
    model: Literal['All New Honda Vario 125 & 150', 'All New Honda Vario 125 & 150 Keyless', 'Vario 110', 'Vario 110 ESP', 'Vario 160', 'Vario Techno 110', 'Vario Techno 125 FI']
    year: int
    mileage: int
    location: str
    tax: Literal["hidup", "mati"]
