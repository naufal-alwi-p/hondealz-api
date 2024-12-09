import re

from typing import Literal

from fastapi import UploadFile

from pydantic import BaseModel, EmailStr, Field, ValidationInfo, field_validator

PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$'
USERNAME_REGEX = r'^[a-zA-Z0-9_]+$'

class RegisterForm(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    confirm_password: str
    username: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1)
    photo_profile: UploadFile | None = Field(default=None)

    @field_validator('password')
    @classmethod
    def password_validation(cls, value: str, info: ValidationInfo):
        if 'email' in info.data:
            if value == info.data['email']:
                raise ValueError("Password cannot be the same as the email")

        if not re.match(PASSWORD_REGEX, value):
            raise ValueError("Password must have at least 1 uppercase letter, 1 lowercase letter, and 1 number")
        
        return value
    
    @field_validator('username')
    @classmethod
    def username_validation(cls, value: str):
        if not re.match(USERNAME_REGEX, value):
            raise ValueError("Username may only consist of letters, numbers and underscores without spaces")
        
        return value
    
    @field_validator('confirm_password')
    @classmethod
    def confirm_password_validation2(cls, value: str, info: ValidationInfo):
        if 'password' in info.data:
            if value != info.data['password']:
                raise ValueError("Password confirmation is not the same")

        return value

class LoginForm(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class UpdateForm(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=1, max_length=30)
    name: str | None = Field(default=None, min_length=1)
    
    @field_validator('username')
    @classmethod
    def username_validation(cls, value: str):
        if not re.match(USERNAME_REGEX, value):
            raise ValueError("Username may only consist of letters, numbers and underscores without spaces")
        
        return value

class UpdatePasswordForm(BaseModel):
    old_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)
    confirm_new_password: str

    @field_validator('old_password', 'new_password')
    @classmethod
    def password_validation(cls, value: str):
        if not re.match(PASSWORD_REGEX, value):
            raise ValueError("Password must have at least 1 uppercase letter, 1 lowercase letter, and 1 number")
        
        return value
    
    @field_validator('confirm_new_password')
    @classmethod
    def confirm_new_password_validation2(cls, value: str, info: ValidationInfo):
        if 'new_password' in info.data:
            if value != info.data['new_password']:
                raise ValueError("Password confirmation is not the same")

        return value

class ResetPasswordForm(BaseModel):
    token: str = Field(max_length=36)
    password: str = Field(min_length=8)
    confirm_password: str

    @field_validator('password')
    @classmethod
    def password_validation(cls, value: str):
        if not re.match(PASSWORD_REGEX, value):
            raise ValueError("Password must have at least 1 uppercase letter, 1 lowercase letter, and 1 number")
        
        return value
    
    @field_validator('confirm_password')
    @classmethod
    def confirm_password_validation2(cls, value: str, info: ValidationInfo):
        if 'password' in info.data:
            if value != info.data['password']:
                raise ValueError("Password confirmation is not the same")

        return value

class PricePredictForm(BaseModel):
    model: Literal['All New Honda Vario 125 & 150', 'All New Honda Vario 125 & 150 Keyless', 'Vario 110', 'Vario 110 ESP', 'Vario 160', 'Vario Techno 110', 'Vario Techno 125 FI']
    year: int
    mileage: int
    province: str
    engine_size: int
