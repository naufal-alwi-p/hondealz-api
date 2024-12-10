# Dokumentasi

## Deskripsi
Repository ini merupakan source code server API HonDealz. Sebuah projek Capstone Bangkit Academy 2024 H2. Server API ini memiliki fitur authentication menggunakan JWT (JSON Web Token) dan terintegrasi dengan model Machine Learning yang dapat mengenal jenis motor Vario serta dapat memprediksi harga jual motor Vario bekas berdasarkan beberapa parameter.

## Cara Menjalankan Program

Berikut ini adalah cara menjalankan server API agar dapat digunakan. Sebelum itu ada beberapa syarat yang harus dipenuhi:

- MySQL >= 8.0
- Mengimport file `hondealz_database.sql` ke database
- Set beberapa environment variables:
    | **Env Variable**                          | **Default Value**  | **Requirement**                                    | **Description**                                                                                |
    |-------------------------------------------|--------------------|----------------------------------------------------|------------------------------------------------------------------------------------------------|
    | `APP_ENV`                                 | `dev`              | Optional                                           | Application Environment                                                                        |
    | `ACCESS_SECRET`                           | `abcde`            | Optional                                           | Secret for JWT                                                                                 |
    | `JWT_ALGORITHM`                           | `HS256`            | Optional                                           | Algorithm used for JWT                                                                         |
    | `ACCESS_TOKEN_EXPR_MINUTES`               | `30`               | Optional                                           | Bearer Expiration Time                                                                         |
    | `DB_HOST`                                 | `127.0.0.1`        | Optional                                           | Database Hostname                                                                              |
    | `DB_PORT`                                 | `3306`             | Optional                                           | Database Port                                                                                  |
    | `DB_USERNAME`                             | `root`             | Optional                                           | Database Username                                                                              |
    | `DB_PASSWORD`                             |                    | Optional                                           | Database Password                                                                              |
    | `DB_DATABASE`                             | `hondealz_app`     | Optional                                           | Database Name                                                                                  |
    | `DB_UNIX_SOCKET`                          |                    | Required when `APP_ENV=prod`                       | Please read Cloud SQL documentation                                                            |
    | `CLOUD_BUCKET`                            |                    | Required                                           | Cloud Storage Bucket to store user image                                                       |
    | `CLOUD_BUCKET_PHOTO_PROFILE_DIRECTORY`    |                    | Optional                                           | Folder to store photo profiles in the bucket                                                   |
    | `CLOUD_BUCKET_MOTOR_IMAGE_DIRECTORY`      |                    | Optional                                           | Folder to store motor images in the bucket                                                     |
    | `CLOUD_BUCKET_RESOURCE`                   |                    | Required                                           | Cloud Storage Bucket that stores Machine Learning Model                                        |
    | `IMAGE_MODEL_NAME`                        |                    | Required                                           | Machine Learning model to recognize motor types by image stored in CLOUD_BUCKET_RESOURCE       |
    | `PRICE_MODEL_NAME`                        |                    | Required                                           | Machine Learning model to predict second-hand motorcycle price stored in CLOUD_BUCKET_RESOURCE |
    | `BCRYPT_SALT_ROUND`                       | `12`               | Optional                                           | Bcrypt Salt Round for Hashing Password                                                         |
    | `SENDER_EMAIL`                            |                    | Required                                           | Email used by server to send forgot password form                                              |
    | `EMAIL_PASSWORD`                          |                    | Required                                           | Password for email used by server                                                              |
    | `RESET_PASSWORD_EXPR_MINUTES`             | `10`               | Optional                                           | Forgot Password form expire time                                                               |

### Menjalankan Program di Komputer Lokal
Setelah menyiapkan beberapa hal diatas. Aplikasi baru bisa digunakan. Berikut adalah langkah-langkah untuk menjalankan program di komputer.

1. **(Opsional)** Buat _virtual environment_ dengan perintah `python -m venv .venv`

2. **(Opsional)** Masuk ke _virtual environment_ dengan cara menjalankan perintah berikut sesuai dengan jenis shell yang digunakan
    - POSIX
        | Shell      | Command to activate virtual environment                |
        |------------|--------------------------------------------------------|
        | bash/zsh   | `$ source <venv>/bin/activate`                         |
        | fish       | `$ source <venv>/bin/activate.fish`                    |
        | csh/tcsh   | `$ source <venv>/bin/activate.csh`                     |
        | pwsh       | `$ <venv>/bin/Activate.ps1`                            |
    - Windows
        | Shell      | Command to activate virtual environment                |
        |------------|--------------------------------------------------------|
        | cmd.exe    | `C:\> <venv>\Scripts\activate.bat`                     |
        | PowerShell | `PS C:\> <venv>\Scripts\Activate.ps1`                  |

3. Install seluruh package yang diperlukan dengan`pip install -r requirements.txt`

4. Ketik perintah `fastapi dev` untuk menjalankan server dalam mode development atau gunakan `fastapi run` untuk menjalankan server dalam mode production.

5. Ketik shortcut `Ctrl` + `C` untuk menghentikan server jika selesai

6. **(Opsional)** Ketik perintah `deactivate` untuk keluar dari *virtual environment*

### Menjalankan Program di Docker

Program ini sudah memiliki file Dockerfile. Berikut adalah cara menjalankan program menggunakan container docker.

1. Buat docker image telebih dahulu dengan mengetik perintah `docker build -t "nama_image:tag" .`

2. Lalu jalankan container berdasarkan image yang sudah dibuat dengan mengetik perintah `docker run --name "nama_container" -p 8080:port_pilihan [--env KEY1=value1 --env KEY2=value2 ...] "nama_image:tag"`
