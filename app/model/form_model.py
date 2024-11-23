from typing import Annotated

from pydantic import BaseModel, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber, PhoneNumberValidator

class LoginForm(BaseModel):
    email: EmailStr
    password: str

class UpdateForm(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    nama: str | None = None
    telepon: Annotated[PhoneNumber | None, PhoneNumberValidator(default_region="ID", number_format="NATIONAL")] = None
