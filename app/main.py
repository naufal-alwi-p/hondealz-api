from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, Form, UploadFile, File
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from utility import upload_file_to_cloud_storage, get_cloud_storage_public_url, delete_file_on_cloud_storage, generate_random_name, extension_based_on_mime_type, CLOUD_BUCKET_PHOTO_PROFILE_DIRECTORY
from auth import encode_jwt, verify_password, generate_expire_time, hash_password, validate_jwt
from database import get_session
from model.model import AccessTokenPayload, UserData, UserDataWithoutPhoto
from model.database_model import User
from model.form_model import LoginForm, UpdateForm, RegisterForm, UpdatePasswordForm
from model.response_model import LoginSuccess, RegisterSuccess, UserDataSuccess, UpdatePhotoSuccess, UpdataDataSuccess, SuccessResponse, ErrorResponse, SelfValidationError

app = FastAPI(
    title="HonDealz API Documentation",
    description="Second-Hand Honda Motorcycle Price Prediction Application",
    version="1.2.0",
    docs_url=None,
    redoc_url="/documentation"
)

SessionDatabase = Annotated[Session, Depends(get_session)]

@app.post(
    '/user/login',
    response_model=LoginSuccess,
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Unauthorized"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal Server Error"
        }
    }
)
def login_user(form_data: Annotated[LoginForm, Form()], session: SessionDatabase):
    try:
        user = session.exec(select(User).where(User.email == form_data.email)).first()
    except:
        raise HTTPException(500, detail="Internal Server Error")
    
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(401, detail="Login Failed")
    
    expire_time = generate_expire_time()

    payload = AccessTokenPayload(id=user.id, expr=expire_time)

    return LoginSuccess(access_token=encode_jwt(payload), expire=expire_time)

@app.post(
    '/user/register',
    status_code=201,
    response_model=RegisterSuccess,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "User with the same data already registered"
        },
        415: {
            "model": ErrorResponse,
            "description": "File Not Supported"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal Server Error"
        }
    }
)
async def registering_user(
        form_data: Annotated[RegisterForm, Form(), File()],
        session: SessionDatabase
    ):
    random_filename = (generate_random_name(35) + extension_based_on_mime_type(form_data.photo_profile.content_type)) if form_data.photo_profile and form_data.photo_profile.size else None

    new_user = User(email=form_data.email, password=hash_password(form_data.password), username=form_data.username, name=form_data.name, photo_profile=random_filename)

    try:
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
    except IntegrityError:
        raise HTTPException(400, detail="User with the same data already registered")
    except:
        raise HTTPException(500, detail="Internal Server Error")
    
    if form_data.photo_profile and form_data.photo_profile.size:
        upload_file_to_cloud_storage(form_data.photo_profile, random_filename, CLOUD_BUCKET_PHOTO_PROFILE_DIRECTORY)
    
    expire_time = generate_expire_time()

    payload = AccessTokenPayload(id=new_user.id, expr=expire_time)

    data_user = UserData(
        email=new_user.email,
        username=new_user.username,
        name=new_user.name,
        photo_profile=get_cloud_storage_public_url(new_user.photo_profile, CLOUD_BUCKET_PHOTO_PROFILE_DIRECTORY) if random_filename else None
    )

    return RegisterSuccess(
        user=data_user,
        access_token=encode_jwt(payload),
        expire=expire_time
    )

@app.get(
    "/user",
    response_model=UserDataSuccess,
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Unauthorized"
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal Server Error"
        }
    }
)
def get_user_data(payload: Annotated[AccessTokenPayload, Depends(validate_jwt)], session: SessionDatabase):
    try:
        user = session.get(User, payload.id)
    except:
        raise HTTPException(500, detail="Internal Server Error")

    if not user:
        raise HTTPException(401, detail="User Unknown")

    data_user = UserData(
        email=user.email,
        username=user.username,
        name=user.name,
        photo_profile=get_cloud_storage_public_url(user.photo_profile, CLOUD_BUCKET_PHOTO_PROFILE_DIRECTORY) if user.photo_profile else None
    )

    return UserDataSuccess(user=data_user)

@app.patch(
    "/user/password",
    response_model=SuccessResponse,
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Unauthorized"
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal Server Error"
        }
    }
)
def update_user_password(payload: Annotated[AccessTokenPayload, Depends(validate_jwt)], form_data: Annotated[UpdatePasswordForm, Form()], session: SessionDatabase):
    try:
        user = session.get(User, payload.id)
    except:
        raise HTTPException(500, detail="Internal Server Error")

    if not user:
        raise HTTPException(401, detail="User Unknown")
    
    if not verify_password(form_data.old_password, user.password):
        raise HTTPException(403, detail="Change password failed")
    
    if form_data.new_password == form_data.old_password:
        raise HTTPException(422, detail=[SelfValidationError(loc=["body", "new_password"], msg="Password cannot be the same as the old password", input=form_data.new_password).model_dump()])

    if form_data.new_password == user.email:
        raise HTTPException(422, detail=[SelfValidationError(loc=["body", "new_password"], msg="Password cannot be the same as the email", input=form_data.new_password).model_dump()])
    
    user.password = hash_password(form_data.new_password)

    try:
        session.add(user)
        session.commit()
        session.refresh(user)
    except:
        raise HTTPException(500, detail="Internal Server Error")
    
    return SuccessResponse(message="Password updated")

@app.patch(
    "/user/photo-profile",
    response_model=UpdatePhotoSuccess,
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Unauthorized"
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden"
        },
        415: {
            "model": ErrorResponse,
            "description": "File Not Supported",
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal Server Error"
        }
    }
)
def update_user_photo_profile(payload: Annotated[AccessTokenPayload, Depends(validate_jwt)], photo_profile: Annotated[UploadFile, File()], session: SessionDatabase):
    try:
        user = session.get(User, payload.id)
    except:
        raise HTTPException(500, detail="Internal Server Error")

    if not user:
        raise HTTPException(401, detail="User Unknown")
    
    if not photo_profile.size:
        raise HTTPException(415, detail="No File Uploaded")
    
    random_filename = generate_random_name(35) + extension_based_on_mime_type(photo_profile.content_type)
    old_filename = user.photo_profile

    user.photo_profile = random_filename

    try:
        session.add(user)
        session.commit()
        session.refresh(user)
    except:
        raise HTTPException(500, detail="Internal Server Error")

    if user.photo_profile:
        delete_file_on_cloud_storage(old_filename, CLOUD_BUCKET_PHOTO_PROFILE_DIRECTORY)
    
    upload_file_to_cloud_storage(photo_profile, random_filename, CLOUD_BUCKET_PHOTO_PROFILE_DIRECTORY)

    return UpdatePhotoSuccess(photo_profile=get_cloud_storage_public_url(user.photo_profile, CLOUD_BUCKET_PHOTO_PROFILE_DIRECTORY))

@app.delete(
    "/user/photo-profile",
    response_model=SuccessResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Photo profile already null"
        },
        401: {
            "model": ErrorResponse,
            "description": "Unauthorized"
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal Server Error"
        }
    }
)
def delete_user_photo_profile(payload: Annotated[AccessTokenPayload, Depends(validate_jwt)], session: SessionDatabase):
    try:
        user = session.get(User, payload.id)
    except:
        raise HTTPException(500, detail="Internal Server Error")

    if not user:
        raise HTTPException(401, detail="User Unknown")
    
    if user.photo_profile == None:
        raise HTTPException(400, detail="Photo profile already null")
    
    old_filename = user.photo_profile
    user.photo_profile = None

    try:
        session.add(user)
        session.commit()
        session.refresh(user)
    except:
        raise HTTPException(500, detail="Internal Server Error")
    
    delete_file_on_cloud_storage(old_filename, CLOUD_BUCKET_PHOTO_PROFILE_DIRECTORY)

    return SuccessResponse(message="Photo Profile Successfully Deleted")

@app.put(
    "/user",
    response_model=UpdataDataSuccess,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Nothing to update"
        },
        401: {
            "model": ErrorResponse,
            "description": "Unauthorized"
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal Server Error"
        }
    }
)
def update_user_data(payload: Annotated[AccessTokenPayload, Depends(validate_jwt)], form_data: Annotated[UpdateForm, Form()], session: SessionDatabase):
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
    
    if form_data.username and form_data.username != user.username:
        user.username = form_data.username
        updated = True

    if form_data.name and form_data.name != user.name:
        user.name = form_data.name
        updated = True
    
    if updated:
        try:
            session.add(user)
            session.commit()
            session.refresh(user)
        except IntegrityError:
            raise HTTPException(400, detail="User with the same data already registered")
        except:
            raise HTTPException(500, detail="Internal Server Error")

        data_user = UserDataWithoutPhoto(email=user.email, username=user.username, name=user.name)

        return UpdataDataSuccess(user=data_user)
    else:
        raise HTTPException(400, detail="Nothing to update")

@app.delete(
    "/user",
    response_model=SuccessResponse,
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Unauthorized"
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal Server Error"
        }
    }
)
def delete_user_account(payload: Annotated[AccessTokenPayload, Depends(validate_jwt)], session: SessionDatabase):
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
    
    if user.photo_profile:
        delete_file_on_cloud_storage(user.photo_profile, CLOUD_BUCKET_PHOTO_PROFILE_DIRECTORY)

    return SuccessResponse(message=f"{user.username} account has been deleted")

# @app.post("/ai-models/motor-image-recognition")
# def motor_image_recognition():
#     return { "message": "API for Motocycle Image Recognition Model" }

# @app.post("/ai-models/motor-price-estimator")
# def motor_price_estimator():
#     return { "message": "API for Second-Hand Motor Price Estimator Model" }
