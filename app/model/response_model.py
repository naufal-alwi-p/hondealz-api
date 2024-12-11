from typing import Literal, Any
from datetime import datetime

from pydantic import BaseModel, HttpUrl

from model.model import UserData, UserDataWithoutPhoto

class SuccessResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    detail: str

class SelfValidationError(BaseModel):
    type: Literal["value_error"] = "value_error"
    loc: list[str] = []
    msg: str = ""
    input: str = ""
    ctx: dict[str, Any] = {}

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

class ImagePredictSuccess(BaseModel):
    id_picture: int
    model: str
    created_at: datetime

class PricePredictSuccess(BaseModel):
    min_price: int
    predicted_price: int
    max_price: int

class PredictHistory(BaseModel):
    id: int
    image_url: HttpUrl | None = None
    model: Literal['All New Honda Vario 125 & 150', 'All New Honda Vario 125 & 150 Keyless', 'Vario 110', 'Vario 110 ESP', 'Vario 160', 'Vario Techno 110', 'Vario Techno 125 FI']
    year: int
    mileage: int
    location: str
    tax: Literal["hidup", "mati"]
    min_price: int
    predicted_price: int
    max_price: int
    created_at: datetime

class AllPredictHistory(BaseModel):
    histories: list[PredictHistory]