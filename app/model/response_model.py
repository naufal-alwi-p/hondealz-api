from pydantic import BaseModel, HttpUrl

from model.model import UserData, UserDataWithoutPhoto

class SuccessResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    detail: str

class LoginSuccess(BaseModel):
    access_token: str
    expire: int

class UserDataSuccess(BaseModel):
    user: UserData

class RegisterSuccess(UserDataSuccess):
    access_token: str
    expire: int

class UpdatePhotoSuccess(BaseModel):
    photo_profile: HttpUrl

class UpdataDataSuccess(BaseModel):
    user: UserDataWithoutPhoto

