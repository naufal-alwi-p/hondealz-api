from typing import Annotated
import random

from fastapi import FastAPI, Depends, HTTPException, Form, UploadFile, File
from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError, IntegrityError
from pydantic import EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber, PhoneNumberValidator

from utility import upload_file_to_cloud_storage, get_cloud_storage_public_url, delete_file_on_cloud_storage, generate_random_name, extension_based_on_mime_type
from auth import encode_jwt, verify_password, generate_expire_time, hash_password, validate_jwt
from database import get_session
from model.model import JWTPayload, UserData, UserDataWithoutPhoto
from model.database_model import User
from model.form_model import LoginForm, UpdateForm
from model.response_model import AccessToken, RegisterSuccess, UserDataSuccess, UpdatePhotoSuccess, UpdataDataSuccess, SuccessMessageResponse

app = FastAPI(
    title="HonDealz API Documentation",
    description="Second-Hand Honda Motorcycle Price Prediction Application",
    version="1.0.0"
)

SessionDatabase = Annotated[Session, Depends(get_session)]

@app.post('/user/login')
def login_user(form_data: Annotated[LoginForm, Form()], session: SessionDatabase) -> AccessToken:
    try:
        user = session.exec(select(User).where(User.email == form_data.email)).first()
    except:
        raise HTTPException(500, detail="Internal Server Error")
    
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(401, detail="Login Failed")
    
    payload = JWTPayload(id=user.id, expr=generate_expire_time())

    return AccessToken(access_token=encode_jwt(payload))

@app.post('/user/register', status_code=201)
async def registering_user(
        email: Annotated[EmailStr, Form()],
        password: Annotated[str, Form()],
        nama: Annotated[str, Form()],
        telepon: Annotated[PhoneNumber, Form(), PhoneNumberValidator(default_region="ID", number_format="NATIONAL")],
        photo_profile: Annotated[UploadFile, File()],
        session: SessionDatabase
    ) -> RegisterSuccess:
    random_filename = generate_random_name(35) + extension_based_on_mime_type(photo_profile.content_type)

    new_user = User(email=email, password=hash_password(password), nama=nama, telepon=telepon, photo_profile=random_filename)

    try:
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
    except IntegrityError:
        raise HTTPException(400, detail="User with the same data already registered")
    except:
        raise HTTPException(500, detail="Internal Server Error")
    
    upload_file_to_cloud_storage(photo_profile, random_filename)

    payload = JWTPayload(id=new_user.id, expr=generate_expire_time())

    data_user = UserData(
        email=new_user.email,
        nama=new_user.nama,
        telepon=new_user.telepon,
        photo_profile=get_cloud_storage_public_url(new_user.photo_profile)
    )

    return RegisterSuccess(
        user=data_user,
        access_token=encode_jwt(payload)
    )

@app.get("/user")
def get_user_data(payload: Annotated[JWTPayload, Depends(validate_jwt)], session: SessionDatabase) -> UserDataSuccess:
    try:
        user = session.get(User, payload.id)
    except:
        raise HTTPException(500, detail="Internal Server Error")

    if not user:
        raise HTTPException(401, detail="User Unknown")

    data_user = UserData(
        email=user.email,
        nama=user.nama,
        telepon=user.telepon,
        photo_profile=get_cloud_storage_public_url(user.photo_profile)
    )

    return UserDataSuccess(user=data_user)

@app.patch("/user/photo-profile")
def update_user_photo_profile(payload: Annotated[JWTPayload, Depends(validate_jwt)], photo_profile: Annotated[UploadFile, File()], session: SessionDatabase):
    try:
        user = session.get(User, payload.id)
    except:
        raise HTTPException(500, detail="Internal Server Error")

    if not user:
        raise HTTPException(401, detail="User Unknown")
    
    random_filename = generate_random_name(35) + extension_based_on_mime_type(photo_profile.content_type)
    old_filename = user.photo_profile

    user.photo_profile = random_filename

    try:
        session.add(user)
        session.commit()
        session.refresh(user)
    except:
        raise HTTPException(500, detail="Internal Server Error")

    delete_file_on_cloud_storage(old_filename)
    upload_file_to_cloud_storage(photo_profile, random_filename)

    return UpdatePhotoSuccess(photo_profile=get_cloud_storage_public_url(user.photo_profile))

@app.put("/user")
def update_user_data(payload: Annotated[JWTPayload, Depends(validate_jwt)], form_data: Annotated[UpdateForm, Form()], session: SessionDatabase):
    try:
        user = session.get(User, payload.id)
    except:
        raise HTTPException(500, detail="Internal Server Error")

    if not user:
        raise HTTPException(401, detail="User Unknown")
    
    updated = False

    if form_data.email and form_data.email != user.email:
        user.email = form_data.email
        updated = True

    if form_data.password:
        hashed_password = hash_password(form_data.password)
        if hashed_password != user.password:
            user.password = hashed_password
            updated = True

    if form_data.nama and form_data.nama != user.nama:
        user.nama = form_data.nama
        updated = True
    
    if form_data.telepon and form_data.telepon != user.telepon:
        user.telepon = form_data.telepon
        updated = True
    
    if updated:
        try:
            session.add(user)
            session.commit()
            session.refresh(user)
        except:
            raise HTTPException(500, detail="Internal Server Error")

        data_user = UserDataWithoutPhoto(email=user.email, nama=user.nama, telepon=user.telepon)

        return UpdataDataSuccess(user=data_user)
    else:
        raise HTTPException(400, detail="Nothing to update")

@app.delete("/user")
def delete_user_account(payload: Annotated[JWTPayload, Depends(validate_jwt)], session: SessionDatabase):
    try:
        user = session.get(User, payload.id)
    except:
        raise HTTPException(500, detail="Internal Server Error")

    if not user:
        raise HTTPException(401, detail="User Unknown")
    
    try:
        session.delete(user)
        session.commit()
    except:
        raise HTTPException(500, detail="Internal Server Error")

    delete_file_on_cloud_storage(user.photo_profile)

    return SuccessMessageResponse(message=f"{user.nama} account has been deleted")

@app.post("/ai-models/motor-image-recognition")
def motor_image_recognition():
    return { "message": "API for Motocycle Image Recognition Model" }

@app.post("/ai-models/motor-price-estimator")
def motor_price_estimator():
    return { "message": "API for Second-Hand Motor Price Estimator Model" }
