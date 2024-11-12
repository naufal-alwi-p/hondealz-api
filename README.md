# Cara Menjalankan Program

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
