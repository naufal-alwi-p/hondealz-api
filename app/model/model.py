from pydantic import BaseModel, HttpUrl, EmailStr

class UserDataWithoutPhoto(BaseModel):
    email: EmailStr
    username: str
    name: str

class UserData(UserDataWithoutPhoto):
    photo_profile: HttpUrl | None

class AccessTokenPayload(BaseModel):
    id: int
    expr: int
