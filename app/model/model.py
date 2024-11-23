from typing import Annotated

from pydantic import BaseModel, HttpUrl, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber, PhoneNumberValidator

class UserDataWithoutPhoto(BaseModel):
    email: EmailStr
    nama: str
    telepon: Annotated[PhoneNumber, PhoneNumberValidator(default_region="ID", number_format="NATIONAL")]

class UserData(UserDataWithoutPhoto):
    photo_profile: HttpUrl

class JWTPayload(BaseModel):
    id: int
    expr: int
