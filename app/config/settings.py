import os
from datetime import timedelta


class Settings:
    # 환경변수에서 못 찾으면 기본값 사용
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:1234@localhost:3306/ssh?charset=utf8mb4",
    )

    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME_TO_SOMETHING_SECURE")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24시간


settings = Settings()
