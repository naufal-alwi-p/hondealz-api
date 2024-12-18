FROM python:3.12.8

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

# Bcrypt Dependencies
RUN apt-get update && apt-get install build-essential cargo -y

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["fastapi", "run", "app/main.py", "--port", "8080"]
