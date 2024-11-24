from pydantic import BaseModel, HttpUrl

from model.model import UserData, UserDataWithoutPhoto

class SuccessResponse(BaseModel):
    message: str

class LoginSuccess(BaseModel):
    access_token: str

class UserDataSuccess(BaseModel):
    user: UserData

class RegisterSuccess(UserDataSuccess):
    access_token: str

class UpdatePhotoSuccess(BaseModel):
    photo_profile: HttpUrl

class UpdataDataSuccess(BaseModel):
    user: UserDataWithoutPhoto

