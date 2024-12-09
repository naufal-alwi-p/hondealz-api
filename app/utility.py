import os
import secrets

from math import floor

from fastapi import UploadFile, HTTPException

from google.cloud import storage

CLOUD_BUCKET = os.environ["CLOUD_BUCKET"] # Wajib buat env variabel sendiri
CLOUD_BUCKET_PHOTO_PROFILE_DIRECTORY = os.environ.get("CLOUD_BUCKET_PHOTO_PROFILE_DIRECTORY", "")
CLOUD_BUCKET_MOTOR_IMAGE_DIRECTORY = os.environ.get("CLOUD_BUCKET_MOTOR_IMAGE_DIRECTORY", "")

CLOUD_BUCKET_RESOURCE = os.environ["CLOUD_BUCKET_RESOURCE"] # Wajib buat env variabel sendiri
IMAGE_MODEL_NAME = os.environ["IMAGE_MODEL_NAME"] # Wajib buat env variabel sendiri
PRICE_MODEL_NAME = os.environ["PRICE_MODEL_NAME"] # Wajib buat env variabel sendiri

CLOUD_BUCKET_RESOURCE = os.environ["CLOUD_BUCKET_RESOURCE"]

IMAGE_MIME_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp"
}

def generate_random_name(length: int = 30) -> str:
    length_bytes = floor(length * 3 / 4)
    return secrets.token_urlsafe(length_bytes)

def extension_based_on_mime_type(mime_type: str) -> str:
    if mime_type in IMAGE_MIME_TYPE:
        return IMAGE_MIME_TYPE[mime_type]
    else:
        raise HTTPException(415, detail="File must be jpg, jpeg, png, or webp")

def upload_file_to_cloud_storage(file: UploadFile, uploaded_filename: str, path: str, bucket: str = CLOUD_BUCKET):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket)
    blob = bucket.blob(f"{path}{uploaded_filename}")

    generation_match_precondition = 0

    blob.upload_from_file(file.file, content_type=file.content_type, if_generation_match=generation_match_precondition)

def download_file_from_google_cloud(destination_file: str, object_file: str, path: str, bucket: str):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket)

    blob = bucket.blob(f"{path}{object_file}")
    blob.download_to_filename(destination_file)

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

def generate_reset_password_email_content(server_origin: str, uuid: str):
    content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HonDealz Email</title>
        <link rel="shortcut icon" href="/assets/favicon.ico" type="image/x-icon">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 50px auto;
                background: #fff;
                padding: 20px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .header img {{
                max-width: 120px;
            }}
            .content {{
                margin-bottom: 20px;
            }}
            .content a {{
                color: #0073e6;
                text-decoration: none;
            }}
            .content a:hover {{
                text-decoration: underline;
            }}
            .highlight {{
                font-weight: bold;
            }}
            .footer {{
                font-size: 0.9em;
                color: #555;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://storage.googleapis.com/hondealz-bucket/assets/images/hondealz_logo.png" alt="HonDealz Logo">
            </div>
            <div class="content">
                <p>Hi,</p>
                <p>
                    To reset your HonDealz account password please <a href="{0}/reset-password/{1}">click here</a>. This email is only valid for <b>10 minutes</b>.
                </p>
                <p>
                    If you have previously requested to change your password, only the link contained in this e-mail is valid.
                </p>
            </div>
            <div class="footer">
                <p>Sincerely,</p>
                <p>Your HonDealz team</p>
            </div>
        </div>
    </body>
    </html>
    """.format(server_origin, uuid)

    return content

def generate_reset_password_form(uuid: str):
    content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Password</title>
        <link rel="shortcut icon" href="/assets/favicon.ico" type="image/x-icon">
        <style>
            body {{
                font-family: Arial, sans-serif;
                text-align: center;
                margin: 0;
                padding: 0;
            }}
            .container {{
                width: 100%;
                max-width: 400px;
                margin: 50px auto;
                padding: 50px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border-radius: 10px;
                background-color: #f9f9f9;
            }}
            img {{
                width: 100px;
                margin-bottom: 20px;
            }}
            h1 {{
                margin-bottom: 20px;
            }}
            .form-group {{
                text-align: left;
                margin-bottom: 15px;
            }}
            label {{
                display: block;
                margin-bottom: 5px;
                font-weight: lighter;
            }}
            .required {{
                color: red;
            }}
            input {{
                width: 100%;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }}
            button {{
                background-color: #ffc107;
                color: #000;
                border: none;
                padding: 10px;
                width: 100%;
                border-radius: 5px;
                cursor: pointer;
            }}
            button:hover {{
                background-color: #e6ac00;
            }}
            .error {{
                color: red;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <img src="https://storage.googleapis.com/hondealz-bucket/assets/images/hondealz_logo.png" alt="HonDealz Logo">
            <h1>Reset Password</h1>
            <form method="post" action="/reset-password" id="resetPasswordForm">
                <div class="form-group">
                    <label for="password">Password <span class="required">*</span></label>
                    <input type="password" id="password" name="password">
                    <div id="passwordError" class="error"></div>
                </div>
                <input type="hidden" name="token" value="{}">
                <div class="form-group">
                    <label for="confirmPassword">Confirm Password <span class="required">*</span></label>
                    <input type="password" id="confirmPassword" name="confirm_password">
                    <div id="confirmPasswordError" class="error"></div>
                </div>
                <button type="submit">Reset Password</button>
            </form>
        </div>

        <script>
            const form = document.getElementById("resetPasswordForm");
            const passwordInput = document.getElementById("password");
            const confirmPasswordInput = document.getElementById("confirmPassword");
            const passwordError = document.getElementById("passwordError");
            const confirmPasswordError = document.getElementById("confirmPasswordError");

            form.addEventListener("submit", (e) => {{
                // Reset error messages
                passwordError.textContent = "";
                confirmPasswordError.textContent = "";

                // Password validation
                const passwordValue = passwordInput.value;
                const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).{{8,}}$/;

                if (!passwordRegex.test(passwordValue)) {{
                    passwordError.textContent = "Password must be at least 8 characters, include 1 uppercase, 1 lowercase, and 1 number.";
                    return false;
                }}

                // Confirm password validation
                const confirmPasswordValue = confirmPasswordInput.value;
                if (confirmPasswordValue !== passwordValue) {{
                    confirmPasswordError.textContent = "Passwords does not match.";
                    return false;
                }}
            }});
        </script>
    </body>
    </html>
    """.format(uuid)

    return content

def generate_success_reset_password():
    content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset Successful</title>
        <link rel="shortcut icon" href="/assets/favicon.ico" type="image/x-icon">
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                margin: 0;
                padding: 0;
                background-color: #f9f9f9;
            }
            .container {
                width: 100%;
                max-width: 400px;
                margin: 100px auto;
                padding: 50px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border-radius: 10px;
                background-color: #ffffff;
            }
            img {
                width: 100px;
                margin-bottom: 20px;
            }
            h1 {
                margin-bottom: 10px;
                color: #28a745;
            }
            p {
                margin-bottom: 20px;
                font-size: 16px;
                color: #333;
            }
            a {
                display: inline-block;
                text-decoration: none;
                background-color: #ffc107;
                color: #000;
                padding: 10px 20px;
                border-radius: 5px;
            }
            a:hover {
                background-color: #e6ac00;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <img src="https://storage.googleapis.com/hondealz-bucket/assets/images/hondealz_logo.png" alt="HonDealz Logo">
            <h1>Password Reset Successful!</h1>
            <p>Your password has been successfully reset.</p>
        </div>
    </body>
    </html>
    """

    return content
