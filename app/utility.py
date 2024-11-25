import random
import string
import os

from fastapi import UploadFile, HTTPException

from google.cloud import storage

CLOUD_BUCKET = os.environ["CLOUD_BUCKET"] # Wajib buat env variabel sendiri
CLOUD_BUCKET_PHOTO_PROFILE_DIRECTORY = os.environ.get("CLOUD_BUCKET_PHOTO_PROFILE_DIRECTORY", "")

IMAGE_MIME_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp"
}

def generate_random_name(length: int = 30) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def extension_based_on_mime_type(mime_type: str) -> str:
    if mime_type in IMAGE_MIME_TYPE:
        return IMAGE_MIME_TYPE[mime_type]
    else:
        raise HTTPException(422, detail="File must be jpg, jpeg, png, or webp")

def upload_file_to_cloud_storage(file: UploadFile, uploaded_filename: str, path: str):
    storage_client = storage.Client()
    bucket = storage_client.bucket(CLOUD_BUCKET)
    blob = bucket.blob(f"{path}{uploaded_filename}")

    blob.upload_from_file(file.file, content_type=file.content_type)

def get_cloud_storage_public_url(filename: str, path: str):
    public_url = f"https://storage.googleapis.com/{CLOUD_BUCKET}/{path}{filename}"

    return public_url

def delete_file_on_cloud_storage(filename: str, path: str):
    storage_client = storage.Client()
    bucket = storage_client.bucket(CLOUD_BUCKET)
    blob = bucket.blob(f"{path}{filename}")
    generation_match_precondition = None

    blob.reload()
    generation_match_precondition = blob.generation

    blob.delete(if_generation_match=generation_match_precondition)
