import os

SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ENCODE_ALGORITHM = os.getenv("ENCODE_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MIN: int = 30
REFRESH_TOKEN_EXPIRE_DAYS: int = 15