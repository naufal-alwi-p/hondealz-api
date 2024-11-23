FROM python:3.13.0

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

# Bcrypt Dependencies
RUN sudo apt install build-essential cargo

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["fastapi", "run", "app/main.py", "--port", "8080"]
