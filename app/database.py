import os

from sqlalchemy.engine.url import URL
from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy.util import EMPTY_DICT

import model.database_model

# Env
database_url = URL.create(
    drivername='mysql+pymysql',
    host=os.environ.get("DB_HOST", None) if os.environ.get("APP_ENV", None) == "prod" else '127.0.0.1', # Pilih salah satu
    port=os.environ.get("DB_PORT", 3306),
    username=os.environ.get("DB_USERNAME", "root"),
    password=os.environ.get("DB_PASSWORD", None),
    database=os.environ.get("DB_DATABASE", "hondealz_app"),
    query={"unix_socket": os.environ.get("DB_UNIX_SOCKET")} if os.environ.get("APP_ENV", None) == "prod" else EMPTY_DICT # Pilih salah satu
)

engine = create_engine(database_url, echo=True if __name__ == "__main__" else False)

def migration():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

if __name__ == "__main__":
    migration()
