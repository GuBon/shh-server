from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config.settings import settings

# 연결 설정 최적화: pool_pre_ping 제거, 연결 수 제한
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=5,  # 연결 풀 크기 제한
    max_overflow=0,  # 추가 연결 생성 금지
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
