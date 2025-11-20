import os
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi   # ⭐ 추가됨

from app.core.database import Base, engine
from app.api.v1 import auth, stores, recommendations, debug

app = FastAPI(title="소확행 API v1")

# 라우터 등록
app.include_router(auth.router, prefix="/api/v1")
app.include_router(stores.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(debug.router, prefix="/api/v1")


# OpenAPI 스키마 캐싱 (부팅 속도 개선)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="소확행 API v1",
        version="1.0.0",
        description="소확행 API 문서",
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
