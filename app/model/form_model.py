from typing import Annotated

from pydantic import BaseModel, EmailStr, Field
from pydantic_extra_types.phone_numbers import PhoneNumber, PhoneNumberValidator

class LoginForm(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

class UpdateForm(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=1)
    username: str | None = Field(default=None, min_length=1, max_length=30)
    name: str | None = Field(default=None, min_length=1)
    telephone: Annotated[PhoneNumber | None, PhoneNumberValidator(default_region="ID", number_format="NATIONAL")] = None
