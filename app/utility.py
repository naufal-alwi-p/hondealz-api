import mimetypes
import random
import string
import os

from fastapi import UploadFile

from google.cloud import storage

CLOUD_BUCKET = os.environ["CLOUD_BUCKET"] # Wajib buat env variabel sendiri
CLOUD_BUCKET_DIRECTORY = os.environ.get("CLOUD_BUCKET_DIRECTORY", "")

def generate_random_name(length: int = 30) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def extension_based_on_mime_type(mime_type: str) -> str:
    return [ext for ext in mimetypes.types_map if mimetypes.types_map[ext] == mime_type][0]

def upload_file_to_cloud_storage(file: UploadFile, uploaded_filename: str):
    storage_client = storage.Client()
    bucket = storage_client.bucket(CLOUD_BUCKET)
    blob = bucket.blob(f"{CLOUD_BUCKET_DIRECTORY}{uploaded_filename}")

    blob.upload_from_file(file.file, content_type=file.content_type)

def get_cloud_storage_public_url(filename: str):
    public_url = f"https://storage.googleapis.com/{CLOUD_BUCKET}/{CLOUD_BUCKET_DIRECTORY}{filename}"

    return public_url

def delete_file_on_cloud_storage(filename: str):
    storage_client = storage.Client()
    bucket = storage_client.bucket(CLOUD_BUCKET)
    blob = bucket.blob(f"{CLOUD_BUCKET_DIRECTORY}{filename}")
    generation_match_precondition = None

    blob.reload()
    generation_match_precondition = blob.generation

    blob.delete(if_generation_match=generation_match_precondition)
