from typing import Annotated

from pydantic import BaseModel, HttpUrl, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber, PhoneNumberValidator

from model.model import UserData, UserDataWithoutPhoto

class SuccessResponse(BaseModel):
    status: str = "success"

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str

class SuccessMessageResponse(SuccessResponse):
    message: str

class AccessToken(SuccessResponse):
    access_token: str

class UserDataSuccess(SuccessResponse):
    user: UserData

class RegisterSuccess(UserDataSuccess):
    access_token: str

class UpdatePhotoSuccess(SuccessResponse):
    photo_profile: HttpUrl

class UpdataDataSuccess(SuccessResponse):
    user: UserDataWithoutPhoto

