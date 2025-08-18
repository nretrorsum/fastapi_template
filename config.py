import os

from dotenv import load_dotenv

load_dotenv()

# DB CONNECTION CREDENTIALS
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# LOGGING PARAMETER
LOG_LEVEL = os.environ.get("LOG_LEVEL")

# JWT SECRET KEY
SECRET_KEY = os.environ.get("SECRET_KEY")

# TOKENS_LIFETIME
ACCESS_TOKEN_LIVE = os.environ.get("ACCESS_TOKEN_LIVE")
REFRESH_TOKEN_LIVE = os.environ.get("REFRESH_TOKEN_LIVE")

#UPLOAD DIR
UPLOAD_DIR = os.environ.get("UPLOAD_DIR")
