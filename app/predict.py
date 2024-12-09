import os

from PIL import Image
import tensorflow as tf

from fastapi import UploadFile

from utility import download_file_from_google_cloud
from utility import CLOUD_BUCKET_RESOURCE, IMAGE_MODEL_NAME, PRICE_MODEL_NAME

from model.form_model import PricePredictForm
from ml import MotorImagePredictor, MotorPricePredictorWithRange

if not os.path.isfile("app/image_model.keras"):
    print("Start load image model")
    download_file_from_google_cloud("app/image_model.keras", IMAGE_MODEL_NAME, "image_recognition/", CLOUD_BUCKET_RESOURCE)
    print("Load image finished")

if not os.path.isfile("app/price_model.joblib"):
    print("Start load price model")
    download_file_from_google_cloud("app/price_model.joblib", PRICE_MODEL_NAME, "price_prediction/", CLOUD_BUCKET_RESOURCE)
    print("Load price model finished")

image_model = MotorImagePredictor(model_path="app/image_model.keras")

price_model = MotorPricePredictorWithRange(model_path="app/price_model.joblib")

def predict_uploaded_image(file: UploadFile):
    try:
        img = Image.open(file)

        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Get and display predictions using the correct method name
        predictions = image_model.predict_image(img)  # Changed from predict to predict_image

        return {
            "status": "success",
            "model": predictions[0][0]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error during prediction: {str(e)}"
        }

def predict_motor_price(data: PricePredictForm):
    result = price_model.predict_with_range(data.model_dump())

    return result
