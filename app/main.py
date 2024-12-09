import uuid

from typing import Annotated
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, Depends, HTTPException, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select, desc
from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError

from utility import upload_file_to_cloud_storage, download_file_from_google_cloud, get_cloud_storage_public_url, delete_file_on_cloud_storage, generate_random_name, extension_based_on_mime_type, generate_reset_password_email_content, generate_reset_password_form, generate_success_reset_password
from utility import CLOUD_BUCKET_PHOTO_PROFILE_DIRECTORY, CLOUD_BUCKET_MOTOR_IMAGE_DIRECTORY
from auth import encode_jwt, verify_password, generate_expire_time, hash_password, validate_jwt, generate_expire_datetime
from database import get_session
from model.model import AccessTokenPayload, UserData, UserDataWithoutPhoto
from model.database_model import User, Forgot_Password, Motor, Motor_Image
from model.form_model import LoginForm, UpdateForm, RegisterForm, UpdatePasswordForm, ResetPasswordForm, PricePredictForm
from model.response_model import LoginSuccess, RegisterSuccess, UserDataSuccess, UpdatePhotoSuccess, UpdataDataSuccess, SuccessResponse, ErrorResponse, SelfValidationError, PricePredictSuccess, ImagePredictSuccess
from email_handler import send_reset_password_email
from predict import predict_uploaded_image, predict_motor_price

app = FastAPI(
    title="HonDealz API Documentation",
    description="Second-Hand Honda Motorcycle Price Prediction Application",
    version="1.2.0",
    docs_url=None,
    redoc_url="/documentation"
)

app.mount("/assets", StaticFiles(directory="app/assets"), "assets")

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
    random_filename = (generate_random_name(33) + extension_based_on_mime_type(form_data.photo_profile.content_type)) if form_data.photo_profile and form_data.photo_profile.size else None

    new_user = User(email=form_data.email, password=hash_password(form_data.password), username=form_data.username, name=form_data.name, photo_profile=random_filename)

    try:
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
    except IntegrityError:
        raise HTTPException(400, detail="User with the same data already registered")
    # except:
    #     raise HTTPException(500, detail="Internal Server Error")
    
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

@app.post(
    "/user/forgot-password",
    response_model=SuccessResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Already requested it a while ago"
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal Server Error"
        }
    }
)
def forgot_password(email: Annotated[EmailStr, Form()], session: SessionDatabase, request: Request):
    try:
        user = session.exec(select(User).where(User.email == email)).first()
    except:
        raise HTTPException(500, detail="Internal Server Error")

    if not user:
        raise HTTPException(404, detail="Unknown Email")
    
    interval_10_minutes = datetime.now(timezone.utc) - timedelta(minutes=10)

    try:
        latest_fp_token = session.exec(select(Forgot_Password).where(Forgot_Password.user_id == user.id).where(Forgot_Password.expire > interval_10_minutes)).first()
    except:
        raise HTTPException(500, detail="Internal Server Error")
    
    if latest_fp_token:
        raise HTTPException(400, detail="Recently you have requested a password reset, if you want to request it again, please wait 10 minutes")
    
    fp_token = Forgot_Password(uuid=uuid.uuid4(), user=user, expire=generate_expire_datetime())

    try:
        session.add(fp_token)
        session.commit()
        session.refresh(fp_token)
    except:
        raise HTTPException(500, detail="Internal Server Error")
    
    url_origin = f"{request.url.scheme}://{request.url.hostname}"

    if not (request.url.port == 80 or request.url.port == 443 or request.url.port == None):
        url_origin = url_origin + f":{request.url.port}"

    try:
        send_reset_password_email(user.email, generate_reset_password_email_content(url_origin, fp_token.uuid))
        return SuccessResponse(message="Success, please check your email to reset your password")
    except:
        raise HTTPException(500, detail="Internal Server Error")

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
    
    random_filename = generate_random_name(33) + extension_based_on_mime_type(photo_profile.content_type)
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

@app.get("/reset-password", include_in_schema=False)
def get_method_reset_password():
    raise HTTPException(404)

@app.get("/reset-password/{uuid}", response_class=HTMLResponse, include_in_schema=False)
def reset_password_page(uuid: str, session: SessionDatabase):
    try:
        fp_token = session.get(Forgot_Password, uuid)
    except:
        raise HTTPException(500, detail="Internal Server Error")

    if not fp_token:
        raise HTTPException(404)
    
    interval_10_minutes = datetime.now(timezone.utc) - timedelta(minutes=10)

    try:
        latest_fp_token = session.exec(select(Forgot_Password).where(Forgot_Password.user_id == fp_token.user_id).where(Forgot_Password.expire > interval_10_minutes).order_by(desc(Forgot_Password.expire))).first()
    except:
        raise HTTPException(500, detail="Internal Server Error")
    
    if not latest_fp_token or latest_fp_token.uuid != fp_token.uuid:
        raise HTTPException(404)

    html_content = generate_reset_password_form(fp_token.uuid)

    return html_content

@app.post("/reset-password", response_class=HTMLResponse, include_in_schema=False)
def reset_password_handler(form_data: Annotated[ResetPasswordForm, Form()], session: SessionDatabase):
    try:
        fp_token = session.get(Forgot_Password, form_data.token)
        all_fp_token = session.exec(select(Forgot_Password).where(Forgot_Password.user_id == fp_token.user_id)).all()
    except:
        raise HTTPException(500, detail="Internal Server Error")

    if not fp_token:
        raise HTTPException(401, detail="Unauthorized")
    
    try:
        user = fp_token.user
    except:
        raise HTTPException(500, detail="Internal Server Error")
    
    if form_data.password == user.email:
        raise HTTPException(422, detail=[SelfValidationError(loc=["body", "password"], msg="Password cannot be the same as the email", input=form_data.password).model_dump()])
    
    user.password = hash_password(form_data.password)

    try:
        for token in all_fp_token:
            session.delete(token)
        session.add(user)
        session.commit()
        session.refresh(user)
    except:
        raise HTTPException(500, detail="Internal Server Error")
    
    return generate_success_reset_password()

@app.post(
    "/ai-models/motor-image-recognition",
    response_model=ImagePredictSuccess,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Prediction failed"
        },
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
async def motor_image_recognition(payload: Annotated[AccessTokenPayload, Depends(validate_jwt)], photo: Annotated[UploadFile, File()], session: SessionDatabase):
    try:
        user = session.get(User, payload.id)
    except:
        raise HTTPException(500, detail="Internal Server Error")

    if not user:
        raise HTTPException(401, detail="User Unknown")
    
    if not photo.size:
        raise HTTPException(415, detail="No File Uploaded")
    
    photo_bytes = await photo.read()

    predict_result = predict_uploaded_image(photo_bytes)

    if predict_result["status"] == "success":
        random_filename = generate_random_name(33) + extension_based_on_mime_type(photo.content_type)

        motor_image = Motor_Image(user=user, filename=random_filename, model_prediction=predict_result["model"])

        try:
            session.add(motor_image)
            session.commit()
            session.refresh(motor_image)
        except:
            raise HTTPException(500, detail="Internal Server Error")
        
        await photo.seek(0)
        upload_file_to_cloud_storage(photo, random_filename, CLOUD_BUCKET_MOTOR_IMAGE_DIRECTORY)

        return ImagePredictSuccess(id_picture=motor_image.id, model=motor_image.model_prediction)
    else:
        raise HTTPException(400, detail=predict_result["message"])


@app.post(
    "/ai-models/motor-price-estimator",
    response_model=PricePredictSuccess,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Prediction failed"
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
def motor_price_estimator(payload: Annotated[AccessTokenPayload, Depends(validate_jwt)], form_data: Annotated[PricePredictForm, Form()], session: SessionDatabase):
    try:
        user = session.get(User, payload.id)
        motor_image = None
        if form_data.id_picture != None:
            motor_image = session.get(Motor_Image, form_data.id_picture)
    except:
        raise HTTPException(500, detail="Internal Server Error")

    if not user:
        raise HTTPException(401, detail="User Unknown")
    
    predict_result = predict_motor_price(form_data)

    if predict_result["status"] == "success":
        motor = Motor(user=user, model=form_data.model, year=form_data.year, mileage=form_data.mileage, province=form_data.province, engine_size=form_data.engine_size, predicted_price=predict_result["predicted_price"], min_price=predict_result["price_range"]["lower"], max_price=predict_result["price_range"]["upper"])

        if motor_image:
            motor.motor_image = motor_image

        try:
            session.add(motor)
            session.commit()
            session.refresh(motor)
        except:
            raise HTTPException(500, detail="Internal Server Error")

        return PricePredictSuccess(min_price=motor.min_price, predicted_price=motor.predicted_price, max_price=motor.max_price)
    else:
        raise HTTPException(400, detail=predict_result["message"])
